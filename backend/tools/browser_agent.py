import logging
import asyncio
import os
import time
from playwright.async_api import async_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
from tools.registry import registry
from core.config import settings
import urllib.parse
import ipaddress
import socket

logger = logging.getLogger("AlchemistBrowserAgent")

def is_url_allowed(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False
            
        if hostname.lower() in ("localhost", "169.254.169.254", "127.0.0.1", "[::1]"):
            return False
            
        try:
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                return False
        except Exception:
            pass
            
        return True
    except Exception:
        return False

RETRY_ATTEMPTS = 3


async def _retry_playwright(coro_factory, operation: str):
    """Retry Playwright operations with exponential backoff."""
    last_error = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            return await coro_factory()
        except (PlaywrightTimeoutError, PlaywrightError) as e:
            last_error = e
            if attempt < RETRY_ATTEMPTS - 1:
                delay = 2 ** attempt
                logger.warning(
                    f"Playwright {operation} failed (attempt {attempt + 1}/{RETRY_ATTEMPTS}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"Playwright {operation} failed after {RETRY_ATTEMPTS} attempts: {e}")
    raise last_error


class BrowserSession:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserSession, cls).__new__(cls)
            cls._instance.playwright = None
            cls._instance.browser = None
            cls._instance.context = None
            cls._instance.page = None
        return cls._instance

    def _configure_context(self):
        if self.context:
            self.context.set_default_timeout(15000)
            self.context.set_default_navigation_timeout(30000)

    async def _ensure_browser(self):
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            if not self.browser or not self.browser.is_connected():
                self.browser = await self.playwright.chromium.launch(headless=False)
            if not self.context:
                self.context = await self.browser.new_context()
                self._configure_context()
            if not self.page or self.page.is_closed():
                self.page = await self.context.new_page()
        except Exception as e:
            logger.error(f"Failed to ensure browser state: {e}. Reinitializing Playwright.")
            await self._force_restart()

    async def _force_restart(self):
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
                logger.info("Force restart: page closed.")
        except Exception as e:
            logger.warning(f"Force restart: error closing page: {e}")
        try:
            if self.context:
                await self.context.close()
                logger.info("Force restart: context closed.")
        except Exception as e:
            logger.warning(f"Force restart: error closing context: {e}")
        try:
            if self.browser:
                await self.browser.close()
                logger.info("Force restart: browser closed.")
        except Exception as e:
            logger.warning(f"Force restart: error closing browser: {e}")
        try:
            if self.playwright:
                await self.playwright.stop()
                logger.info("Force restart: playwright stopped.")
        except Exception as e:
            logger.warning(f"Force restart: error stopping playwright: {e}")
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self._configure_context()
        self.page = await self.context.new_page()

    async def _navigate(self, url: str):
        await _retry_playwright(
            lambda: self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            ),
            "goto",
        )
        await self.page.wait_for_load_state("domcontentloaded", timeout=10000)

    async def _click_locator(self, locator):
        await locator.wait_for(state="visible", timeout=10000)
        await _retry_playwright(
            lambda: locator.click(timeout=15000),
            "click",
        )

    async def _fill_locator(self, locator, text: str):
        await _retry_playwright(
            lambda: locator.fill(text, timeout=15000),
            "fill",
        )

    async def start(self, url: str) -> str:
        try:
            await self._ensure_browser()

            if not url.startswith("http"):
                url = "http://" + url

            if not is_url_allowed(url):
                raise ValueError(f"URL {url} is blocked by SSRF protection.")

            logger.info(f"Playwright: {self.playwright}")
            logger.info(f"Browser: {self.browser}")
            logger.info(f"Context: {self.context}")
            logger.info(f"Page: {self.page}")

            if self.page is None:
                raise RuntimeError("Browser page was not initialized.")

            await self._navigate(url)
            return f"Successfully started browser and navigated to {url}. Title: {await self.page.title()}"
        except Exception as e:
            logger.error(f"Error starting browser: {e}")
            return f"Failed to start browser: {e}"

    async def _locate_element(self, selector: str):
        # We try three strategies in sequence:
        # 1. get_by_role (try common roles: button, link, textbox, checkbox, searchbox)
        # 2. get_by_text
        # 3. standard page.locator(selector)

        # Strategy 1: get_by_role
        if not any(char in selector for char in ['.', '#', '[', ']', '=', '>', '/']):
            for role in ["button", "link", "textbox", "checkbox", "searchbox"]:
                try:
                    locator = self.page.get_by_role(role, name=selector, exact=False)
                    if await locator.count() > 0:
                        logger.info(f"Located element by role='{role}' and name='{selector}'")
                        return locator.first
                except Exception:
                    pass

        # Strategy 2: get_by_text
        if not any(char in selector for char in ['.', '#', '[', ']', '=', '>', '/']):
            try:
                locator = self.page.get_by_text(selector, exact=False)
                if await locator.count() > 0:
                    logger.info(f"Located element by text='{selector}'")
                    return locator.first
            except Exception:
                pass

        # Strategy 3: fallback locator
        logger.info(f"Using fallback locator for selector='{selector}'")
        return self.page.locator(selector)

    async def _capture_failure_screenshot(self, action: str) -> str:
        try:
            filename = f"failure_{action}_{int(time.time())}.png"
            os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
            path = os.path.join(settings.SCREENSHOTS_DIR, filename)
            if self.page:
                await self.page.screenshot(path=path)
                logger.info(f"Captured failure screenshot at {path}")
                return path
        except Exception as e:
            logger.error(f"Failed to capture failure screenshot: {e}")
        return "None"

    async def _get_html_snippet(self) -> str:
        try:
            if self.page:
                content = await self.page.content()
                if len(content) > 4000:
                    return content[:2000] + "\n... [TRUNCATED] ...\n" + content[-2000:]
                return content
        except Exception as e:
            logger.error(f"Failed to get HTML snippet: {e}")
        return "None"

    async def click(self, selector: str) -> str:
        try:
            await self._ensure_browser()
            if not self.page:
                return "Error: Browser not started. Call browser_start first."

            locator = await self._locate_element(selector)
            await self._click_locator(locator)
            return f"Clicked element matching {selector}."
        except Exception as e:
            logger.error(f"Error clicking element '{selector}': {e}")
            screenshot_path = await self._capture_failure_screenshot("click")
            html_snippet = await self._get_html_snippet()
            logger.error(f"HTML snippet around failure: {html_snippet}")
            return f"Error clicking element '{selector}': {str(e)}. Screenshot saved at {screenshot_path}"

    async def type_text(self, selector: str, text: str) -> str:
        try:
            await self._ensure_browser()
            if not self.page:
                return "Error: Browser not started. Call browser_start first."

            locator = await self._locate_element(selector)
            await self._fill_locator(locator, text)
            return f"Typed '{text}' into {selector}."
        except Exception as e:
            logger.error(f"Error typing text into '{selector}': {e}")
            screenshot_path = await self._capture_failure_screenshot("type")
            html_snippet = await self._get_html_snippet()
            logger.error(f"HTML snippet around failure: {html_snippet}")
            return f"Error typing text: {str(e)}. Screenshot saved at {screenshot_path}"

    async def get_html(self) -> str:
        try:
            await self._ensure_browser()
            if not self.page:
                return "Browser not started."
            return await self.page.content()
        except PlaywrightError as e:
            logger.error(f"Playwright error getting HTML: {e}")
            await self._force_restart()
            return "Browser crashed. Playwright restarted."
        except Exception as e:
            logger.error(f"Error getting HTML: {e}")
            return f"Error: {str(e)}"

    async def read_page_title(self) -> str:
        try:
            await self._ensure_browser()
            if not self.page:
                return "Error: Browser not started."
            return f"Page title is: {await self.page.title()}"
        except Exception as e:
            logger.error(f"Error reading title: {e}")
            return f"Failed to read title: {e}"

    async def extract_page_text(self) -> str:
        try:
            await self._ensure_browser()
            if not self.page:
                return "Error: Browser not started."
            text = await self.page.evaluate("document.body.innerText")
            return text[:4000] if text else "No text found."
        except PlaywrightError as e:
            logger.error(f"Playwright error extracting text: {e}")
            await self._force_restart()
            return f"Browser crashed. Playwright restarted. {e}"
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return f"Error extracting text: {str(e)}"

    async def search_google(self, query: str) -> str:
        try:
            await self.start("https://www.google.com")
            locator = self.page.locator('textarea[name="q"]')
            await self._fill_locator(locator, query)
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            return f"Searched Google for '{query}'. Top results page title: {await self.page.title()}"
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            return f"Failed to search Google: {e}"

    async def open_linkedin(self) -> str:
        return await self.start("https://www.linkedin.com")

    async def open_github(self) -> str:
        return await self.start("https://github.com")

    async def open_chatgpt(self) -> str:
        return await self.start("https://chat.openai.com")

    async def navigate_page(self, url: str) -> str:
        return await self.start(url)

    async def navigate_back(self) -> str:
        try:
            await self._ensure_browser()
            if not self.page:
                return "Error: Browser not started."
            await self.page.go_back()
            return "Navigated back."
        except PlaywrightError as e:
            logger.error(f"Playwright error navigating back: {e}")
            return f"Playwright error: {e}"
        except Exception as e:
            logger.error(f"Error navigating back: {e}")
            return f"Error navigating back: {str(e)}"

    async def submit_form(self, selector: str) -> str:
        try:
            await self._ensure_browser()
            if not self.page:
                return "Error: Browser not started."
            locator = self.page.locator(selector)
            await self._click_locator(locator)
            await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            return f"Successfully submitted form via {selector}."
        except Exception as e:
            logger.error(f"Error submitting form {selector}: {e}")
            return f"Failed to submit form: {e}"

    async def close(self) -> str:
        try:
            if self.page:
                try:
                    await self.page.close()
                    logger.info("Browser page closed.")
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")
                finally:
                    self.page = None
            if self.context:
                try:
                    await self.context.close()
                    logger.info("Browser context closed.")
                except Exception as e:
                    logger.warning(f"Error closing context: {e}")
                finally:
                    self.context = None
            if self.browser:
                try:
                    await self.browser.close()
                    logger.info("Browser closed.")
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
                finally:
                    self.browser = None
            if self.playwright:
                try:
                    await self.playwright.stop()
                    logger.info("Playwright stopped.")
                except Exception as e:
                    logger.warning(f"Error stopping playwright: {e}")
                finally:
                    self.playwright = None
            return "Successfully closed browser."
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            return f"Failed to close browser: {e}"

session = BrowserSession()

async def browser_start(url: str) -> str:
    return await session.start(url)

async def open_url(url: str) -> str:
    return await session.start(url)

async def browser_click(selector: str) -> str:
    return await session.click(selector)

async def click_element(selector: str) -> str:
    return await session.click(selector)

async def browser_type(selector: str, text: str) -> str:
    return await session.type_text(selector, text)

async def type_into_field(selector: str, text: str) -> str:
    return await session.type_text(selector, text)

async def browser_get_html() -> str:
    return await session.get_html()

async def browser_close() -> str:
    return await session.close()

async def read_page_title() -> str:
    return await session.read_page_title()

async def extract_page_text() -> str:
    return await session.extract_page_text()

async def navigate_page(url: str) -> str:
    return await session.navigate_page(url)

async def navigate_back() -> str:
    return await session.navigate_back()

async def submit_form(selector: str) -> str:
    return await session.submit_form(selector)

async def search_google(query: str) -> str:
    return await session.search_google(query)

async def open_linkedin() -> str:
    return await session.open_linkedin()

async def open_github() -> str:
    return await session.open_github()

async def open_chatgpt() -> str:
    return await session.open_chatgpt()

# Register Tools
registry.register("browser_start", browser_start)
registry.register("open_url", open_url)
registry.register("open_website", open_url)
registry.register("browser_click", browser_click)
registry.register("click_element", click_element)
registry.register("browser_type", browser_type)
registry.register("type_into_field", type_into_field)
registry.register("browser_get_html", browser_get_html)
registry.register("browser_close", browser_close)
registry.register("read_page_title", read_page_title)
registry.register("extract_page_text", extract_page_text)
registry.register("navigate_page", navigate_page)
registry.register("navigate_back", navigate_back)
registry.register("submit_form", submit_form)
registry.register("search_google", search_google)
registry.register("open_linkedin", open_linkedin)
registry.register("open_github", open_github)
registry.register("open_chatgpt", open_chatgpt)

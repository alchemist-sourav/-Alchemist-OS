import logging
from playwright.sync_api import sync_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
from tools.registry import registry

logger = logging.getLogger("AlchemistBrowserAgent")

class BrowserSession:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserSession, cls).__new__(cls)
            cls._instance.playwright = None
            cls._instance.browser = None
            cls._instance.page = None
        return cls._instance

    def _ensure_browser(self):
        try:
            if not self.playwright:
                self.playwright = sync_playwright().start()
            if not self.browser or not self.browser.is_connected():
                self.browser = self.playwright.chromium.launch(headless=False)
            if not self.page or self.page.is_closed():
                self.page = self.browser.new_page()
        except Exception as e:
            logger.error(f"Failed to ensure browser state: {e}. Reinitializing Playwright.")
            self._force_restart()

    def _force_restart(self):
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        self.playwright = None
        self.browser = None
        self.page = None
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()

    def start(self, url: str) -> str:
        try:
            self._ensure_browser()
            
            if not url.startswith("http"):
                url = "http://" + url
                
            self.page.goto(url)
            self.page.wait_for_load_state("networkidle")
            return f"Successfully started browser and navigated to {url}. Title: {self.page.title()}"
        except Exception as e:
            logger.error(f"Error starting browser: {e}")
            return f"Failed to start browser: {e}"

    def click(self, selector: str) -> str:
        try:
            self._ensure_browser()
            if not self.page:
                return "Error: Browser not started. Call browser_start first."
            self.page.click(selector, timeout=5000)
            return f"Clicked element matching {selector}."
        except PlaywrightError as e:
            logger.error(f"Playwright error clicking: {e}")
            return f"Playwright error: could not click {selector}. {e}"
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return f"Error clicking element: {str(e)}"

    def type_text(self, selector: str, text: str) -> str:
        try:
            self._ensure_browser()
            if not self.page:
                return "Error: Browser not started. Call browser_start first."
            self.page.fill(selector, text, timeout=5000)
            return f"Typed '{text}' into {selector}."
        except PlaywrightError as e:
            logger.error(f"Playwright error typing: {e}")
            return f"Playwright error: could not type into {selector}. {e}"
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return f"Error typing text: {str(e)}"

    def get_html(self) -> str:
        try:
            self._ensure_browser()
            if not self.page:
                return "Browser not started."
            return self.page.content()
        except PlaywrightError as e:
            logger.error(f"Playwright error getting HTML: {e}")
            self._force_restart()
            return "Browser crashed. Playwright restarted."
        except Exception as e:
            logger.error(f"Error getting HTML: {e}")
            return f"Error: {str(e)}"

    def read_page_title(self) -> str:
        try:
            self._ensure_browser()
            if not self.page:
                return "Error: Browser not started."
            return f"Page title is: {self.page.title()}"
        except Exception as e:
            logger.error(f"Error reading title: {e}")
            return f"Failed to read title: {e}"

    def extract_page_text(self) -> str:
        try:
            self._ensure_browser()
            if not self.page:
                return "Error: Browser not started."
            text = self.page.evaluate("document.body.innerText")
            return text[:4000] if text else "No text found."
        except PlaywrightError as e:
            logger.error(f"Playwright error extracting text: {e}")
            self._force_restart()
            return f"Browser crashed. Playwright restarted. {e}"
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return f"Error extracting text: {str(e)}"

    def search_google(self, query: str) -> str:
        try:
            self.start("https://www.google.com")
            self.page.fill('textarea[name="q"]', query)
            self.page.keyboard.press("Enter")
            self.page.wait_for_load_state("networkidle")
            return f"Searched Google for '{query}'. Top results page title: {self.page.title()}"
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            return f"Failed to search Google: {e}"

    def open_linkedin(self) -> str:
        return self.start("https://www.linkedin.com")

    def open_github(self) -> str:
        return self.start("https://github.com")

    def open_chatgpt(self) -> str:
        return self.start("https://chat.openai.com")

    def navigate_page(self, url: str) -> str:
        return self.start(url)

    def navigate_back(self) -> str:
        try:
            self._ensure_browser()
            if not self.page:
                return "Error: Browser not started."
            self.page.go_back()
            return "Navigated back."
        except PlaywrightError as e:
            logger.error(f"Playwright error navigating back: {e}")
            return f"Playwright error: {e}"
        except Exception as e:
            logger.error(f"Error navigating back: {e}")
            return f"Error navigating back: {str(e)}"

    def submit_form(self, selector: str) -> str:
        try:
            if not self.page:
                return "Error: Browser not started."
            self.page.click(selector)
            self.page.wait_for_load_state("networkidle")
            return f"Successfully submitted form via {selector}."
        except Exception as e:
            logger.error(f"Error submitting form {selector}: {e}")
            return f"Failed to submit form: {e}"

    def close(self) -> str:
        try:
            if self.page:
                self.page.close()
                self.page = None
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            return "Successfully closed browser."
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            return f"Failed to close browser: {e}"

session = BrowserSession()

def browser_start(url: str) -> str:
    return session.start(url)

def open_url(url: str) -> str:
    return session.start(url)

def browser_click(selector: str) -> str:
    return session.click(selector)

def click_element(selector: str) -> str:
    return session.click(selector)

def browser_type(selector: str, text: str) -> str:
    return session.type_text(selector, text)

def type_into_field(selector: str, text: str) -> str:
    return session.type_text(selector, text)

def browser_get_html() -> str:
    return session.get_html()

def browser_close() -> str:
    return session.close()

def read_page_title() -> str:
    return session.read_page_title()

def extract_page_text() -> str:
    return session.extract_page_text()

def navigate_page(url: str) -> str:
    return session.navigate_page(url)

def navigate_back() -> str:
    return session.navigate_back()

def submit_form(selector: str) -> str:
    return session.submit_form(selector)

def search_google(query: str) -> str:
    return session.search_google(query)

def open_linkedin() -> str:
    return session.open_linkedin()

def open_github() -> str:
    return session.open_github()

def open_chatgpt() -> str:
    return session.open_chatgpt()

# Register Tools
registry.register("browser_start", browser_start)
registry.register("open_url", open_url)
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

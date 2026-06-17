import asyncio
from tools.browser_agent import session, browser_start, browser_navigate, browser_close

async def test_browser():
    try:
        print("Starting browser...")
        res = await browser_start()
        print("browser_start:", res)
        
        print("Navigating...")
        res = await browser_navigate("https://example.com")
        print("browser_navigate:", res)
        
        print("Closing...")
        res = await browser_close()
        print("browser_close:", res)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_browser())

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: print(f"[Browser Console {msg.type}] {msg.text}"))
        
        print("Navigating to http://localhost:5173...")
        await page.goto("http://localhost:5173", wait_until="networkidle")
        await asyncio.sleep(1)
        
        # Click Enter as Technician
        btn = page.locator("button:has-text('Enter as Technician')")
        if await btn.is_visible():
            print("Clicking Enter as Technician...")
            await btn.click()
            await asyncio.sleep(2)
        
        print("Current URL:", page.url)
        await page.screenshot(path="C:/Users/srivish/.gemini/antigravity/brain/65102128-f43c-470f-8dfd-0262e2720085/dashboard_logged_in.png", full_page=True)
        print("Saved screenshot to dashboard_logged_in.png")
        
        if errors:
            print("Page Unhandled Errors:", errors)
        else:
            print("No page JS errors detected!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

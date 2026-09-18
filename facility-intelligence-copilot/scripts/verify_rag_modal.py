import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("http://localhost:5173", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        btn = page.locator("button:has-text('Enter as Technician')")
        if await btn.is_visible():
            await btn.click()
            await asyncio.sleep(2)

        # Click the circular brain icon in header
        memory_icon = page.locator("header button[title='Open Facility Memory Modal']").first
        if await memory_icon.is_visible():
            print("Clicking circular Facility Memory icon in header...")
            await memory_icon.click()
            await asyncio.sleep(2)

        await page.screenshot(path="C:/Users/srivish/.gemini/antigravity/brain/65102128-f43c-470f-8dfd-0262e2720085/facility_memory_modal_open.png")
        print("Saved screenshot to facility_memory_modal_open.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

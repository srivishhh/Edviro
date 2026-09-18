import asyncio
from playwright.async_api import async_playwright

SNS_URL = "https://agents.snsihub.ai/dashboard"
EMAIL = "srivishnu.s.cse.2024@snsct.org"
PASSWORD = "#Brucevish23"

async def main():
    print("--- CREATING & PUBLISHING WORKFLOW 'GSENSE 3.0' ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(SNS_URL, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        email_input = page.locator("input[type='email']")
        if await email_input.is_visible():
            await email_input.fill(EMAIL)
            await page.locator("input[type='password']").fill(PASSWORD)
            await page.locator("button[type='submit']").click()
            await asyncio.sleep(3)

        # Click Agent Builder
        builder_btn = page.locator("button:has-text('Agent Builder')").first
        if await builder_btn.is_visible():
            await builder_btn.click()
            await asyncio.sleep(3)

        # Click title 'Agent Builder' to rename to 'GSENSE 3.0'
        title_el = page.locator("text='Agent Builder'").first
        if await title_el.is_visible():
            await title_el.click()
            await asyncio.sleep(1)
            # Type GSENSE 3.0
            await page.keyboard.type("GSENSE 3.0")
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)

        # Click Save button
        save_btn = page.locator("button:has-text('Save')").first
        if await save_btn.is_visible():
            print("Clicking Save...")
            await save_btn.click()
            await asyncio.sleep(2)

        # Click Deploy button
        deploy_btn = page.locator("button:has-text('Deploy')").first
        if await deploy_btn.is_visible():
            print("Clicking Deploy...")
            await deploy_btn.click()
            await asyncio.sleep(3)

        await page.screenshot(path="C:/Users/srivish/.gemini/antigravity/brain/65102128-f43c-470f-8dfd-0262e2720085/sns_gsense30_deployed.png")
        print("Captured screenshot sns_gsense30_deployed.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

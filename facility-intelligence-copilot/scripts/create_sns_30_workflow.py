import asyncio
import json
from playwright.async_api import async_playwright

SNS_URL = "https://agents.snsihub.ai/dashboard"
EMAIL = "srivishnu.s.cse.2024@snsct.org"
PASSWORD = "#Brucevish23"

async def main():
    print("--- CREATING NEW WORKFLOW 'GSENSE 3.0' IN LIVE SNS WORKBENCH ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        api_headers = {}

        async def handle_request(route, request):
            nonlocal api_headers
            if "api" in request.url:
                for k, v in request.headers.items():
                    api_headers[k] = v
            await route.continue_()

        await context.route("**/*", handle_request)

        await page.goto(SNS_URL, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        email_input = page.locator("input[type='email']")
        if await email_input.is_visible():
            await email_input.fill(EMAIL)
            await page.locator("input[type='password']").fill(PASSWORD)
            await page.locator("button[type='submit']").click()
            await asyncio.sleep(4)

        # Look for Create Project / New Agent button
        create_btn = page.locator("button:has-text('Create'), button:has-text('New Project'), button:has-text('New Agent'), button:has-text('Build')").first
        if await create_btn.is_visible():
            print("Found Create button:", await create_btn.inner_text())
            await create_btn.click()
            await asyncio.sleep(3)

        # Take screenshot of builder/modal
        await page.screenshot(path="C:/Users/srivish/.gemini/antigravity/brain/65102128-f43c-470f-8dfd-0262e2720085/sns_create_30.png")
        print("Captured screenshot sns_create_30.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

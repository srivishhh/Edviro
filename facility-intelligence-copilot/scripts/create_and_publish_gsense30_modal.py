import asyncio
from playwright.async_api import async_playwright

SNS_URL = "https://agents.snsihub.ai/dashboard"
EMAIL = "srivishnu.s.cse.2024@snsct.org"
PASSWORD = "#Brucevish23"

async def main():
    print("--- CREATING & PUBLISHING 'GSENSE 3.0' WORKFLOW WITH MODAL INTERACTION ---")
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

        # Open Agent Builder
        builder_btn = page.locator("button:has-text('Agent Builder')").first
        if await builder_btn.is_visible():
            await builder_btn.click()
            await asyncio.sleep(3)

        # Click Deploy
        deploy_btn = page.locator("button:has-text('Deploy')").first
        if await deploy_btn.is_visible():
            print("Clicking Deploy (force=True)...")
            await deploy_btn.click(force=True)
            await asyncio.sleep(2)

        # Inspect any open modal dialog
        modal_input = page.locator("div[role='dialog'] input, div[data-state='open'] input").first
        if await modal_input.is_visible():
            print("Modal input detected! Filling 'GSENSE 3.0'...")
            await modal_input.fill("GSENSE 3.0")
            await asyncio.sleep(1)

        modal_confirm = page.locator("div[role='dialog'] button:has-text('Deploy'), div[role='dialog'] button:has-text('Publish'), div[role='dialog'] button:has-text('Confirm'), div[role='dialog'] button:has-text('Save')").first
        if await modal_confirm.is_visible():
            print("Clicking Modal confirm button...")
            await modal_confirm.click()
            await asyncio.sleep(3)

        await page.screenshot(path="C:/Users/srivish/.gemini/antigravity/brain/65102128-f43c-470f-8dfd-0262e2720085/sns_gsense30_modal_success.png")
        print("Captured screenshot sns_gsense30_modal_success.png")

        # Go back to dashboard to list projects
        await page.goto(SNS_URL, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        body_text = await page.inner_text("body")
        print("Dashboard contains GSENSE 3.0:", "GSENSE 3.0" in body_text)
        print("Dashboard text preview:", body_text[:400].replace("\n", " "))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

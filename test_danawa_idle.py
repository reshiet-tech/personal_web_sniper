import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Wait for networkidle instead
        await page.goto("https://m.danawa.com/product/product.html?code=88205561", wait_until="networkidle")
        
        # Wait specifically for the price class if we know it
        try:
            await page.wait_for_selector(".lowest_price", timeout=5000)
        except:
            pass
            
        current_content = await page.locator("body").inner_text()
        import re
        matches = re.finditer(r".{0,20}원.{0,20}", current_content)
        for m in matches:
            print("MATCH:", m.group(0))
        
        print("Total length:", len(current_content))
        await browser.close()

asyncio.run(main())

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://m.danawa.com/product/product.html?code=88205561", wait_until="domcontentloaded")
        
        candidates = [".product_info_details", ".box__prod-summary", ".title_compare_area", ".gprice_comparea_area", ".box__prod-lowest-info"]
        
        for c in candidates:
            try:
                text = await page.locator(c).inner_text()
                print(f"--- Selector {c} ---")
                print(text[:200])
            except Exception as e:
                pass
                
        await browser.close()

asyncio.run(main())

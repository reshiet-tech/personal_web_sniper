import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://m.danawa.com/product/product.html?code=88205561", wait_until="domcontentloaded")
        
        # Get the title text
        title_elem = await page.locator(".prod_name, .title, h1, .detail_title").first.inner_text()
        print("Title candidates:")
        print(title_elem)
        
        # Get price candidates
        prices = await page.locator(".lowest_price, .price, .lwst_prc, .prc_c, em").all_inner_texts()
        print("\nPrice candidates:")
        for pr in prices[:10]:
            print(pr.strip())
            
        # Or just get a wrapper that contains both
        summary = await page.locator(".prod_info, .product_summary, .detail_summary, .info_top").all_inner_texts()
        print("\nSummary wrapper:")
        for s in summary[:2]:
            print(s[:500])
            
        await browser.close()

asyncio.run(main())

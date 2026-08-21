import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://m.danawa.com/product/product.html?code=88205561", wait_until="domcontentloaded")
        
        # print all classes on the body or main container
        main_classes = await page.evaluate("() => Array.from(document.querySelectorAll('div')).map(el => el.className).filter(c => c.includes('prod') || c.includes('price') || c.includes('title'))")
        print("Classes related to prod/price/title:")
        print(list(set(main_classes))[:20])
        
        await browser.close()

asyncio.run(main())

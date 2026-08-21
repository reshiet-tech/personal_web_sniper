import asyncio
from src.config import load_targets
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    targets = load_targets()
    danawa_target = next(t for t in targets if t['name'] == '스위치2 젤다 왕눈')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        await page.goto(danawa_target['url'], wait_until="domcontentloaded")
        current_content = await page.locator("body").inner_text()
        
        # print around the price
        import re
        matches = re.finditer(r".{0,20}원.{0,20}", current_content)
        for m in matches:
            print(m.group(0))
        
        await browser.close()

asyncio.run(main())

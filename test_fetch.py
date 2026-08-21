import asyncio
from src.config import load_targets
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from src.fetcher import fetch_and_normalize

async def main():
    targets = load_targets()
    danawa_target = next(t for t in targets if t['name'] == '스위치2 젤다 왕눈')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        result = await fetch_and_normalize(page, danawa_target)
        
        print("Price extracted:", result.get("price"))
        print("Text snippet:", result.get("text")[:200])
        
        await browser.close()

asyncio.run(main())

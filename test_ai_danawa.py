import asyncio
import json
from src.config import load_targets
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from src.ai_filter import evaluate_diff_with_ai
import re
import difflib

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
        
        # We need to simulate the AI summary error
        # Let's check what evaluate_diff_with_ai outputs for small changes
        # Replace price to trigger a change
        old_content = re.sub(r"6[0-9],\d{3}", "150,000", current_content)
        old_content = re.sub(r"7[0-9],\d{3}", "150,000", old_content)
        
        old_lines = old_content.splitlines()
        new_lines = current_content.splitlines()
        
        diff = difflib.ndiff(old_lines, new_lines)
        added = []
        removed = []
        for line in diff:
            if line.startswith('+ '): added.append(line[2:])
            elif line.startswith('- '): removed.append(line[2:])
            
        print(f"Added lines: {len(added)}, Removed lines: {len(removed)}")
        
        is_meaningful, summary = evaluate_diff_with_ai(
            danawa_target['name'], 
            added, 
            removed, 
            danawa_target.get('ai_prompt', "")
        )
        
        print(f"Is Meaningful: {is_meaningful}")
        print(f"Summary: {summary}")
        
        await browser.close()

asyncio.run(main())

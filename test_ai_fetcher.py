import asyncio
import json
import re
import difflib
from src.config import load_targets
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from src.fetcher import fetch_and_normalize
from src.ai_filter import evaluate_diff_with_ai

async def main():
    targets = load_targets()
    danawa_target = next(t for t in targets if t['name'] == '스위치2 젤다 왕눈')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Use the actual fetcher
        current_content = await fetch_and_normalize(page, danawa_target)
        
        # Fake an old content where price was 85,000
        # Let's see if we can find any 7X,XXX price
        old_content = re.sub(r"7[0-9],\d{3}", "85,000", current_content)
        old_content = re.sub(r"6[0-9],\d{3}", "85,000", old_content)
        
        old_lines = old_content.splitlines()
        new_lines = current_content.splitlines()
        
        diff = difflib.ndiff(old_lines, new_lines)
        added = []
        removed = []
        for line in diff:
            if line.startswith('+ '): added.append(line[2:])
            elif line.startswith('- '): removed.append(line[2:])
            
        print("--- DIFF ---")
        print("ADDED:")
        print("\n".join(added[:10]))
        print("\nREMOVED:")
        print("\n".join(removed[:10]))
        
        # Now run AI
        is_meaningful, summary = evaluate_diff_with_ai(
            danawa_target['name'], 
            added, 
            removed, 
            danawa_target.get('ai_prompt', "")
        )
        
        print("\n--- AI RESULT ---")
        print(f"Is Meaningful: {is_meaningful}")
        print(f"Summary: {summary}")
        
        await browser.close()

asyncio.run(main())

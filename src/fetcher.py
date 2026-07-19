import asyncio
import re
import requests
from bs4 import BeautifulSoup
from src.config import get_logger

logger = get_logger(__name__)

async def fetch_and_normalize(page, target):
    """Playwright를 이용해 DOM을 가져오고 정규화하여 텍스트를 반환합니다."""
    url = target["url"]
    selector = target.get("selector", "body")
    ignore_selectors = target.get("ignore_selectors", [])
    ignore_regex = target.get("ignore_regex", [])
    
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    # SPA 웹사이트(컬리 등)가 JS로 '담기' 버튼을 '품절'로 바꾸는 시간을 충분히 기다림
    await asyncio.sleep(10)
    
    # DOM 정규화 및 불필요한 요소 제거
    if ignore_selectors:
        await page.evaluate("""(selectors) => {
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });
        }""", ignore_selectors)
    
    content = await page.locator(selector).inner_text()
    
    # 정규표현식을 이용한 무의미한 텍스트 제거
    if ignore_regex:
        for regex_pattern in ignore_regex:
            try:
                content = re.sub(regex_pattern, "", content, flags=re.MULTILINE)
            except Exception as e:
                logger.warning(f"정규식 처리 오류 ({regex_pattern}): {e}")
                
    return content

async def fetch_simple(target):
    """requests와 BeautifulSoup을 이용하여 브라우저 없이 단순 HTML을 가져옵니다. (WAF 우회용)"""
    url = target["url"]
    selector = target.get("selector", "body")
    ignore_selectors = target.get("ignore_selectors", [])
    ignore_regex = target.get("ignore_regex", [])
    
    def _do_fetch():
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 불필요한 요소 제거
        for sel in ignore_selectors:
            for el in soup.select(sel):
                el.decompose()
                
        # 타겟 영역 추출
        if selector == "body":
            target_el = soup.body if soup.body else soup
        else:
            target_el = soup.select_one(selector)
            
        if not target_el:
            return ""
            
        return target_el.get_text(separator='\n', strip=True)
        
    content = await asyncio.to_thread(_do_fetch)
    
    # 정규표현식을 이용한 무의미한 텍스트 제거
    if ignore_regex:
        for regex_pattern in ignore_regex:
            try:
                content = re.sub(regex_pattern, "", content, flags=re.MULTILINE)
            except Exception as e:
                logger.warning(f"정규식 처리 오류 ({regex_pattern}): {e}")
                
    return content

import asyncio
import re
import json
import requests
from bs4 import BeautifulSoup
from src.config import get_logger
from src.ai_filter import extract_price_with_ai

logger = get_logger(__name__)

def extract_price_from_html(html_content):
    """HTML에서 JSON-LD (SEO) 데이터를 파싱하여 가격을 정확하게 추출합니다."""
    soup = BeautifulSoup(html_content, 'html.parser')
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if 'offers' in data:
                offers = data['offers']
                if isinstance(offers, dict) and 'lowPrice' in offers:
                    return int(offers['lowPrice'])
                if isinstance(offers, dict) and 'price' in offers:
                    return int(offers['price'])
                elif isinstance(offers, list) and len(offers) > 0 and 'price' in offers[0]:
                    return int(offers[0]['price'])
            if '@graph' in data:
                for item in data['@graph']:
                    if 'offers' in item and 'lowPrice' in item['offers']:
                        return int(item['offers']['lowPrice'])
        except Exception:
            continue
    return None

async def fetch_and_normalize(page, target):
    """Playwright를 이용해 DOM을 가져오고 정규화하여 텍스트 및 메타데이터를 반환합니다."""
    url = target["url"]
    selector = target.get("selector", "body")
    ignore_selectors = target.get("ignore_selectors", [])
    ignore_regex = target.get("ignore_regex", [])
    target_type = target.get("type", "keyword_monitor")
    
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(5)
    
    # DOM 정규화 및 불필요한 요소 제거
    if ignore_selectors:
        await page.evaluate("""(selectors) => {
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });
        }""", ignore_selectors)
    
    content = await page.locator(selector).inner_text()
    html_content = await page.content()
    
    # 정규표현식을 이용한 무의미한 텍스트 제거
    if ignore_regex:
        for regex_pattern in ignore_regex:
            try:
                content = re.sub(regex_pattern, "", content, flags=re.MULTILINE)
            except Exception as e:
                logger.warning(f"정규식 처리 오류 ({regex_pattern}): {e}")
                
    price = None
    if target_type == "price_monitor":
        price = extract_price_from_html(html_content)
        if price is None:
            logger.info(f"[{target['name']}] JSON-LD에서 가격을 찾지 못해 AI 추출을 시도합니다.")
            price = extract_price_with_ai(target['name'], content)
            
    return {
        "text": content,
        "price": price
    }

async def fetch_simple(target):
    """requests와 BeautifulSoup을 이용하여 브라우저 없이 단순 HTML을 가져옵니다. (WAF 우회용)"""
    url = target["url"]
    selector = target.get("selector", "body")
    ignore_selectors = target.get("ignore_selectors", [])
    ignore_regex = target.get("ignore_regex", [])
    target_type = target.get("type", "keyword_monitor")
    
    def _do_fetch():
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text

    html_content = await asyncio.to_thread(_do_fetch)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for sel in ignore_selectors:
        for el in soup.select(sel):
            el.decompose()
            
    if selector == "body":
        selected = soup.body if soup.body else soup
    else:
        selected = soup.select_one(selector)
        
    content = selected.get_text(separator='\n', strip=True) if selected else ""
    
    if ignore_regex:
        for regex_pattern in ignore_regex:
            try:
                content = re.sub(regex_pattern, "", content, flags=re.MULTILINE)
            except Exception as e:
                logger.warning(f"정규식 처리 오류 ({regex_pattern}): {e}")
                
    price = None
    if target_type == "price_monitor":
        price = extract_price_from_html(html_content)
        if price is None:
            logger.info(f"[{target['name']}] JSON-LD에서 가격을 찾지 못해 AI 추출을 시도합니다.")
            price = extract_price_with_ai(target['name'], content)
            
    return {
        "text": content,
        "price": price
    }

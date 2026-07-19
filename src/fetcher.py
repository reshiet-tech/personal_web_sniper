import asyncio
import re
from src.config import get_logger

logger = get_logger(__name__)

async def fetch_and_normalize(page, target):
    """Playwright를 이용해 DOM을 가져오고 정규화하여 텍스트를 반환합니다."""
    url = target["url"]
    selector = target.get("selector", "body")
    ignore_selectors = target.get("ignore_selectors", [])
    ignore_regex = target.get("ignore_regex", [])
    
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(6)
    
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
                content = re.sub(regex_pattern, "", content)
            except Exception as e:
                logger.warning(f"정규식 처리 오류 ({regex_pattern}): {e}")
                
    return content

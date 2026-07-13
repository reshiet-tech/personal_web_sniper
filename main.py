import asyncio
import os
import sys
import logging
import requests
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 환경변수 로드 (로컬 테스트용 .env 파일이 있으면 로드, GitHub Actions에서는 Secrets로 주입됨)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message: str):
    """텔레그램 봇 API를 사용하여 알림을 전송합니다."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("텔레그램 토큰 또는 Chat ID가 설정되지 않아 알림을 보낼 수 없습니다.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("텔레그램 알림 전송 성공")
    except Exception as e:
        logger.error(f"텔레그램 알림 전송 실패: {e}")

import json

# 감지할 타겟 사이트 목록을 targets.json 파일에서 불러옵니다.
def load_targets():
    if not os.path.exists("targets.json"):
        logger.warning("targets.json 파일이 없습니다. 빈 목록으로 시작합니다.")
        return []
    with open("targets.json", "r", encoding="utf-8") as f:
        return json.load(f)

TARGET_SITES = load_targets()

async def check_site_status(page, target):
    """지정된 사이트에 접속하여 상태를 확인합니다."""
    name = target["name"]
    url = target["url"]
    selector = target["selector"]
    success_texts = target["success_text"]
    failure_texts = target["failure_text"]

    try:
        logger.info(f"[{name}] 접속 중: {url}")
        
        # networkidle 옵션: 네트워크 요청이 최소 500ms 동안 없을 때까지 대기 (동적 렌더링 사이트 대응)
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # 페이지가 완전히 렌더링될 수 있도록 약간의 추가 대기 시간
        await asyncio.sleep(2)
        
        # 특정 요소나 body 전체의 텍스트 가져오기
        content = await page.locator(selector).inner_text()
        
        # 성공 텍스트 포함 여부 확인
        is_success = any(text in content for text in success_texts)
        # 실패 텍스트 포함 여부 확인
        is_failure = any(text in content for text in failure_texts)

        if is_success and not is_failure:
            logger.info(f"[{name}] 상태 변경 감지! (예약/구매 가능)")
            # 텔레그램 메시지 구성
            message = f"🚨 <b>{name} 스나이퍼 알림</b> 🚨\n\n✅ <b>상태:</b> 예약/구매 가능\n🔗 <b>링크:</b> <a href='{url}'>바로가기</a>"
            send_telegram_message(message)
        elif is_failure:
            logger.info(f"[{name}] 상태: 불가능 (품절/예약마감)")
        else:
            logger.info(f"[{name}] 성공/실패 텍스트를 명확히 찾지 못했습니다. 상태 확인 필요.")
            
    except Exception as e:
        logger.error(f"[{name}] 확인 중 에러 발생: {e}")

async def main():
    logger.info("=== 웹 스나이퍼 봇 실행 시작 ===")
    
    async with async_playwright() as p:
        # 봇 탐지 우회를 위한 브라우저 설정 (헤드리스 모드)
        browser = await p.chromium.launch(headless=True)
        
        # User-Agent 및 기본 설정 적용
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        page = await context.new_page()

        for target in TARGET_SITES:
            await check_site_status(page, target)
            # IP 차단을 막기 위해 사이트 간 랜덤 딜레이 또는 고정 딜레이 추가
            await asyncio.sleep(3)

        await browser.close()
        
    logger.info("=== 웹 스나이퍼 봇 실행 종료 ===")

if __name__ == "__main__":
    asyncio.run(main())

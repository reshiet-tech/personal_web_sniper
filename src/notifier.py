import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, get_logger

logger = get_logger(__name__)

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

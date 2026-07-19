import json
import requests
from src.config import GEMINI_API_KEY, get_logger

logger = get_logger(__name__)

def evaluate_diff_with_ai(target_name: str, added: list, removed: list) -> bool:
    """
    Gemini API를 호출하여 이 변경사항(Diff)이 유의미한지 평가합니다.
    유의미하면 True, 무의미하면 False를 반환합니다.
    """
    if not GEMINI_API_KEY:
        # API 키가 없으면 기본적으로 유의미하다고 판단 (기존 로직 유지)
        return True

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    
    diff_text = f"추가된 내용:\n" + "\n".join(added) + "\n\n삭제된 내용:\n" + "\n".join(removed)
    
    prompt = f"""
    너는 상품 재고 및 예약 모니터링을 담당하는 어시스턴트야.
    내가 웹페이지에서 감지한 텍스트 변경점(추가된 내용, 삭제된 내용)을 줄게.
    이 사이트의 이름은 [{target_name}] 야.

    변경점이 다음 중 하나라도 해당하면 무의미한 변경(가짜 알림)이므로 무조건 'NO' 라고 대답해:
    1. 날짜, 시간, 실시간 검색어, '당일특가' 같은 수식어의 변경
    2. 후기 개수, 찜 개수, 평점, 조회수 증감
    3. 배송 방법(예: 샛별배송, 일반배송), 배송 시간 안내 문구의 변경
    4. 동일한 '품절'이나 '상품준비중' 텍스트가 삭제되었다가 다시 추가된 경우 (위치만 바뀐 경우)
    5. 다른 추천 상품의 이름이 노출된 경우 (예: 스카이베이호텔 등)

    오직 아래의 경우에만 유의미한 변경이므로 'YES' 라고 대답해:
    - 감시 대상 상품의 '품절'이 완전히 풀리고 '예약하기', '구매하기', '장바구니' 등의 버튼이 명확하게 새로 생긴 경우
    - 새로운 날짜의 예약이 확실하게 오픈된 경우
    **주의**: 만약 애매하거나 재고 입고가 확실하지 않다면 무조건 'NO'라고 대답해!

    다른 설명은 일절 하지 말고 오직 'YES' 또는 'NO' 로만 대답해.

    [변경점 시작]
    {diff_text}
    [변경점 끝]
    """

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 5,
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        result = response.json()
        
        answer = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip().upper()
        
        logger.info(f"[{target_name}] AI 판독 결과: {answer}")
        
        if "YES" in answer:
            return True
        else:
            return False
            
    except Exception as e:
        logger.error(f"[{target_name}] Gemini API 호출 중 오류 발생: {e}")
        # API 오류 시에는 안전하게 True를 반환하여 알림을 놓치지 않도록 함
        return True

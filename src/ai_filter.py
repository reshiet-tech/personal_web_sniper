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

    변경점이 다음 중 하나에 해당하면 무의미한 변경(가짜 알림)이므로 무조건 'NO' 라고 대답해:
    - 날짜, 시간, 실시간 검색어의 변경
    - 후기 개수, 찜 개수, 조회수 증감
    - 배송 방법(예: 샛별배송, 일반배송)이나 배송 안내 문구의 변경
    - 단순 UI 변경이나 광고 배너 텍스트 변경
    - 품절 상태가 유지되고 있는데 문구만 바뀐 경우

    하지만 다음 중 하나에 해당하면 유의미한 변경이므로 'YES' 라고 대답해:
    - 상품의 '품절'이 풀리고 '예약하기', '구매하기', '장바구니' 등의 버튼이 생김
    - 새로운 날짜의 예약이 오픈됨
    - 재고가 들어왔거나 가격이 의미 있게 하락함
    - 그 외에 사용자가 반드시 당장 확인해야 할 중요한 알림

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

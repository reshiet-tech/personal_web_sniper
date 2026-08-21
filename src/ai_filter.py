import json
import requests
import time
from src.config import GEMINI_API_KEY, get_logger

logger = get_logger(__name__)

def extract_price_with_ai(target_name: str, html_text: str):
    """
    Gemini API를 호출하여 웹페이지 텍스트에서 가격을 추출합니다.
    오직 JSON 형식으로만 반환하도록 강제합니다.
    """
    if not GEMINI_API_KEY:
        logger.warning("API 키가 없어 AI 가격 추출을 건너뜁니다.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    
    # 텍스트가 너무 길면 앞부분만 자릅니다 (보통 가격은 초반/중반에 위치함)
    max_length = 30000
    if len(html_text) > max_length:
        html_text = html_text[:max_length]
    
    prompt = f"""
당신은 웹페이지 텍스트에서 특정 상품의 최저 가격을 추출하는 데이터 추출기입니다.
사이트/상품 이름: {target_name}

아래 제공되는 웹페이지 텍스트를 분석하여 해당 상품의 현재 최저 가격(숫자)을 추출하세요.
배송비가 명시되어 있다면 포함된 가격을, 아니라면 표기된 상품 가격을 추출하세요.
만약 가격 정보를 도저히 찾을 수 없다면 null을 반환하세요.

반드시 아래 JSON 형식으로만 응답해야 하며, 다른 텍스트는 절대 포함하지 마세요.
{{"price": 75000}}

[웹페이지 텍스트 시작]
{html_text}
[웹페이지 텍스트 끝]
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }

    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 429:
                logger.warning(f"[{target_name}] AI API 요청 한도 초과(429). {attempt+1}차 재시도 대기(10초)...")
                time.sleep(10)
                continue
                
            response.raise_for_status()
            result = response.json()
            
            candidates = result.get("candidates", [])
            if not candidates:
                return None
            candidate = candidates[0]
            answer = candidate.get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            
            try:
                parsed = json.loads(answer)
                return parsed.get("price")
            except json.JSONDecodeError:
                logger.error(f"AI JSON 파싱 실패: {answer}")
                return None
                
        except Exception as e:
            logger.error(f"[{target_name}] Gemini API 호출 중 오류 발생: {e}")
            if attempt < 2:
                time.sleep(5)
                continue
            return None
            
    return None

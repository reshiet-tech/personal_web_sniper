import json
import requests
from src.config import GEMINI_API_KEY, get_logger

logger = get_logger(__name__)

def evaluate_diff_with_ai(target_name: str, added: list, removed: list, custom_prompt: str = "") -> bool:
    """
    Gemini API를 호출하여 이 변경사항(Diff)이 유의미한지 평가합니다.
    유의미하면 True, 무의미하면 False를 반환합니다.
    """
    if not GEMINI_API_KEY:
        # API 키가 없으면 기본적으로 유의미하다고 판단 (기존 로직 유지)
        return True, "API 키가 설정되지 않아 AI 요약을 건너뛰었습니다."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    
    diff_text = f"추가된 내용:\n" + "\n".join(added) + "\n\n삭제된 내용:\n" + "\n".join(removed)
    
    # 너무 길 경우 앞/뒤만 남기고 자르기 (Gemini API 부하/타임아웃 방지)
    max_length = 20000
    if len(diff_text) > max_length:
        half = max_length // 2
        diff_text = diff_text[:half] + "\n\n... [중략] ...\n\n" + diff_text[-half:]
    
    custom_instruction = ""
    if custom_prompt.strip():
        custom_instruction = f"[사용자 특별 요청사항]\n{custom_prompt.strip()}\n"

    prompt = f"""
당신은 웹사이트의 변경사항을 감시하는 어시스턴트입니다.
사이트 이름: {target_name}

{custom_instruction}
아래는 이전 텍스트와 비교하여 새롭게 추가되거나 삭제된 텍스트입니다.
(삭제된 내용 = 과거 상태 / 추가된 내용 = 현재 상태)

[변경점 시작]
{diff_text}
[변경점 끝]

위 변경사항을 분석하여, 사용자에게 알림을 보낼 만큼 유의미한(중요한) 변경인지 판단하세요.
특히 가격 변동이나 재고(품절 해제) 여부를 주의 깊게 확인하세요.

응답 규칙 (반드시 지킬 것):
- 만약 유의미한 변경이라면 반드시 'YES|' 로 시작하고, 그 뒤에 변경된 핵심 이유를 명확하게 1문장으로 적으세요.
  (예시: YES|가격이 85,000원에서 71,000원으로 하락했습니다.)
- 만약 무의미한 변경이거나, 조건에 맞지 않거나, 명확한 단서가 없다면 오직 'NO' 라고만 대답하세요.
- 절대로 이 규칙 외의 다른 말을 덧붙이지 마세요.
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 150,
        }
    }

    import time
    
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
                logger.warning(f"[{target_name}] AI 응답에 candidates가 없습니다. 결과: {result}")
                return True, "AI 분석 중 오류가 발생하여 내용을 요약할 수 없습니다."
                
            candidate = candidates[0]
            if "content" not in candidate:
                logger.warning(f"[{target_name}] AI 응답이 필터링되었거나 내용이 없습니다. 결과: {candidate}")
                return True, "AI 분석이 차단되었거나 내용을 요약할 수 없습니다."
                
            answer = candidate.get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            logger.info(f"[{target_name}] AI 판독 결과: {answer}")
            
            if answer.upper().startswith("YES"):
                parts = answer.split("|", 1)
                summary = parts[1].strip() if len(parts) > 1 else "AI 판단: 조건이 충족되었습니다."
                return True, summary
            else:
                return False, ""
                
        except Exception as e:
            logger.error(f"[{target_name}] Gemini API 호출 중 오류 발생: {e}")
            if attempt < 2:
                time.sleep(5)
                continue
            # API 오류(특히 429 한도 초과) 시 True를 반환하면 계속해서 오탐 알림이 폭주하므로 False를 반환하여 스킵합니다.
            return False, ""
            
    return False, ""

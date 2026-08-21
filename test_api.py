import requests
import json
from src.config import GEMINI_API_KEY

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"

prompt = """
당신은 웹사이트의 변경사항을 감시하는 어시스턴트입니다.
대상: 스위치2 젤다 왕눈

사용자의 특별 요청(가장 우선순위가 높음):
기존 내용에 있던 가격보다 현재 가격이 더 저렴해진(할인된) 경우에만 알려줘
가격 변동이 없거나 오히려 비싸졌다면 무조건 무시해
타겟제품은 스위치2 젤다의 전설 티어즈 오브 킹덤(왕국의 눈물) 게임칩이야(배송지 포함)

너가 확인해야할 젤다 게임칩 가격은 75,000이하야

아래는 이전 내용과 비교하여 새롭게 추가되거나 삭제된 텍스트입니다.
추가된 내용:
최저가 71,000원
할인 쿠폰 적용 가능

삭제된 내용:
최저가 85,000원
품절

위 변경사항을 분석하여, 사용자에게 알림을 보낼 만큼 의미 있는(중요한) 변경인지 판단하세요.
만약 유의미한 변경이라면 반드시 'YES|' 로 시작하고 그 뒤에 1~2줄로 이유를 요약하세요.
무의미한 변경이라면 'NO' 라고만 대답하세요.
"""

payload = {"contents": [{"parts": [{"text": prompt}]}]}

r = requests.post(url, json=payload)
print(json.dumps(r.json(), indent=2, ensure_ascii=False))

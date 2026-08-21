from src.ai_filter import evaluate_diff_with_ai

added = ["최저가 71,000원", "할인 쿠폰 적용 가능"]
removed = ["최저가 85,000원", "품절"]
custom_prompt = "기존 내용에 있던 가격보다 현재 가격이 더 저렴해진(할인된) 경우에만 알려줘\n가격 변동이 없거나 오히려 비싸졌다면 무조건 무시해\n타겟제품은 스위치2 젤다의 전설 티어즈 오브 킹덤(왕국의 눈물) 게임칩이야(배송지 포함)\n\n너가 확인해야할 젤다 게임칩 가격은 75,000이하야"

res, summary = evaluate_diff_with_ai("스위치2 젤다 왕눈", added, removed, custom_prompt)
print("Result:", res)
print("Summary:", summary)

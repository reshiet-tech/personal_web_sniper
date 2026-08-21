import json

with open("data/snapshots.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Inject a fake snapshot for "스위치2 젤다 왕눈"
data["스위치2 젤다 왕눈"] = "상품명: 스위치2 젤다의 전설 티어즈 오브 킹덤\n가격: 100,000,000원\n상태: 품절 아님"

with open("data/snapshots.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
print("Injected fake snapshot!")

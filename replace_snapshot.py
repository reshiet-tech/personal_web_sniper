import json
import re

with open("data/snapshots.json", "r", encoding="utf-8") as f:
    data = json.load(f)

text = data.get("스위치2 젤다 왕눈", "")
# replace any 65,XXX or 70,XXX or similar price patterns with 150,000
text = re.sub(r"65,\d{3}", "150,000", text)
text = re.sub(r"70,\d{3}", "150,000", text)
text = re.sub(r"71,\d{3}", "150,000", text)
data["스위치2 젤다 왕눈"] = text

text2 = data.get("다나와_스플래툰 레이더스", "")
text2 = re.sub(r"68,\d{3}", "150,000", text2)
text2 = re.sub(r"71,\d{3}", "150,000", text2)
data["다나와_스플래툰 레이더스"] = text2

with open("data/snapshots.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
print("Snapshots fully faked for price drops.")

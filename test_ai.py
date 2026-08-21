import asyncio
from src.ai_filter import evaluate_diff_with_ai
from src.config import load_targets
import json

with open("data/snapshots.json", "r", encoding="utf-8") as f:
    snapshots = json.load(f)

danawa_text = snapshots.get("스위치2 젤다 왕눈", "dummy text")
added = danawa_text.split("\n")
removed = ["이전 내용 1", "이전 내용 2"]

print(f"Added lines: {len(added)}")

try:
    res, summary = evaluate_diff_with_ai("스위치2 젤다 왕눈", added, removed, "테스트 프롬프트")
    print("Result:", res)
    print("Summary:", summary)
except Exception as e:
    print("Exception thrown:", e)

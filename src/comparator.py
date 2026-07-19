import os
import json
import difflib

def load_snapshots():
    if not os.path.exists("data/snapshots.json"):
        return {}
    try:
        with open("data/snapshots.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_snapshots(snapshots):
    os.makedirs("data", exist_ok=True)
    with open("data/snapshots.json", "w", encoding="utf-8") as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=4)

def get_text_diff(old_text, new_text):
    old_lines = [line.strip() for line in old_text.splitlines() if line.strip()]
    new_lines = [line.strip() for line in new_text.splitlines() if line.strip()]
    
    diff = difflib.unified_diff(old_lines, new_lines, n=0, lineterm="")
    added = []
    removed = []
    
    for line in diff:
        if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
            continue
        if line.startswith('+'):
            added.append(line[1:])
        elif line.startswith('-'):
            removed.append(line[1:])
            
    return added, removed

import json
with open('usage_history.json', 'r') as f:
    history = json.load(f)
for r in history[-10:]:
    print(f"{r['timestamp'][11:16]}  gem={r['gemini_5h']:5.1f}  ext={r['external_5h']:5.1f}")

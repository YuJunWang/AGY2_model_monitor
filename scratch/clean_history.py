import json
from datetime import datetime

with open('usage_history.json', 'r') as f:
    history = json.load(f)

print(f'Before dedup: {len(history)} records')

cleaned = []
for r in history:
    if cleaned:
        last = cleaned[-1]
        try:
            t_last = datetime.fromisoformat(last['timestamp'])
            t_curr = datetime.fromisoformat(r['timestamp'])
            delta_s = (t_curr - t_last).total_seconds()
            # Skip if same values AND within 30 seconds
            if delta_s < 30 and last['gemini_5h'] == r['gemini_5h'] and last['external_5h'] == r['external_5h']:
                continue
        except:
            pass
    cleaned.append(r)

print(f'After dedup: {len(cleaned)} records')
print()
print(f"{'Time':8s}  {'Gemini':>8s}  {'External':>8s}")
print("-" * 32)
for r in cleaned:
    print(f"{r['timestamp'][11:16]}    {r['gemini_5h']:6.1f}    {r['external_5h']:6.1f}")

with open('usage_history.json', 'w') as f:
    json.dump(cleaned, f, indent=2)
print()
print('Saved cleaned history.')

# scripts/check-lineup.py — run: uv run --no-project python scripts/check-lineup.py
import json, re
src = open('lineup.js', encoding='utf-8').read()
payload = re.search(r'const LINEUP = (\[.*\]);', src, re.S).group(1)
lineup = json.loads(payload)  # generator must emit JSON-compatible literals
sizes = [s['size'] for s in lineup]
assert sizes == ['1MR', '1MC', '3M', '5M', '5BR', '7M', '8K', '17K', 'F350'], sizes
counts = {s['size']: len(s['colors']) for s in lineup}
assert counts == {'1MR': 21, '1MC': 25, '3M': 42, '5M': 50, '5BR': 16,
                  '7M': 15, '8K': 33, '17K': 10, 'F350': 10}, counts
cats = {'Standard', 'Pastel', 'Fluo', 'Metallic', 'Glitter'}
all_keys = [c['key'] for s in lineup for c in s['colors']]
assert len(all_keys) == len(set(all_keys)), 'duplicate keys'
for s in lineup:
    for c in s['colors']:
        assert c['key'].startswith(s['size'] + ':'), c
        assert re.fullmatch(r'#[0-9a-f]{6}', c['hex']), c
        assert c['category'] in cats, c
        assert c['number'] is None or re.fullmatch(r'[PFMG]?\d+', c['number']), c
glitter = [c for c in next(s for s in lineup if s['size'] == '3M')['colors']
           if c['category'] == 'Glitter']
assert len(glitter) == 8, len(glitter)
nulls = [(s['size'], c['name']) for s in lineup for c in s['colors'] if c['number'] is None]
print('lineup OK ·', len(nulls), 'unverified numbers:', nulls)

import json
scrape = json.load(open('scripts/posca-scrape.json'))
legacy = json.load(open('scripts/legacy-map.json'))
EXPECTED = {'pc-1mr': 21, 'pc1-mc': 25, 'pc-3m': 42, 'pc-5m': 50, 'pc-5br': 16,
            'pc-7m': 15, 'pc-8k': 33, 'pc-17k': 10, 'pcf-350': 10}
for slug, n in EXPECTED.items():
    found = scrape[slug]['found']
    assert found == n, f'{slug}: {found} != {n}'
    assert int(scrape[slug]['declared_count']) == n, f'{slug}: declared mismatch'
assert len(legacy) == 68, f'legacy map count changed: {len(legacy)}'
assert all(set(e) == {'category', 'number', 'name', 'hex'} for e in legacy)
print('sources OK')

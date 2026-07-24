# scripts/build-lineup.py — regenerates lineup.js. Run: uv run --no-project python scripts/build-lineup.py
import json
SIZES = [  # (scrape slug, size key, label, tip)
    ('pc-1mr', '1MR', 'PC-1MR', 'extra fine 0.7 mm'),
    ('pc1-mc', '1MC', 'PC-1MC', 'fine conical 0.7-1 mm'),
    ('pc-3m',  '3M',  'PC-3M',  'fine 0.9-1.3 mm'),
    ('pc-5m',  '5M',  'PC-5M',  'medium 1.8-2.5 mm'),
    ('pc-5br', '5BR', 'PC-5BR', 'brush'),
    ('pc-7m',  '7M',  'PC-7M',  'broad 4.5-5.5 mm'),
    ('pc-8k',  '8K',  'PC-8K',  'chisel 8 mm'),
    ('pc-17k', '17K', 'PC-17K', 'extra broad 15 mm'),
    ('pcf-350','F350','PCF-350','brush'),
]
scrape = json.load(open('scripts/posca-scrape.json'))
numbers = json.load(open('scripts/number-map.json'))

def normalize_name(name):
    """Display-normalize a posca.com color name to consistent Title Case.

    posca.com scrapes some names in ALL CAPS (e.g. 'CACAO BROWN', 'YELLOW
    FLUO') and others already in mixed case (e.g. 'Apple Green'). Per the
    2026-07-23 Round 2 decision, ALL-CAPS names get converted to Title Case;
    names that are already mixed-case are left untouched (str.title() would
    mangle things like 'McSomething', but posca.com has none of those, and
    this only fires when the source name is fully upper-case).
    """
    if name.isupper():
        return name.title()
    return name

# Category overrides for null-numbered colors (2026-07-23, Round 3).
#
# When a color's number is null, category() falls back to name-based
# detection, which defaults to Standard for anything without an obvious
# Glitter/Metallic/Fluorescent cue — wrong for colors that are actually
# Pastel-series. An override is recorded ONLY when BOTH saved independent
# sources agree on a non-Standard category via their section/series
# placement (not the posca.com number, which is null for these):
#
#   - scripts/second-source.html (PoscART PMS chart): flat name/number/hex
#     table; Glacier Blue -> number "P33" (P-prefix = Pastel).
#   - scripts/source-jennyscrayoncollection.html + .jpg (Jenny's Crayon
#     Collection infographic): PC-1MR text lists the 5 colors exclusive to
#     the UK assortment in bold — Apricot(P4), Aqua Green(P6), Glacier
#     Blue, Lavender(P11), Sunshine Yellow(P2). The other 4 are confirmed
#     Pastel-series (P-prefixed) in second-source.html, so Jenny's places
#     Glacier Blue in that same series-grouping even though her own
#     infographic (all 65 non-UK colors) doesn't carry it individually.
#   Both sources -> Pastel.
#
# Rounds 3 and 5 (2026-07-24) checked three more independent sources
# (mpuni.co.jp JP product pages, second-source.pdf, source-cultpens-pc5m
# .html) against the remaining nulls; see git history for the full
# per-color trail. None of them cleared the two-source/exact-hex bar, so
# Coral, Yellow Fluo, Grape Green, Pale Fluorescent Orange and Glacier Blue
# all stayed null pending a physical-cap check.
#
# Round 6 / Task N6 (2026-07-24) resolved three of those from the owner's
# physical cap reading ("physical cap (owner), 2026-07-24" — see
# HEX_NAME_CORRECTIONS below and .superpowers/sdd/task-N6-report.md):
# 3M's second "Brown" -> Dark Brown 22, 5M/5BR Coral -> Coral Pink 66, 5M
# Yellow Fluo -> Fluorescent Yellow F2. Remaining nulls (cap check pending):
# 1MR Glacier Blue, 5M Grape Green, 8K Pale Fluorescent Orange.
CATEGORY_OVERRIDES = {
    'glacier blue': 'Pastel',
}

# Hex-qualified name corrections from physical cap evidence (owner,
# 2026-07-24 — Task N6). Keyed by (posca.com scrape name lower, hex) so a
# correction only fires for the exact entry it was verified against, never
# for an unrelated color that happens to share the pre-correction name or
# hex alone. After renaming, the normal name-keyed lookup in
# number-map.json supplies the number, propagating to same-named entries in
# other sizes (e.g. 5M/5BR Coral Pink) exactly like every other color.
HEX_NAME_CORRECTIONS = {
    # 3M: cap has both nr 21 "Brown" and nr 22 "Dark Brown"; Jenny's saved
    # source pairs Dark Brown 22 with this exact hex.
    ('brown', '#572d2d'): 'Dark Brown',
    # 5M/5BR: cap PC-5M nr 66 is named "Coral Pink"; only coral in the range.
    ('coral', '#ff8da1'): 'Coral Pink',
    # 5M: cap F2 is named "F.Yellow"; display name matches sibling
    # Fluorescent Orange/Pink/Red.
    ('yellow fluo', '#ffff2e'): 'Fluorescent Yellow',
}

# Colors missing from the posca.com scrape (its PC-3M listing is incomplete),
# appended per size after the scraped colors as (name, hex). Hex reused from
# the same pigment in PC-5M; numbers resolve via number-map.json like every
# other color (2026-07-24 spec: docs/superpowers/specs/2026-07-24-lineup-gaps-
# scroll-anchor-owned-check-design.md).
EXTRA_COLORS = {
    '3M': [
        ('Aqua Green', '#71dbd4'),  # physical cap (owner, 2026-07-24): P6
        ('Coral Pink', '#ff8da1'),  # physical cap (owner, 2026-07-24): 66
        ('Orange', '#ff5c39'),      # both saved sources list PC-3M Orange
                                    # (Jenny's Crayon Collection, mpuni.co.jp)
    ],
    # posca.com's PC-1MC page misses the same newer colors as PC-3M did.
    # mpuni.co.jp lists the series as "PC-1M" (order codes PC1M.x) — same
    # series, EU naming PC-1MC; barrel print says PC-1M.
    '1MC': [
        ('Orange', '#ff5c39'),      # physical (owner, 2026-07-24) + mpuni
                                    # PC1M.4 + Jenny's Crayon Collection
        ('Sky Blue', '#009cde'),    # physical cap 48 + mpuni PC1M.48
        ('Coral Pink', '#ff8da1'),  # physical cap 66 + mpuni PC1M.66
        ('Aqua Green', '#71dbd4'),  # physical cap (owner, 2026-07-24): P6
        ('Apple Green', '#78be21'), # physical cap (owner, 2026-07-24): 72
    ],
}

def category(name, number):
    if number:
        pfx = number[0]
        if pfx == 'P': return 'Pastel'
        if pfx == 'F': return 'Fluo'
        if pfx == 'M': return 'Metallic'
        if pfx == 'G': return 'Glitter'
        return 'Standard'
    override = CATEGORY_OVERRIDES.get(name.lower())
    if override: return override
    for p, c in (('Glitter', 'Glitter'), ('Metallic', 'Metallic'), ('Fluorescent', 'Fluo')):
        if name.startswith(p): return c
    if 'fluo' in name.lower(): return 'Fluo'
    return 'Standard'

lineup = []
for slug, size, label, tip in SIZES:
    colors, seen = [], {}
    entries = list(scrape[slug]['colors']) + \
        [[hexv, name] for name, hexv in EXTRA_COLORS.get(size, [])]
    for hexv, raw_name in entries:
        name = normalize_name(raw_name)
        hexl = hexv.lower()
        name = HEX_NAME_CORRECTIONS.get((name.lower(), hexl), name)
        # posca.com lists some names twice within a size (e.g. Brown in PC-3M,
        # before the HEX_NAME_CORRECTIONS rename above splits it in two);
        # keys stay unique via a deterministic ordinal suffix in scrape order.
        seen[name] = seen.get(name, 0) + 1
        key = f'{size}:{name}' if seen[name] == 1 else f'{size}:{name}-{seen[name]}'
        if seen[name] == 1:
            num = numbers.get(name.lower())
        else:
            # Second+ occurrence of a name HEX_NAME_CORRECTIONS didn't
            # rename apart: only verified when a source explicitly pairs
            # THIS hex to a number, via a scripts/number-map.json 'name@hex'
            # key. No such case currently exists; stays name-verbatim,
            # number null until one does.
            num = numbers.get(f'{name.lower()}@{hexl}')
        colors.append({'key': key, 'name': name, 'number': num, 'hex': hexl,
                       'category': category(name, num)})
    lineup.append({'size': size, 'label': label, 'tip': tip, 'colors': colors})

body = json.dumps(lineup, indent=1)
open('lineup.js', 'w').write(
    '// Generated by scripts/build-lineup.py from scripts/posca-scrape.json'
    ' + scripts/number-map.json. Do not hand-edit colors.\n'
    f'const LINEUP = {body};\n')
print('lineup.js written')

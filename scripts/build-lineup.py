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
# Round 3 (2026-07-24) added a third independent source — scripts/
# source-mpuni-pc{1m,3m,5m,8k,17k}.html (mpuni.co.jp, Mitsubishi Pencil's
# official Japan site; product listings give each color's PC-<size>.<number>
# code, e.g. "黒" (Black) = PC5M.24 on all five size pages). It resolved
# Black -> 24 and White -> 1 (both plain numbers, so no CATEGORY_OVERRIDES
# entry — category() derives Standard from the numeric prefix directly).
# White is a 2-vs-1 split: mpuni + Jenny's agree on 1; second-source.html's
# 255 is outvoted (see .superpowers/sdd/task-N1-report.md).
#
# Checked and still REJECTED after the third source (fallback Standard
# stands, no override written; numbers also stay null — see check-lineup.py
# output):
#   - Coral (5M, 5BR): all three sources only have "Coral Pink" (#66) —
#     never bare "Coral" (posca.com's scrape name). Per the R1 conservative
#     rule (name-or-hex-paired matches only), a name mismatch doesn't
#     verify the number even with three-way hex agreement.
#   - Grape Green (5M), Yellow Fluo (5M), Pale Fluorescent Orange (8K):
#     absent from mpuni.co.jp entirely (no Fluorescent-series page exists
#     on the JP site) and from second-source.html.
#   - Glacier Blue (1MR): absent from mpuni.co.jp (JP pastels are only
#     P2/P4/P6/P11) — still single-source (second-source.html P33).
#   - 3M "Brown" 2nd occurrence (hex #572d2d): mpuni's PC-3M page lists
#     only one Brown (茶 = PC3M.21, no ダークブラウン/Dark Brown entry) —
#     doesn't satisfy "a saved source explicitly lists the 3M range with
#     both entries identified." Only Jenny's does; stays single-source.
#
# Round 5 (2026-07-24, Task N5) added a NEW sanctioned identity rule: a
# name-variant color may be accepted when TWO independent saved sources
# both show the color, in the SAME size range, with a hex IDENTICAL
# (case-insensitive, no near-misses) to the posca.com scrape hex for that
# entry. Re-examined all 7 remaining nulls against this rule plus new
# sources (scripts/second-source.pdf — turned out to be the same PoscART
# chart as second-source.html, not independent; scripts/
# source-mpuni-posca-index.html — confirms mpuni.co.jp's JP catalogue has
# no PC-5BR/PCF-350/PC-1MR pages at all, only pc_1m/pc_3m/pc_5m/pc_8k/
# pc_17k, so no further JP data exists for the 5BR/1MR-only colors;
# scripts/source-cultpens-pc5m.html — a real UK retailer page, confirms
# the name variants "Coral Pink", "Green Grape" and "Fluorescent Yellow"
# but carries zero per-color hex or number codes anywhere on the page).
# None of the 7 clear the identity rule's hex bar:
#   - Glacier Blue (1MR, #69caf8): second-source.html's Glacier Blue P33
#     IS an exact hex match — but it's the only independent source (the
#     .pdf duplicate of the same PoscART chart doesn't count as a second
#     one, and Jenny's explicitly says she never got hex data for it).
#     One matching source, not two -> stays null.
#   - Coral (5M/5BR, #ff8da1): second-source "Coral Pink" #FA9D8F and
#     Jenny's "Coral Pink" #FF8CA1 are both close but not IDENTICAL to
#     #ff8da1 (near-miss, explicitly excluded by the rule). mpuni.co.jp's
#     PC-5M page does give a size-matched number for the name variant
#     (PC5M.66 = コーラルピンク/Coral Pink) but carries no hex at all, so it
#     can't supply the hex-identity half of the rule either.
#   - Grape Green (5M, #cace58): no saved or newly-found source lists this
#     entry under ANY name (bare or variant) with a hex at all.
#   - Yellow Fluo (5M, #ffff2e): second-source's "Fluorescent Yellow" F2 is
#     #FEFF2E — one byte off #ffff2e, so a near-miss, not identical.
#   - Pale Fluorescent Orange (8K, #ffff2e — same hex posca.com gives
#     Yellow Fluo/5M, apparently a posca.com-side scrape quirk, not ours to
#     fix): no source lists this name or a matching hex in the 8K range.
#   - 3M Brown 2nd occurrence (#572d2d): unchanged from Round 3 — still
#     single-source (Jenny's Dark Brown 22, exact hex match); second-
#     source's Dark Brown 22 stays a hex mismatch (#4c2c30); mpuni's PC-3M
#     page still lists only one Brown.
# All 7 stay null; listed in the report for a physical-cap check.
CATEGORY_OVERRIDES = {
    'glacier blue': 'Pastel',
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
    for hexv, raw_name in scrape[slug]['colors']:
        name = normalize_name(raw_name)
        # posca.com lists some names twice within a size (e.g. Brown in PC-3M);
        # keys stay unique via a deterministic ordinal suffix in scrape order.
        seen[name] = seen.get(name, 0) + 1
        key = f'{size}:{name}' if seen[name] == 1 else f'{size}:{name}-{seen[name]}'
        hexl = hexv.lower()
        if seen[name] == 1:
            num = numbers.get(name.lower())
        else:
            # Second+ occurrence of a duplicated name: only verified when a
            # source explicitly pairs THIS hex to a number, via a
            # scripts/number-map.json 'name@hex' key. No such key currently
            # exists: the PC-3M second "Brown" (hex #572d2d) is still
            # unverified. Jenny's source has "Dark Brown" 22 at this exact
            # hex, but second-source.html's "Dark Brown" 22 is a hex
            # mismatch (#4c2c30) and mpuni.co.jp's PC-3M page lists only one
            # Brown — so only one independent source supports the pairing.
            # The mechanism stays in place, unused, until a second source
            # confirms it. Otherwise stays name-verbatim, number null.
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

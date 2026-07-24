# Posca-Only Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `~/Projects/markers` as a Posca-only marker inventory: static page, official lineup data, gap overview per pen size, viewable in-store on a phone.

**Architecture:** Three runtime files (`index.html`, `lineup.js`, `inventory.js`) with zero dependencies and no build step. Dev-only tooling lives in `scripts/` (Python via `uv`, plus data snapshots). Deployed as-is on GitHub Pages.

**Tech Stack:** Vanilla HTML/CSS/JS. Python 3 via `uv run` for data generation/verification. `playwright-cli` skill for browser verification.

**Spec:** `docs/superpowers/specs/2026-07-23-posca-rebuild-design.md` — read it before starting any task.

## Global Constraints

- Runtime = exactly `index.html`, `lineup.js`, `inventory.js`. No frameworks, no CDN, no build step.
- Color names and hex values come 1:1 from posca.com (snapshot in `scripts/posca-scrape.json`). Never adjust a hex or name.
- Color numbers: only verified numbers go in `lineup.js`; unverifiable numbers are `null`, never guessed.
- MOP'R PCM-22 is excluded. Copic is removed entirely.
- Code, comments, commit messages: English. UI copy: Dutch. No em-dashes, no ALL-CAPS ornament in UI copy (acronyms like PC-5M are fine).
- Python: `uv run --no-project` only (no pip/venv).
- Browser checks: `playwright-cli` skill only.
- **Design-skill gate (explicit user requirement):** Task 4 must load `frontend-design:frontend-design` AND `ui-ux-pro-max` via the Skill tool BEFORE writing UI code, and the task report must name which guidelines were applied where. Task 7 must load `impeccable` and `design-taste-frontend` the same way. Loading without demonstrably applying them counts as task failure.
- The visual design (typography, spacing, exact styling) is deliberately NOT pre-specified in this plan: it must be produced under the loaded design skills in Task 4/7 within the structural constraints below. This is intentional, not a placeholder.
- Work directly on `main` (solo repo, no worktree needed).

## Data formats (used by every task)

`lineup.js`:

```js
// Generated from scripts/posca-scrape.json + scripts/number-map.json. Do not hand-edit colors.
const LINEUP = [
  {
    size: '5M',                 // key used by inventory
    label: 'PC-5M',
    tip: 'medium 1.8-2.5 mm',
    colors: [
      // name/hex verbatim from posca.com; number null when unverified.
      // key = 'SIZE:Name'; when posca.com lists the same name twice within a
      // size (real case: Brown 2x in PC-3M), later duplicates get a
      // deterministic ordinal suffix in scrape order: '3M:Brown', '3M:Brown-2'.
      { key: '5M:Blue', name: 'Blue', number: '33', hex: '#0072ce', category: 'Standard' },
      // ...
    ]
  },
  // sizes in this order: 1MR, 1MC, 3M, 5M, 5BR, 7M, 8K, 17K, F350
];
```

`inventory.js`:

```js
// Owned markers as lineup.js color keys ("SIZE:Color Name", duplicate names
// carry an ordinal suffix like "3M:Brown-2").
// Updated by tapping in the page (copy button) or via Claude Code.
const INVENTORY = [];
```

Categories: `Standard`, `Pastel`, `Fluo`, `Metallic`, `Glitter`. Derived from the verified number prefix (`P`→Pastel, `F`→Fluo, `M`→Metallic, `G`/glitter name→Glitter, else Standard); when number is null, fall back to name prefix (`Glitter *`, `Metallic *`, `Fluorescent *`, else Standard).

---

### Task 1: Preserve data sources in scripts/

**Files:**
- Create: `scripts/posca-scrape.json` (copy from scratchpad `/private/tmp/claude-501/-Users-philipgedrojc/a355b346-15e7-4c13-af31-0fe3183bc25d/scratchpad/posca-scrape.json`; if missing, re-scrape posca.com product pages the same way: color name + hex per range page `<section id="colors">`)
- Create: `scripts/legacy-map.json` (number→name pairs extracted from the current `index.html` `POSCA_COLORS` array)
- Test: `scripts/check-sources.py`

**Interfaces:**
- Produces: `posca-scrape.json` — `{ "<page-slug>": { "declared_count": "42", "found": 42, "colors": [["#hex","Name"], ...] } }` with page slugs `pc-1mr, pc1-mc, pc-3m, pc-5m, pc-5br, pc-7m, pc-8k, pc-17k, pcf-350` (plus `mopr-pcm-22`, ignored downstream)
- Produces: `legacy-map.json` — `[{ "category": "Standard", "number": "33", "name": "Blue", "hex": "#025094" }, ...]` (68 entries from the old page; verified count)

- [ ] **Step 1: Copy the scrape snapshot into the repo**

```bash
cp "/private/tmp/claude-501/-Users-philipgedrojc/a355b346-15e7-4c13-af31-0fe3183bc25d/scratchpad/posca-scrape.json" ~/Projects/markers/scripts/posca-scrape.json
```

- [ ] **Step 2: Extract the legacy number map from the current index.html**

```bash
cd ~/Projects/markers && uv run --no-project python - <<'EOF'
import re, json
html = open('index.html', encoding='utf-8').read()
block = re.search(r'const POSCA_COLORS = \[(.*?)\];', html, re.S).group(1)
rows = re.findall(r"\['([^']+)','([^']+)','([^']+)','([^']+)'\]", block)
data = [{'category': c, 'number': n, 'name': nm, 'hex': h} for c, n, nm, h in rows]
json.dump(data, open('scripts/legacy-map.json', 'w'), indent=1)
print(len(data), 'legacy entries')
EOF
```

Expected: `73 legacy entries`

- [ ] **Step 3: Write the source check**

```python
# scripts/check-sources.py — run: uv run --no-project python scripts/check-sources.py
import json
scrape = json.load(open('scripts/posca-scrape.json'))
legacy = json.load(open('scripts/legacy-map.json'))
EXPECTED = {'pc-1mr': 21, 'pc1-mc': 25, 'pc-3m': 42, 'pc-5m': 50, 'pc-5br': 16,
            'pc-7m': 15, 'pc-8k': 33, 'pc-17k': 10, 'pcf-350': 10}
for slug, n in EXPECTED.items():
    found = scrape[slug]['found']
    assert found == n, f'{slug}: {found} != {n}'
    assert int(scrape[slug]['declared_count']) == n, f'{slug}: declared mismatch'
assert len(legacy) >= 70, f'legacy map too small: {len(legacy)}'
assert all(set(e) == {'category', 'number', 'name', 'hex'} for e in legacy)
print('sources OK')
```

- [ ] **Step 4: Run it**

Run: `cd ~/Projects/markers && uv run --no-project python scripts/check-sources.py`
Expected: `sources OK`

- [ ] **Step 5: Commit**

```bash
git add scripts/ && git commit -m "chore: snapshot posca.com scrape and legacy number map"
```

### Task 2: Number mapping and lineup.js generation

**Files:**
- Create: `scripts/number-map.json`
- Create: `scripts/build-lineup.py`
- Create: `lineup.js`
- Test: `scripts/check-lineup.py`

**Interfaces:**
- Consumes: `scripts/posca-scrape.json`, `scripts/legacy-map.json` (Task 1)
- Produces: `lineup.js` defining global `const LINEUP` in the exact format from "Data formats" above; `scripts/number-map.json` — `{ "<color name lowercase>": "<number>" }`

**Number verification procedure (the anti-guess rule):**
1. Seed candidates from `legacy-map.json` (name → number).
2. Fetch one independent retailer/manufacturer color chart that lists Posca cap numbers with names (try in order until one works: `https://www.cultpens.com/pages/posca-colour-chart`, `https://www.jacksonsart.com/blog/2021/04/16/posca-paint-markers-colour-chart/`, a uni-ball regional site found via `mcp__gemini-grounding__search_with_grounding` for "posca colour chart cap numbers"). Save the raw page under `scripts/` for traceability.
3. A number is **verified** when legacy and the second source agree, or when the second source states it explicitly and legacy has no entry.
4. Names present on posca.com but in neither source → `number: null`. Print every null so the report can list them.
5. When a size lists the same name twice (Brown in PC-3M), name-based lookup cannot tell the entries apart: only the first occurrence gets the mapped number; later duplicates get `number: null` unless a source explicitly disambiguates them by hex or by listing two numbered entries.

- [ ] **Step 1: Build number-map.json following the procedure above** (manual research step; store result as JSON, lowercase-name keys)

- [ ] **Step 2: Write the failing lineup check**

```python
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
```

- [ ] **Step 3: Run it to verify it fails** (no `lineup.js` yet)

Run: `cd ~/Projects/markers && uv run --no-project python scripts/check-lineup.py`
Expected: FAIL with FileNotFoundError

- [ ] **Step 4: Write scripts/build-lineup.py**

```python
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

def category(name, number):
    if number:
        pfx = number[0]
        if pfx == 'P': return 'Pastel'
        if pfx == 'F': return 'Fluo'
        if pfx == 'M': return 'Metallic'
        if pfx == 'G': return 'Glitter'
        return 'Standard'
    for p, c in (('Glitter', 'Glitter'), ('Metallic', 'Metallic'), ('Fluorescent', 'Fluo')):
        if name.startswith(p): return c
    return 'Standard'

lineup = []
for slug, size, label, tip in SIZES:
    colors, seen = [], {}
    for hexv, name in scrape[slug]['colors']:
        # posca.com lists some names twice within a size (e.g. Brown in PC-3M);
        # keys stay unique via a deterministic ordinal suffix in scrape order.
        seen[name] = seen.get(name, 0) + 1
        key = f'{size}:{name}' if seen[name] == 1 else f'{size}:{name}-{seen[name]}'
        num = numbers.get(name.lower())
        colors.append({'key': key, 'name': name, 'number': num, 'hex': hexv.lower(),
                       'category': category(name, num)})
    lineup.append({'size': size, 'label': label, 'tip': tip, 'colors': colors})

body = json.dumps(lineup, indent=1)
open('lineup.js', 'w').write(
    '// Generated by scripts/build-lineup.py from scripts/posca-scrape.json'
    ' + scripts/number-map.json. Do not hand-edit colors.\n'
    f'const LINEUP = {body};\n')
print('lineup.js written')
```

- [ ] **Step 5: Generate and verify**

Run: `uv run --no-project python scripts/build-lineup.py && uv run --no-project python scripts/check-lineup.py`
Expected: `lineup.js written`, then `lineup OK · N unverified numbers: [...]` — record the N unverified names for the final report.

- [ ] **Step 6: Commit**

```bash
git add scripts/ lineup.js && git commit -m "feat: official Posca lineup data with verified color numbers"
```

### Task 3: Empty inventory

**Files:**
- Create: `inventory.js`

**Interfaces:**
- Produces: global `const INVENTORY` (array of `"SIZE:Color Name"` strings), consumed by Task 4/6.

- [ ] **Step 1: Write inventory.js** (exact content from "Data formats" section, including the comment)

- [ ] **Step 2: Commit**

```bash
git add inventory.js && git commit -m "feat: empty inventory (fresh Posca-only start)"
```

### Task 4: Page rebuild under design skills

**Files:**
- Modify: `index.html` (full replacement of the old Copic/Posca page)

**Interfaces:**
- Consumes: `LINEUP` (Task 2), `INVENTORY` (Task 3) via `<script src="lineup.js">` and `<script src="inventory.js">`
- Produces: DOM contract for Tasks 6-7: each swatch element carries `data-key` equal to its lineup.js color `key` and class `owned` or `missing`; each size section has `id="size-<SIZE>"` and a counter element with class `size-count`; `<body data-mode="kleur|nummer|naam">` reflects the label mode.

- [ ] **Step 1: Load the design skills (MANDATORY, before any code)**

Invoke via Skill tool: `frontend-design:frontend-design`, then `ui-ux-pro-max`. Follow their process; the final report must cite which of their guidelines shaped which decision (typography, spacing, color handling, mobile ergonomics). Skipping or only nominally loading them = task failure.

- [ ] **Step 2: Build the page structure** (design under the loaded skills; structure is fixed)

Fixed structural requirements from the spec:
- Phone-first, light, single vertical page; Dutch UI copy.
- Sticky top bar: size jump buttons (1MR … F350) + label-mode toggle with states kleur / nummer / naam (persisted in localStorage; default kleur).
- Per size: section with `id="size-<SIZE>"`, header `PC-5M` + tip + counter `12 van 50` (count = owned in that size).
- Within a size: category subgroups in order Standard, Pastel, Fluo, Metallic, Glitter (only when non-empty), each spectrum-sorted with this exact function:

```js
function spectrumKey(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255,
        g = parseInt(hex.slice(3, 5), 16) / 255,
        b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2;
  const s = max === min ? 0 : (max - min) / (1 - Math.abs(2 * l - 1));
  let h = 0;
  if (max !== min) {
    if (max === r) h = ((g - b) / (max - min) + 6) % 6;
    else if (max === g) h = (b - r) / (max - min) + 2;
    else h = (r - g) / (max - min) + 4;
    h /= 6;
  }
  return s < 0.12 ? l : 1 + h;  // greys/browns first by lightness, then hue
}
```

- Owned = solid swatch; missing = faded with dashed border (exact treatment per the design skills, but the two states must be distinguishable at arm's length on a phone).
- Label modes: kleur = swatch only (densest grid); nummer = number under each swatch (`?` styling for null numbers must make "unknown" visually distinct from a real number); naam = name under each swatch, wider grid. CSS-only truncation if a name overflows (`text-overflow: ellipsis`), full name in `title`/`data-full`.
- Render verbatim: names/numbers exactly as in `lineup.js`, no case changes, no trimming beyond whitespace collapse.

- [ ] **Step 3: Verify in browser**

Use the `playwright-cli` skill: open `file://` or a local `python -m http.server` URL, assert all 9 sections render, `document.querySelectorAll('[data-key]').length === 222`, and screenshot at 390x844 (iPhone-ish) for the report.

- [ ] **Step 4: Commit**

```bash
git add index.html && git commit -m "feat: rebuild page as Posca-only inventory (design-skill pass)"
```

### Task 5: Repo hygiene after the wipe

**Files:**
- Modify: none beyond verification (old page content replaced in Task 4)

- [ ] **Step 1: Verify Copic is gone**

Run: `grep -ci copic ~/Projects/markers/index.html || echo "copic gone"`
Expected: `copic gone` (zero matches)

- [ ] **Step 2: Update repo description**

```bash
gh repo edit DanutaBloom/markers --description "Posca marker inventory: official lineup, gap overview per pen size, static HTML"
```

- [ ] **Step 3: Commit any leftovers, if files changed**

### Task 6: Ownership toggling and the two update routes

**Files:**
- Modify: `index.html`

**Interfaces:**
- Consumes: DOM contract from Task 4 (`data-key`, `owned`/`missing`, `.size-count`)
- Produces: localStorage key `posca-inventory-local` (JSON: `{ "added": [keys], "removed": [keys] }` relative to committed `INVENTORY`), a "kopieer inventory.js" button, and a dirty indicator element visible when `added.length + removed.length > 0`.

- [ ] **Step 1: Implement tap-to-toggle with localStorage overlay**

```js
const LS_KEY = 'posca-inventory-local';
function loadOverlay() {
  try { return JSON.parse(localStorage.getItem(LS_KEY)) || { added: [], removed: [] }; }
  catch { return { added: [], removed: [] }; }
}
function effectiveOwned() {
  const o = loadOverlay();
  const set = new Set(INVENTORY);
  o.added.forEach(k => set.add(k));
  o.removed.forEach(k => set.delete(k));
  return set;
}
function toggleKey(key) {
  const o = loadOverlay();
  const committed = INVENTORY.includes(key);
  const owned = effectiveOwned().has(key);
  if (owned) {                       // -> not owned
    o.added = o.added.filter(k => k !== key);
    if (committed && !o.removed.includes(key)) o.removed.push(key);
  } else {                           // -> owned
    o.removed = o.removed.filter(k => k !== key);
    if (!committed && !o.added.includes(key)) o.added.push(key);
  }
  localStorage.setItem(LS_KEY, JSON.stringify(o));
  render();                          // re-renders swatch states, counters, dirty indicator
}
```

- [ ] **Step 2: Implement the copy button**

Generates the full new `inventory.js` content (same header comment, keys sorted by size order then name) from `effectiveOwned()` and writes it to the clipboard via `navigator.clipboard.writeText`, with a visible "gekopieerd" confirmation. After committing the pasted file, the overlay is stale; on load, drop overlay entries already reflected in `INVENTORY` (added key present, or removed key absent) so the dirty indicator clears itself after a successful commit.

- [ ] **Step 3: Verify with playwright-cli**

Assert: tapping a swatch flips its class and the section counter; reload keeps the state (localStorage); the dirty indicator appears; the copy button produces text containing `const INVENTORY = [` and the toggled key (read the generated string via page evaluation instead of the OS clipboard).

- [ ] **Step 4: Commit**

```bash
git add index.html && git commit -m "feat: tap-to-toggle ownership with localStorage overlay and copy-out"
```

### Task 7: Design polish pass

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Load the polish skills (MANDATORY)**

Invoke via Skill tool: `impeccable`, then `design-taste-frontend`. Run their review approach against the real page (not a copy), on phone viewport. Fix what they surface; the report names each applied guideline. No new features: polish only (spacing, hierarchy, tap targets, contrast of the missing-state, sticky-bar behavior while scrolling).

- [ ] **Step 2: Re-run the Task 4 + Task 6 playwright-cli checks** (nothing may regress)

- [ ] **Step 3: Commit**

```bash
git add index.html && git commit -m "style: design polish pass (impeccable + design-taste review)"
```

### Task 8: Deploy and verify live

**Files:** none (git push only)

- [ ] **Step 1: Push**

Run: `cd ~/Projects/markers && git push origin main`

- [ ] **Step 2: Verify GitHub Pages serves the new page**

Run (Pages can lag; retry up to ~5 min): `curl -sL https://danutabloom.github.io/markers/ | grep -c "PC-5M"`
Expected: non-zero. Also: `curl -sL https://danutabloom.github.io/markers/lineup.js | head -1` shows the generated header comment.

- [ ] **Step 3: Final report to Philip**

Must include: live URL, the list of colors with unverified (`null`) numbers, which design-skill guidelines were applied in Tasks 4 and 7, and how to use both update routes.

---

## Round 2 (user feedback 2026-07-23)

Decisions: legacy-map is NOT a verification source (it partly derives from PoscART — circular); hex source stays posca.com (single consistent origin, complete coverage); color names are display-normalized to consistent Title Case in the data layer (explicit user request; e.g. "CACAO BROWN" → "Cacao Brown", "YELLOW FLUO" → "Yellow Fluo"); progress-fill bar removed; UI copy English; label toggle must not reshape the grid; dark mode added (system preference + persisted manual override).

### Task R1: Independent number re-verification + name normalization

**Files:** Modify `scripts/build-lineup.py`, `scripts/number-map.json`, regenerate `lineup.js`; save two independent source snapshots under `scripts/` (replacing trust in legacy-map.json and the PoscART-derived pair for verification; keep old snapshots for history). Update `scripts/check-lineup.py` only if the null-count assertion text needs it.
- A number is verified only when TWO sources independent of each other and of the old page agree (official uni-ball/Posca retail pages, retailer colour charts). Disagreement or single-source → null. No guessing; provenance of every accepted number listed in the report.
- Duplicate-name entries (Brown 2x in 3M): may only be renamed/numbered if a source explicitly pairs the specific entry (by number+name listing for that size). Otherwise stays name-verbatim with number null.
- Name normalization: Title Case applied in build-lineup.py with a documented function; keys follow normalized names (inventory is empty, no migration).
- check-sources.py: drop the legacy-map assertions' role as verification (file stays as historical snapshot).

### Task R2: UI round — English, stable toggle, dark mode, remove progress bar

**Files:** Modify `index.html` only.
- All UI copy English ("Posca inventory", "Copy inventory.js", "unsaved changes", "Colour/Number/Name" or "Color/Number/Name" — pick one spelling consistently: use US English "Color").
- Label modes share identical grid geometry: same column count/cell size in all three modes; label area is fixed-height reserved space (empty in color mode), nothing reflows on toggle.
- Dark mode: CSS custom properties per theme; default follows prefers-color-scheme; small persisted manual override (localStorage), swatch perception protected (neutral surfaces, borders re-tuned for dark).
- Remove `.size-fill` progress bar (element + CSS).
- MANDATORY skill gate as in Task 4: load frontend-design:frontend-design AND ui-ux-pro-max via Skill tool before code; report names applied guidelines.
- Verify with playwright-cli: mode toggle causes zero layout shift (compare a swatch's boundingClientRect across all three modes), dark/light both render, regression set from Tasks 4/6 passes.

### Task R3: Polish + deploy

- Polish pass on the real page with impeccable + design-taste-frontend (both themes, 390x844), regression re-run, commit.
- Push; verify live (index + lineup.js + inventory.js 200, spot-check dark mode markup present).

---

## Round 3 (user feedback 2026-07-24)

### Task N1: Third source for Black/White (and other nulls where possible)
Find and save a THIRD independent source (independent of PoscART, Jenny's Crayon Collection, and the old page) listing Posca cap numbers. Rule unchanged: a number is verified when two independent saved sources agree. With three sources, any agreeing pair counts; a 2-vs-1 split resolves to the majority pair, documented. Apply to all currently-null names (Black, White, Coral, Grape Green, Yellow Fluo, Pale Fluorescent Orange, the 3M Brown duplicate, Glacier Blue's number). Regenerate lineup.js via build-lineup.py; checks stay green; provenance in report.

### Task N2: Control redesign for consistency
User feedback: (a) label modes are still either/or — "why not both"; Color mode shows nothing extra, then Number OR Name. Redesign: swatch always; Number and Name become independently toggleable (both on = number + name visible). Grid geometry stays constant in ALL combinations (reserve label space accordingly). (b) Theme switcher in the footer feels odd — relocate sensibly (header area or another consistent place), keep Auto/Light/Dark semantics + persistence. (c) "Copy inventory.js" button copy is jargon — rename to plain language describing the action; confirmation copy consistent. Overall: one coherent control language (same component style for all controls).
Mandatory: load `impeccable`, `ui-ux-pro-max` AND `frontend-design:frontend-design` via Skill tool before code; use sequential-thinking MCP for the control-model reasoning and Context7 for any web-platform API doubt; verify with playwright-cli (regression set + zero layout shift across ALL label combinations + theme matrix). Only index.html changes; DOM contract: data-key/owned/missing/size-<SIZE>/.size-count stay; body[data-mode] may become two data attributes (update all references + localStorage migration incl. round-2 values).

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, dependency-free page listing the full official Posca marker range per pen size,
showing which markers Philip owns and where the gaps are. Primary use: phone in a store.
Deployed as-is by GitHub Pages at https://danutabloom.github.io/markers/ (repo
`DanutaBloom/markers`, work happens directly on `main`).

Design decisions and their reasoning live in `docs/superpowers/specs/`; the task-by-task
build history is in `docs/superpowers/plans/2026-07-23-posca-rebuild.md`. Read the specs
before changing data rules or the control model — they record user decisions, not defaults.

## Commands

```bash
# Regenerate lineup.js from the saved sources (must stay reproducible: a rebuild
# on a clean tree leaves git status clean)
uv run --no-project python scripts/build-lineup.py

# Data assertions: shape, unique keys, per-size color counts, hex/number formats
uv run --no-project python scripts/check-lineup.py

# Source-snapshot assertions: scrape counts match the declared counts per range
uv run --no-project python scripts/check-sources.py

# Local preview (clipboard copy needs http(s) or file://, not a remote origin)
python3 -m http.server 8000   # then http://localhost:8000/
```

There is no build step, no package manager, no test runner. The two `check-*.py` scripts
are the whole test suite — run both after touching anything under `scripts/` or `lineup.js`.
Browser verification goes through the `playwright-cli` skill.

## Runtime architecture

Exactly three files ship: `index.html`, `lineup.js`, `inventory.js`. No frameworks, no CDN,
no modules — `index.html` loads the two data files as plain globals (`LINEUP`, `INVENTORY`)
and renders everything in one inline script. Keep it that way.

- **`lineup.js`** — generated reference data, the official range. Never hand-edit colors.
  Shape: `[{size, label, tip, colors: [{key, name, number, hex, category}]}]`, 9 sizes,
  key = `"SIZE:Color Name"` with an ordinal suffix (`3M:Brown-2`) when a size lists the
  same name twice.
- **`inventory.js`** — a flat array of those keys, the only file that changes on a purchase.
- **`index.html`** — UI plus all state handling.

### Ownership is committed data plus a local overlay

`INVENTORY` is the committed truth. Tapping a swatch does not edit it; it writes an
`{added, removed}` overlay into `localStorage["posca-inventory-local"]`. `effectiveOwned()`
merges the two, the copy button emits a full regenerated `inventory.js` for pasting and
committing, and a dot on that button signals uncommitted local changes.
`cleanStaleOverlay()` drops overlay entries that the committed inventory already reflects
or whose key no longer exists in `LINEUP` — a data rename without that cleanup leaves an
orphaned tick and a permanently stuck dirty dot.

The second update route is Claude Code: Philip says what he bought, you edit `inventory.js`
directly (keys must exist in `LINEUP`), commit, push.

Every user-facing setting survives a reload, each under its own localStorage key, each
falling back to a safe default when the stored value is missing or unreadable:
`posca-labels` (independent Number/Name booleans, with a one-time migration from the
round-1/2 `posca-label-mode` value), `posca-theme` (auto/light/dark, applied pre-paint by a
head script), and `posca-own-filter` (all/owned/missing). The filter was deliberately
session-only in the 2026-07-23 spec; Philip reversed that on 2026-08-12, so the spec text
on that point is superseded by the code. Keep new settings on the same pattern.

### How a swatch encodes ownership

Owned is a chip filled with the pigment; missing is the same cell hollow, with a 5px ring
in that same pigment and the page color inside. Both states therefore render the exact
posca.com hex. Two rules protect this and are easy to break by accident:

- Never tint, mix, fade, or overlay the pigment to signal state. The 2026-07-23 design did
  (a wash mixed toward a neutral), which made a missing Yellow `#ffd100` paint as `#aa8f11`.
  The page is used in a store against physical caps, so a wrong hue is a real defect.
- Ownership must survive a pigment that equals the page surface. Fill versus hollow cannot
  carry White in light mode or Black in dark mode, so `tone()` tags each chip pale, mid or
  deep by luminance and the CSS puts a small ink dot on owned chips of the extreme tone for
  the current theme only. Any new state encoding needs an equivalent fallback.

One grid per size, sorted by `CATEGORY_ORDER` then by `spectrumKey`, with no per-category
headings; the number prefix (P, F, M, G) names the series when labels are on. The page head
holds the title and the at-home actions and scrolls away; the sticky bar is two rows. Its
measured height and the `--bar-h` token (currently 101px measured, 108px token) must stay in
step, since `scroll-margin-top` on the size sections depends on it.

### DOM contract

Verification scripts and later tasks rely on these staying stable: `data-key` on each
swatch, the `owned`/`missing` classes, `id="size-<SIZE>"` sections, `.size-count`.
Rendering is a full `render()` rebuild of `#app` — every state change re-renders.

## Data rules (the part that is easy to get wrong)

- Color names and hex values come 1:1 from `scripts/posca-scrape.json` (posca.com snapshot).
  Never adjust a hex or "improve" a name in `lineup.js`.
- Color numbers (cap codes like `33`, `P2`) are not on posca.com. A number enters
  `scripts/number-map.json` only when two sources independent of each other and of
  `legacy-map.json` agree, or from Philip reading a physical cap. Unverifiable stays `null`
  and renders as `?` — never guess one. Three are currently null by design (1MR Glacier
  Blue, 5M Grape Green, 8K Pale Fluorescent Orange).
- Corrections that deviate from the scrape live as explicit tables in `build-lineup.py`
  (`CATEGORY_OVERRIDES`, `HEX_NAME_CORRECTIONS` keyed by name+hex, `EXTRA_COLORS` for
  colors the scrape misses), each with its provenance in a comment. Add to those tables
  with the same evidence note; do not special-case inside the loop.
- Category derives from the number prefix (`P`/`F`/`M`/`G`), with name-based fallback only
  when the number is null.
- Changing per-size color counts means updating the assertions in `check-lineup.py` in the
  same commit.
- MOP'R PCM-22 is out of scope (no published color list). Copic was removed entirely.

## Conventions

Code, comments, commits: English. UI copy: English in the page as it stands. Commits follow
`feat(scope): ...` / `fix(scope): ...`. Python through `uv run --no-project` only.

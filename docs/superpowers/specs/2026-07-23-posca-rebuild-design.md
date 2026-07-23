# Posca inventory rebuild — design

Date: 2026-07-23
Status: approved by Philip (brainstorm session)

## Goal

Rebuild the markers page as a Posca-only inventory. Primary use case: standing in a
store with the phone, seeing at a glance which markers are owned and where the gaps
are, per pen size. Copic is dropped entirely (Copic has its own app). Existing
ownership state is wiped; the new inventory starts empty.

## Non-goals

- No search function (overview-driven, not lookup-driven)
- No backend, no build step, no framework
- No editing sync from the phone in-store (viewing only; updates happen at home)
- No Copic data or brand switching

## Files

| File | Role |
|------|------|
| `index.html` | The UI. Static, no dependencies, no build step. |
| `lineup.js` | The official Posca range (read-only reference data). |
| `inventory.js` | Philip's owned markers. The only file that changes on purchases. |

Rationale for the split: ownership commits never touch lineup data and vice versa.

## Lineup data

Source: posca.com per-range product pages (scraped 2026-07-23, verified counts):

| Range | Tip | Colors |
|-------|-----|--------|
| PC-1MR | extra fine 0.7 mm | 21 |
| PC-1MC | fine conical 0.7-1 mm | 25 |
| PC-3M | fine 0.9-1.3 mm | 42 (includes 8 glitter; no separate 3ML range) |
| PC-5M | medium 1.8-2.5 mm | 50 |
| PC-5BR | brush | 16 |
| PC-7M | broad 4.5-5.5 mm | 15 |
| PC-8K | chisel 8 mm | 33 |
| PC-17K | extra broad 15 mm | 10 |
| PCF-350 | brush | 10 |

MOP'R PCM-22 is excluded: posca.com publishes no color list for it.

Per color: name, number, hex, category (Standard / Pastel / Fluo / Metallic /
Glitter). Names and hexes come 1:1 from posca.com — no local "improvements".
Color numbers (the cap codes like 33, P2) are not on posca.com; they are mapped
from a second source and verified per color. A color whose number cannot be
verified gets an explicit unknown marker in the data — never a guessed number.

## UI

Single vertical page, phone-first, light theme.

- One section per pen size with an owned counter ("PC-5M · 12 van 50").
- Within a section: subgroups per category (Standard, Pastel, Fluo, Metallic,
  Glitter where applicable), each sorted as a color spectrum (greys/browns
  ordered by lightness first).
- Owned = solid color swatch; not owned = faded swatch with dashed border.
- Sticky top bar: size buttons that jump to their section + a display-mode
  toggle with three states: kleur (swatch only, densest grid), nummer, naam.
  Number/name modes widen the grid slightly to fit labels.
- Swatch colors are rendered exactly as the posca.com hex values.

## Updating ownership

Two routes, both ending in a commit to `inventory.js`:

1. In the page: tapping a swatch toggles owned state, stored in localStorage as
   a local overlay. A "kopieer inventory.js" button puts the merged, updated
   file content on the clipboard for committing. The page shows an indicator
   when uncommitted local changes exist, so the two routes cannot silently
   overwrite each other.
2. Via Claude Code: Philip says what he bought; Claude edits `inventory.js`,
   commits and pushes.

## Deployment

GitHub Pages serves the repo as-is; after the rebuild
https://danutabloom.github.io/markers/ shows the new page. Repo description
updated to Posca-only.

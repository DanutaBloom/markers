# Lineup gaps, filter scroll anchor, owned check badge

Date: 2026-07-24 · Status: approved by owner (chat)

Three issues found while entering the physical collection on the live page.

## 1. PC-3M colors missing from lineup.js

The posca.com scrape (`scripts/posca-scrape.json`) is incomplete for PC-3M.
Confirmed gaps:

| Color | Number | Hex (from PC-5M) | Source |
|-------|--------|------------------|--------|
| Aqua Green | P6 | #71dbd4 | physical cap (owner, 2026-07-24) |
| Coral Pink | 66 | #ff8da1 | physical cap (owner, 2026-07-24) |
| Orange | 4 | #ff5c39 | both saved sources list it for PC-3M (Jenny's Crayon Collection, mpuni.co.jp) |

Design: an `EXTRA_COLORS` dict in `scripts/build-lineup.py` — per size key, a
list of `(name, hex)` appended after the scraped colors, each entry with a
source comment. Numbers resolve through `number-map.json` like every other
color; `lineup.js` stays generated-only. Future gaps the owner encounters are
added the same way.

## 2. Ownership filter resets scroll

`setOwnFilter()` re-renders the whole grid; when the filtered content is
shorter the browser clamps scroll to the top. Design: before the re-render,
remember the id of the topmost visible `section.size` (first section whose
bottom edge sits below the sticky bar, `--bar-h`); after `render()`, jump back
to it with `scrollIntoView({behavior: "instant"})` (sections already carry
`scroll-margin-top: var(--bar-h)`). Skipped when `scrollY` is 0. Applies only
to filter switches — tapping a swatch keeps its current behavior.

## 3. Owned vs missing too subtle

The washed chip + thin dashed border reads poorly during entry, especially for
light pigments. Design (owner picked from three options): a small check badge
on owned chips — a paper-colored disc (~14px, top-right inside the chip) with
an ink check glyph, hairline edge via `--chip-edge` so it holds on any
pigment. Missing state stays as is. CSS only: `.sw.owned .chip::after`.

## Testing

playwright-cli against the local page: three new 3M swatches present with
correct numbers, filter switch keeps the viewed section in place, check badge
visible on owned chips in light and dark.

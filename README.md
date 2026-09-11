# The Russell Periodic Chart, 1926 — free web edition

This repository publishes the periodic chart and the ten-octave element table from
Walter Russell's *The Universal One* (Brieger Press, New York, 1926), with every
claim in them scored against modern chemistry. The 1926 edition is in the public
domain. The community that reads it has worked from low-resolution photographs of
the chart for years, and the 1926 engraving crowded its inner labels beyond
legibility even in a perfect scan. This edition fixes both problems and states its
method for each step.

## Read it

**Web:** https://charts.walterrussellarchive.org — the chart in a viewer, the full
table, the scoreboard, and the methods page.

## What is here

- `docs/` — the generated website. It is build output. Edit the data and the
  Markdown, then run `python3 tools/build_site.py`. Pillow is the only dependency,
  and only for the page images.
- `docs/assets/facsimile.png` — the restored 1926 plate at full scan resolution
  (2712 × 3264). Restoration used deterministic image operations only: background
  flattening, one global threshold, and despeckling. No pixel was invented, and no
  model drew anything.
- `charts/russell_periodic.svg` — a measured redraw of the same plate. The ring
  and spiral geometry was measured from the scan; the labels come from the
  transcribed table. It is resolution-independent, so it stays legible at any size.
- `data/russell_1926_elements.json` — the printed table as data: 10 octaves,
  137 rows, 959 cells. Names, tone numbers, sigils, symbols, atomic masses, and
  melting points, with the printed typography of each name recorded.
- `data/scoreboard.json` — 23 scored entries covering all 46 testable claims found
  in the book, each with its 1926 evidence and its modern sources.
- `verification/methods.md` — how every image and every cell was produced, with the
  transcription counts, the disagreement counts, and the commands to re-derive each
  artifact.
- `verification/checksums.tsv` — SHA256 of every published artifact.

## The evidence chain

Every verdict is checkable inside this repository:

    scoreboard → data/scoreboard.json (1926 evidence + modern sources)
               → data/russell_1926_elements.json (the transcribed table)
               → docs/assets/facsimile.png (the printed page)
               → Library of Congress item 27004508 (the scan)

## How the table was transcribed

Machine reading of the chart itself recovers only part of the inner ring labels
with confidence, so the chart is not the data source. The book's own
`TABLE OF THE TEN OCTAVES OF THE VARYING STATES OF MOTION` prints every position,
name, number, and symbol in body type, and that table is the source.

No cell entered the dataset on one reading. Two independent passes transcribed
every cell, and four further readers re-derived the whole table afterwards. Of
959 table cells, 956 agreed on the first pass and 3 needed adjudication, all of
them spacing conventions. Nothing remains uncertain. The disagreement counts and
the adjudication rules are published in `verification/methods.md`, not summarized
away.

## The scoreboard

The scoreboard scores claims, never people. Of the 23 entries: 17 are refuted,
1 is partially confirmed, 1 is unfalsifiable, 1 is a terminology match only, 1 is
a claim the book never made, and 2 are confirmed. Both confirmations are
period-standard: the 1926 table marks gaps that the chemistry of 1926 already
predicted, so the novelty axis records them as standard, not as foresight.

One result runs the other way. Modern retellings credit the book with predicting
deuterium and tritium. The words do not appear in it. Russell's sub-hydrogen gases
were *lighter* than hydrogen, which is the opposite of a heavy isotope. The
scoreboard records that claim as never made, with the search evidence in
`verification/deuterium_negative.md`.

## Provenance

Every published image derives from one source: the Library of Congress
digitization of the 1926 edition, item 27004508
(https://www.loc.gov/item/27004508/), 290 page images. The Library states of that
collection: "The books in this collection are in the public domain and are free to
use and reuse." Credit Line: Library of Congress.

`verification/image_provenance.tsv` lists every published image with its source
URL, its operation chain, and the SHA256 of both source and output.

## What this edition is not

This edition does not argue that the 1926 book anticipated modern chemistry, and
it does not mock the book for failing to. The plates and the table are published
whole, so a reader can check every verdict against the source and reach a
different one. Errors of fact get corrected promptly and visibly.

This is an independent archive project. It has no affiliation with the University
of Science and Philosophy, with the Walter Russell estate, or with any successor
organization. The name of the author and the title of the book identify the
subject of study only.

## License

Original work in this repository — the prose, the scoreboard verdicts, the
redrawn chart, the selection and arrangement of the dataset, and the build tools —
is licensed CC BY-NC 4.0. The 1926 facsimile plates are in the public domain and
no copyright is claimed over them. See [LICENSE.md](LICENSE.md).

Copyright holders with concerns may open an issue in this repository.

## Part of the archive

This edition is one project of the Walter Russell Archive
(https://walterrussellarchive.org), which publishes primary sources for Walter
Russell's scientific claims with their provenance stated. Corrections:
contact@walterrussellarchive.org

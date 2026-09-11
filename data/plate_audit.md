# Plate completeness audit — *The Universal One* (Brieger Press, c1926)

Prepared 2026-09-11. This audit compares the book's own list of charts against two copies: the
Library of Congress copy and a private USP 1974 reprint scan. It reports what each copy contains
and where each chart sits in it. It supports `data/loc_page_map.tsv`, which cites it.

Working files stay in `data/pagemap_work/`, which is private working staging and is not
published. The USP reprint scan and the thumbnails made from it are private working staging as
well; no page of that scan is published, and no pixel of it may reach a publication asset.

Sources:

- LoC item `gdc.27004508`, 290 IIIF page images,
  `https://tile.loc.gov/image-services/iiif/public:gdc:27004508:NNNN/full/full/0/default.jpg`
  (per-page `info.json` retrieved for all 290 indices, 2026-09-11; dimensions in
  `data/pagemap_work/loc_info_dims.tsv`). Local mirror of the same scan (private working
  staging, not published): `source_scans/loc/loc_1926_27004508.pdf` (290 pages, verified
  identical page count; page N of the PDF = IIIF index N).
- USP 1974 reprint scan (private working staging, not published):
  `source_scans/the-universal-one-by-walter-russell/The Universal One by Walter Russell_text.pdf`
  (284 PDF pages, OCR text layer; thumbnails `source_scans/thumbs/p-001.png … p-283.png`).

Conventions: "p. N" = printed folio / position in the book's pagination;
"LoC N" = IIIF image index (1–290); "USP N" = PDF page of the USP scan.

---

## 1. The book's own chart list (Contents, LoC 14–15)

The Contents (LoC 14 = Contents p. 1, LoC 15 = "CONTENTS—(Continued)") lists charts
per chapter with page numbers. Transcribed from the LoC scan (vision-verified at 2×
magnification; OCR in `data/pagemap_work/ocr/pg-013.txt`, `pg-014.txt`):

**Book I** (9 chart pages)

| Chapter | Contents entry | Page(s) |
|---|---|---|
| II The Life Principle | Chart | 5 |
| III Mind, the One Universal Substance | Charts | 9, 11, 13 |
| V The Process of Thinking | Charts | 17, 19 |
| XV The Formula of the Locked Potentials | Chart | 39 |
| XVI Universal One-ness | Chart | 41 |
| XIX Omniscience | Chart | **Opposite 58** |

**Book II** (50 chart pages)

| Chapter | Page(s) |
|---|---|
| IV Positive and Negative Electricity | 83 |
| V The Elements of Matter | 87 |
| VI The Ten Octave Cycle | 89, 91, 93, 95, 97, 99, 101 |
| VII Instability… | 103, 105 |
| VIII The Universal Pulse | 107, 109, 111 |
| IX Concerning Energy | 113 |
| X Electro-Magnetic Pressures | 125 |
| XI Attraction and Repulsion | 139 |
| XIII Universal Direction | 151, 153, 155, 157 |
| XIV Universal Mathematics | 159, 161, 163, 165 |
| XV Charging Poles / Discharging Bases | 167, 169, 171, 173, 175, 177, 179 |
| XVI The Wave | 181, 183 |
| XVII Time | 189 |
| XVIII Temperature | 197, 199 |
| XX Universal Mechanics | 209, 211, 213 |
| XXI Rotation | 219, 221, 223, 225, 227, 229 |
| XXII Revolution | 233, 235 |
| XXV Ionization | 241, 243 |

Chapters with **no** chart line: Book I ch. I, IV, VI–XIV, XVII, XVIII; Book II
ch. I–III, XII, XIX, XXIII, XXIV, XXVI–XXVIII.

Total promised: **59 chart pages** (58 numbered + 1 unpaginated "Opposite 58" plate).
The frontispiece (Russell Periodic Chart) is **not** listed in the Contents.

Every numbered chart page is an odd (recto) folio. Chart pages carry no printed
folio; their position in the pagination is unambiguous because the flanking text
pages carry printed folios (see §3 method).

## 2. Reconciliation against the LoC copy — **LoC copy complete**

Pagination rule established from folio OCR (207/265 body pages read directly, the
rest bracketed by both neighbors): body pages run LoC 19 → p. 1 … LoC 76 → p. 58
(offset 18), the unpaginated plate leaf is LoC 77–78, then LoC 79 → p. 59 …
LoC 283 → p. 263 (offset 20). No other discontinuity exists anywhere in 1–290.

- All 58 numbered chart pages are present at exactly LoC = page + 18 (pages ≤ 58)
  or page + 20 (pages ≥ 59), each verified as a full-page chart/table by OCR of its
  caption and/or vision reading (montages in `data/pagemap_work/`). Flagged
  `plate/figure` in `data/loc_page_map.tsv`.
- The "Opposite 58" plate is LoC 77 (recto: "THERE IS BUT ONE DYNAMIC FORCE",
  caption "THE ONE FORCE OF THE UNIVERSE IS THE ENERGY OF THINKING MIND…") with
  LoC 78 its verso (boxed text "The creating universe of matter appears…"). It sits
  between p. 58 (LoC 76) and p. 59 (LoC 79), i.e. facing p. 58 as promised.
- Frontispiece: LoC 16 = the Russell Periodic Chart (headline "PERIODICITY IS AN
  ABSOLUTE CHARACTERISTIC OF ALL PHENOMENA OF NATURE"), between the Contents
  (LoC 14–15) and the John i:1 epigraph (LoC 17).

**Verdict: the LoC copy is complete.** 59/59 Contents-listed chart pages present
and in their listed positions, plus the unlisted frontispiece. 290 images account
for: covers (LoC 1, 290), endpapers (2–3, 288–289), blank flyleaves (4–6, 284–287),
front matter (7–18), and the full pagination 1–263 with the one tipped-in leaf.

Notes on identity quirks (not gaps):

- The Ch. II "Chart" at p. 5 (LoC 23) is a reproduction of **Mendeléef's 1904
  periodic table** ("THIS IMPROPERLY ARRANGED AND INCOMPLETE…" caption); classed
  `plate/figure` in the TSV since the Contents calls it a Chart.
- P. 235 (LoC 255) is captioned "CRYSTALLIZATION CHART No. 1" but the Contents
  lists it under Ch. XXII (Revolution); Ch. XXIII (Crystallization) has no chart
  line. [INFERENCE] a Contents attribution slip in the original.
- The octave **tables** (headline "TABLE OF THE TEN OCTAVES…") occupy even pages
  92, 94, 96, 98, 100 (LoC 112–120 even) — these are in-pagination tables with
  printed folios, distinct from the seven odd-page octave charts 89–101, and are
  classed `table` in the TSV.
- Two Conclusion-area pages carry sizeable in-text diagrams not in the chart list:
  p. 253 (LoC 273, boxed "appears from the One / disappears into the One") and
  p. 254 (LoC 274, spiral "THE MYSTERY OF GRAVITATION & RADIATION"). Classed
  `text` with notes.

## 3. Reconciliation against the USP 1974 scan

Method: word-set similarity matching of every LoC body page's OCR text against all
284 USP PDF pages' text layer (`pdftotext -layout`), plus vision reading of USP
thumbnails at the anomalies (`data/pagemap_work/mont_usp_anom.png`). Matching is
decisive: text pages match at 0.87–1.00 similarity with runner-ups ≤ 0.43.

USP structure: USP 1–15 = 1974 front matter (incl. 4-page 1974 Preface, which
states the book "was originally published in 1927"; the copyright page itself
prints "Copyright 1926"), USP 15 = frontispiece Periodic Chart, USP 16 = p. 1,
USP 280–284 = 1974 back matter (University of Science and Philosophy promotional
pages, book list, blank).

Full correspondence (each segment verified at both ends):

| USP PDF pages | Book pages | offset |
|---|---|---|
| 16–27 | 1–12 | 15 |
| 28–54 | 14–40 | 14 |
| 55 | 41 (chart) | — |
| **56** | **13 (chart — out of place)** | — |
| 57–73 | 42–58 | 15 |
| 74–75 | unpaginated "Opposite 58" plate leaf | — |
| 76–102 | 59–85 | 17 |
| **103** | **101 (chart — out of place)** | — |
| 104–118 | 86–100 | 18 |
| 119–223 | 102–206 | 17 |
| — | **207 MISSING** | — |
| 224–279 | 208–263 | 16 |

Page-count arithmetic closes exactly: 12+27+1+1+17+2+27+1+15+105+56 = 264 content
sides = 265 sides in the 1926 book (263 numbered + 2 plate-leaf sides) minus 1.

Findings:

1. **USP scan lacks book page 207** (a text page, Ch. XX running head "UNIVERSAL
   MECHANICS—ROTATION—REVOLUTION…"; LoC 227). Evidence: USP 223 ends with printed
   folio "206", USP 224 ends with printed folio "208"; no USP page matches LoC 227's
   text (best similarity 0.42 vs ≥ 0.87 for every matched text page). Since 207/208
   are two sides of one leaf and 208 is present, [INFERENCE] a page was skipped
   during scanning, not torn out. **No plate is missing from the USP scan** — the
   gap is a text page.
2. **Two charts sit at non-Contents positions in the USP scan:** the p. 13 chart
   ("THE OCTAVES ARE NOT SEMI-CIRCULAR…") appears at USP 56, after the p. 41 chart;
   the p. 101 plate ("EVOLUTION OF FORCE INTO TONES…", the four astronomical
   photographs) appears at USP 103, between pp. 85 and 86. Both verified by exact
   caption text in the USP text layer and by thumbnail inspection. [INFERENCE]
   either the 1974 reprint repositioned these plates or the scanned copy had them
   bound/inserted there; the scan itself cannot distinguish.
3. All 59 Contents-listed chart pages **and** the frontispiece are present in the
   USP scan (frontispiece at USP 15; plate leaf at USP 74–75).
4. Known anchor confirmed: USP 110 = book p. 92 = first TABLE OF THE TEN OCTAVES
   page (similarity 0.96; folio 92 read by strip OCR on LoC 112).

## 4. Spot checks (10 random body pages, LoC ↔ folio ↔ USP)

Sample drawn with `random.seed(42)` from body pages with > 400 OCR words.
"sim" = shared-word similarity (intersection / smaller set); folio source
`strip-OCR` = printed folio read by tesseract from the bottom strip of the page.

| LoC | folio | folio source | USP page | sim | first-line match (LoC = USP) |
|---|---|---|---|---|---|
| 025 | 7 | strip-OCR = 7 | 22 | 0.87 | "MIND, THE ONE UNIVERSAL SUBSTANCE" |
| 050 | 32 | strip-OCR = 32 | 46 | 0.97 | "The modern concept that solar energy is" |
| 052 | 34 | strip-OCR = 34 | 48 | 0.97 | "tion in that appearance which man calls space" |
| 062 | 44 | strip-OCR = 44 | 59 | 1.00 | "Man can have dominion over his own body" |
| 087 | 67 | strip-OCR = 67 | 84 | 0.96 | "Electricity is the active, attractive force" (USP page prints folio 67) |
| 092 | 72 | strip-OCR = 72 | 89 | 0.98 | "the smaller stream would also have to be vastly" |
| 100 | 80 | arithmetic (strip OCR noise "0"); confirmed by USP match | 97 | 0.99 | "Electricity opposes magnetism in its desire" |
| 237 | 217 | strip-OCR = 217 | 233 | 0.96 | "…revolution and accelerated rotation end in non-…" (USP page prints folio 217) |
| 272 | 252 | strip-OCR = 252 | 268 | 0.99 | "born together but each travels a different direc-" |
| 275 | 255 | strip-OCR = 255 | 271 | 0.97 | "evade its materialization into the form" (New Laws and Principles, matches Contents "255") |

All 10 pass: printed folio agrees with the arithmetic map, and page text matches
the USP page predicted by the correspondence table in §3.

## 5. Reproducibility — exact commands

All operations are deterministic: crop, resize, level, OCR only. The commands run from the
program root. They read and write private working staging under `data/pagemap_work/` and
`source_scans/`, neither of which is published; they are recorded so the method can be checked
and repeated against the same scans.

```sh
# 1. Per-page IIIF dimensions (polite, sequential, ~3 req/s)
mkdir -p data/pagemap_work/infojson
for i in $(seq 1 290); do n=$(printf "%04d" $i);   # NB: seq without -w (avoid octal)
  curl -s --max-time 20 \
    "https://tile.loc.gov/image-services/iiif/public:gdc:27004508:$n/info.json" \
    -o data/pagemap_work/infojson/$n.json; sleep 0.3; done

# 2. Page images from the local mirror of the same LoC scan
#    (pg-NNN.jpg where NNN = LoC index - 1; identical to fetching
#    .../NNNN/full/full/0/default.jpg for each index)
pdfimages -j source_scans/loc/loc_1926_27004508.pdf data/pagemap_work/pg

# 3. Full-page OCR (classification + text matching)
mkdir -p data/pagemap_work/ocr
ls data/pagemap_work/pg-*.jpg | xargs -P 8 -I{} sh -c \
  'b=$(basename {} .jpg); tesseract {} data/pagemap_work/ocr/$b --psm 3'

# 4. Folio recovery: bottom strip (folios are printed bottom-center), 3x upscale
mkdir -p data/pagemap_work/strips data/pagemap_work/stripocr
ls data/pagemap_work/pg-*.jpg | xargs -P 8 -I{} sh -c \
  'b=$(basename {} .jpg); magick {} -gravity South -crop 60%x15%+0+40 +repage \
   -colorspace Gray -resize 300% -level 20%,80% data/pagemap_work/strips/$b.png && \
   tesseract data/pagemap_work/strips/$b.png data/pagemap_work/stripocr/$b --psm 6'
# second pass on failures: -crop 100%x12%+0+30, tesseract --psm 11

# 5. USP text layer for cross-checking
pdftotext -layout \
  "source_scans/the-universal-one-by-walter-russell/The Universal One by Walter Russell_text.pdf" \
  data/pagemap_work/usp_text.txt
```

Parsing/matching logic: folio = last bottom-strip line that is a bare 1–3 digit
number; classification from OCR word counts + caption keywords, vision-verified on
page montages in `data/pagemap_work/` (`mont_octaves.png`, `mont_ends.png`,
`mont_usp_anom.png`); USP matching = per-page sets of ≥4-letter lowercased words,
score = |A∩B| / min(|A|,|B|), accepted when ≥ 0.7 with a ≥ 0.15 margin over the
runner-up.

Retrieval date for all tile.loc.gov requests: 2026-09-11.

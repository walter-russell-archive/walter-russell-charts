# Claim inventory notes — companion to `data/claims.json`

Prepared 2026-09-11 (project item R16). This document records how every checkable claim in *The
Universal One* (1926) was found, located, and read on a native page image. It supports
`data/claims.json`.

Scope: every checkable claim in the book, in Russell's own words, with page citations. This
document sets no verdicts. The verdict vocabulary and the scoring rules are in
`data/verdict_taxonomy.md` (project item R18). The deuterium and tritium question is settled
separately in `verification/deuterium_negative.md` (project item R17) and is **not** re-derived
here; its dual-witnessed quotes are reused (C008, C030, C037 note provenance).

## 1. Method

Witnesses — the same three used in `verification/deuterium_negative.md` (project item R17):

- **W1 finding** — LoC OCR fulltext `source_scans/loc/loc_fulltext.txt` (continuous, no page breaks). Used to *find* passages. The fulltext is private working staging and is not published.
- **W2 locating** — USP 1974 scan text layer `data/deuterium_negative/usp_text.txt` (283 form-feed pages), private working staging and not published. Used as second OCR witness and to bracket page positions. **Witness-independence caveat (project item R5):** the 1974 plates are photographic reproductions of the 1926 plates; W1/W2 give *scan-level* independence only (independent imaging/OCR of one 1926 printing), which suffices for what-the-book-printed, and nothing more is claimed.
- **W3 verifying** — native-resolution LoC IIIF page images (`tile.loc.gov/image-services/iiif/public:gdc:27004508:NNNN/full/full/0/default.jpg`). **Every quote in claims.json was read on a native page image** (log in §2). New downloads in `data/claims_work/loc_pages/` (27 pages); deterministic PIL crops for table/glyph checks in `data/claims_work/crops/`; pre-existing native images reused (`source_scans/loc/full/p0112.jpg`, `data/deuterium_negative/loc_0111/0113/0114/0120_full.jpg`). `data/claims_work/` and `data/deuterium_negative/` are private working staging and are not published; of the images named here, only the `source_scans/loc/full/` page image is published with the edition.

Page numbers: printed folio read **on the page image itself** wherever a folio is printed; cross-checked against `data/loc_page_map.tsv`. Plate pages carry no folio and are cited as `[N]` (position by pagination sequence, per the page map). The USP↔LoC page offset **drifts** (+3 in front matter and most prose, +2 in the octave-table region LoC 0109–0120), so USP page numbers were used only as a bracketing witness, never as the citation; the folio on the LoC image is authoritative.

OCR line-wrap hyphens silently joined in `quote_verbatim`; nothing else altered. Where the native image contradicts both OCR layers, the image wins (e.g. "3½" in C007). Empty printed table cells are recorded as *empty* ("" / "blank"), never omitted (C017, C019, C024, C027, C028).

## 2. Verification log (quote → native image witness)

Paths in the "LoC image (native)" column are relative to `data/claims_work/` unless a full path
is given. `data/claims_work/` and `data/deuterium_negative/` are private working staging and are
not published; the `source_scans/loc/full/` image named in the table is published with the
edition.

| Claim | Printed page | LoC image (native) | How verified |
|---|---|---|---|
| C001, C002 | Prelude leaf 3 | `loc_pages/loc_0013_full.jpg` | full-page vision read (first tried 0011, 0012 — quotes not there; Prelude spans LoC 0011–0013) |
| C003–C005 | 4 | `loc_pages/loc_0022_full.jpg` | full-page read; folio 4 confirmed |
| C006, C007 | [5] | `loc_pages/loc_0023_full.jpg` | caption read; fraction glyph resolved as **3½** (both OCR layers wrong: "31/4"/"31") |
| C008 | 6 | `loc_pages/loc_0024_full.jpg` | full-page read; folio 6 (also R17 §4) |
| C009 | [9] | `loc_pages/loc_0027_full.jpg` | plate caption read; plate title "CHART TRACING SOURCE OF MAN'S SUPPOSEDLY MANY SUBSTANCES BACK TO THE ONE" |
| C010, C011 | 36 | `loc_pages/loc_0054_full.jpg` | full-page read; folio 36 (first tried 0055 — the 140-elements sentence is on p.36, column layout misled the OCR-stream folio bracketing) |
| C012, +7000-lines quote in §5 | 37 | `loc_pages/loc_0055_full.jpg` | full-page read; folio 37 |
| C013, C014 | [89] | `loc_pages/loc_0109_full.jpg` + crop `crops/p89_lum_block.png` | plate read + zoom on the 403− block for punctuation |
| C015, C016 | [91] | `data/deuterium_negative/loc_0111_full.jpg` | plate read (legend + annotation box + bottom caption) |
| C017 | 92 | `source_scans/loc/full/p0112.jpg` | full-page read: title, subtitle "Beginning of the Cyclic Inhalation at Tomion.", blank mass/melting columns for all 24 rows, folio 92 (also read in project items R2 and R17) |
| C018 | [93] | `data/deuterium_negative/loc_0113_full.jpg` | credo box read line-by-line; plate caption "SEVENTH AND EIGHTH OCTAVE CONSTANTS…" |
| C019, C020 | 94 | `data/deuterium_negative/loc_0114_full.jpg` | native-resolution row transcription reused from `verification/deuterium_negative.md` §5.4 (project item R17); octave 5–6 names screened via W2 (no further invented names) |
| C021 | 96 | crop `crops/p96_footnote.png` (from `loc_pages/loc_0116_full.jpg`) | footnote + folio 96; starred Te/I values seen in table |
| C024 (803D+ part) | 96 | crop `crops/p96_mate_row.png` | "Mate to 3D—" row at 803D+ between Molybdenum and Ruthenium, cells blank |
| C022, C023 | [97] | `loc_pages/loc_0117_full.jpg` | caption (186,400) + header box read; plate ladder spells TOMION |
| C024 (ninth octave), C025 | 98 | crops `crops/p98_table.png`, `p98_table2.png`, `p98_note.png` (from `loc_0118_full.jpg`) | six "Mate to …" rows enumerated; note + folio 98 |
| C026 | [99] | crop `crops/p99_caption.png` (from `loc_0119_full.jpg`) | caption read; "hydrogene" spelling confirmed |
| C027, C028 | 100 | crops `crops/p100_table_top.png`, `p100_table_mid.png` (from `data/deuterium_negative/loc_0120_full.jpg`) | row-by-row transcription of the tenth-octave table, both sides |
| C029–C032 | 100 | crop `crops/p100_prose.png` + native read from `verification/deuterium_negative.md` §5.5 (project item R17) | prose paragraphs read verbatim |
| C033 | [107] | `loc_pages/loc_0127_full.jpg` | note read; Explanatory Chart No. 1 |
| C034 | 124 | `loc_pages/loc_0144_full.jpg` | full-page read; folio 124 |
| C035 | 188 | `loc_pages/loc_0208_full.jpg` | full-page read; folio 188; "(1004‡)" glyph compared against "(1003+)" on same page |
| C036 | 200–201 | `loc_pages/loc_0220_full.jpg` + `loc_0221_full.jpg` | sentence straddles the page break; both halves read, folios 200/201 |
| C037, C038 | 203 | `loc_pages/loc_0223_full.jpg` | full-page read; folio 203; quoted-vs-unquoted "unseen" distinguished |
| C039–C041 | 204 | `loc_pages/loc_0224_full.jpg` | full-page read; folio 204 |
| C042 | 205 | `loc_pages/loc_0225_full.jpg` | full-page read; folio 205 |
| C043 | 206 | `loc_pages/loc_0226_full.jpg` | full-page read; folio 206 |
| C044, C045 | 246 | `loc_pages/loc_0266_full.jpg` | full-page read; folio 246 |
| C046 | 247 | `loc_pages/loc_0267_full.jpg` | full-page read; folio 247 |

Also fetched but not needed for final citations: `loc_0011`, `loc_0012` (Prelude leaves 1–2), `loc_0116` (full), `loc_0118` (full), `loc_0119` (full), `loc_0145`, `loc_0146`, `loc_0219` (candidate pages ruled out during page pinning).

## 3. The invented / undiscovered elements — count and list

**40 novel element names are printed** (counted, not assumed; sources: octave tables pp.92, 94, 100 and plates [89]/[91]/[97], all native-verified):

- Octave 1 (p.92): Alphanon 100=, Irenon 101+, Vijaon 102+, Marvaon 103+, TOMION 104‡, Alberton 103−, Blackton 102−, Boston 101− — **8**
- Octave 2 (p.92): Betanon 200=, Jamearnon 201+, Erneston 202+, Eykaon 203+, ATHENON 204‡, Barnardon 203−, Delphanon 202−, Romanon 201− — **8**
- Octave 3 (p.92): Gammanon 300=, Marconium 301+, Penrynium 302+, Vinton 303+, QUENTIN 304‡, Tracion 303−, Buzzeon 302−, Helenon 301− — **8**
- Octave 4 (p.94): Hydron 400=, Ethlogen 402+, Bebegen 403+, CARBOGEN 404‡, Luminon 403−, Halanon 402−, Helionon 401− — **7**
- Octave 10 (p.100): Uridium 1003D+, Urium 1003E+, TOMIUM 104‡, Whitnion 103E−, Alphonson 103D−, Georgeon 103C−, Victoron 103B−, Lipton 103A−, Omeganon 100= — **9**

Distinct *entities*: **38**, because the text itself identifies Tomium ≡ Tomion ("1004‡ equals 104‡", C023; the [97] plate ladder even spells TOMION) and Omeganon ≡ Alphanon ("Omeganon … the end, which is Alphanon, the beginning", C028). The octave-10 table's Alberton/Blackton/Boston rows repeat octave-1 names (overlap rows, not new elements). Octaves 5–9 print **no** invented names — only real elements plus unnamed placeholders.

**Unnamed predicted slots (8)** — placeholder rows printed "Mate to …" with every data cell empty: 803D+ (p.96); 903D+, 903M−, 903L−, 903I−, 903E−, 901− (p.98); 1001+ (p.100), the last also asserted in prose as "the unknown element (1001+) preceding radium" (p.246, C044).

Not counted as invented: **Niton** (period name for radon), **Uranium XII** (read as the period radioelement designation Uranium X II / UX₂; printed "Uranium XII", symbol "UrXII", 1003B+, cells empty — the reading is flagged for the verdict pass, project item R18), starred-but-real elements on the charts.

## 4. Post-uranium names — question answered

The post-uranium names "Uridium/Urium" are **CONFIRMED, with exact printings**: after Uranium (1003C+, Ur, 238.2, 1850) the tenth-octave table (p.100, LoC 0120) prints **Uridium, 1003D+, symbol Um** and **Urium, 1003E+, symbol Uu**, both with atomic-mass and melting-point cells empty. Verified at native resolution (crop `p100_table_top.png`); both OCR witnesses agree. The frontispiece chart (p0016) and the [97] plate also carry URIDIUM/URIUM in their tone ladders.

## 5. Dropped candidates (searched, not included) — with the search performed

1. **"They are the seven tones of an octave … granite rock …" repeat near p.86** — W2 hit on USP chunk 104 ("seven tones of an octave", "granite rock"); W1 places a similar credo at lines 10103–10109 between folios 85 and 88; location ambiguous between p.86 (LoC 0106) and plate [87] (LoC 0107), and the identical text is already captured verbatim at plate [9] (C009) and p.36 (C010). Dropped as duplicate; no image fetched for 0106/0107.
2. **"Tone means sound. Mass accumulates all down the entire ten octaves; tone lowers from …" (p.38 region, W1 lines 4394–4397)** — weaker duplicate of C046 and C018; located (folio bracket 38) but not image-verified. Dropped to avoid padding.
3. **Frontispiece chart marginal note "NOTE REGARDING MID-TONES … IN OCTAVES 7 AND 8 THERE ARE TEN MID-TONES, FIVE ON EITHER SIDE …" (W1 lines 1626–1640)** — on the Russell periodic chart (LoC 0016); OCR heavily garbled and the chart's transcription is covered by `data/chart_geometry.json`; the same content is captured from the p.96/98/100 table subtitles and the p.98 note (C025). Dropped here.
4. **"Emanations are radio-active light units expelled with such great force …" (W1 line 12727)** — plate caption, OCR badly garbled, no quantitative or element-naming content beyond C035; searched for a clean witness in W2 (found, garbled likewise); dropped as not concretely checkable.
5. **"In the mid-tones alone are there any irregularities in the orderliness of increase and decrease …" (W1 21308–21329, ~p.201)** — restates C025's irregularity point without new checkable content; dropped.
6. **"The inert gases of lower potentials integrate within the inert gases of higher potentials." (p.246, W1 25917)** — subsumed by C045 (same page, adjacent paragraph, verified image would be the same); dropped as near-duplicate.
7. **Duncan "THE NEW KNOWLEDGE" quotation on plate [5]** — a quotation *of Duncan*, not a Russell claim; excluded by design.
8. **"about a hundred" element photograph claim vs "seven thousand color lines"** — the seven-thousand-lines sentence was instead verified and folded into the record: "The spectrum has been divided and the elements assorted into about seven thousand color lines of light; but they are as meaningless to man as the Hebrew language is to the gentile." (p.37, LoC 0055, native-verified). It is contextual to C039–C041 rather than a separate claim; recorded here so it is not lost.

No candidate was dropped for *failing* image verification; every quote that reached verification was found on its page (two initial page-attribution misses — Prelude leaf and p.36/37 — were corrected by checking the adjacent leaf, see §2).

## 6. Marked uncertainties ([uncertain] inventory)

- **C009**: comma-vs-semicolon after "the seven tones of an octave" in the plate [9] caption (native image ambiguous; W1 reads ";").
- **C013**: hand-lettered comma after "helium" (~2 px; both OCR layers omit it); order of closing quote and period after "phosphorescence"; "fireflies" printed without apostrophe (certain).
- **C018**: stray period-like mark, "a.unit." on the scan; transcribed "a unit."
- **C026**: sign glyphs after "1" and "4" both render double-stroked; "1" vs "I" unresolvable at native resolution.
- **C027**: "Uranium XII" — printed text certain (both OCR + native image); *interpretation* as UX₂ is a reading, flagged for the verdict pass, project item R18.
- **C036**: minus-sign glyph form (hyphen/en-dash/minus) not distinguishable; values certain.
- Sigils preserved throughout: `=`, `+`, `−`, `‡`; small caps on 4-position rows (TOMION, ATHENON, QUENTIN, CARBOGEN, TOMIUM, LUTECIUM); italic on 0= rows (e.g. *Niton*); rotated margin labels ENDOTHERMAL INHALATION / EXOTHERMAL EXHALATION present on all table pages.

## 7. Cross-references for the verdict pass, project item R18 (facts only, no verdicts)

- Two different printed light-speed figures: 186,400 (C022, plate [97]) vs "exactly 186,330" (C035, p.188, three occurrences on the page).
- Tomium/Tomion spelling varies between the p.100 table and the [97] plate ladder; the text equates 1004‡ with 104‡ (C023).
- "Cold light" appears twice with different wording: "will be the chemical basis of the cold light of the future" (plate [89], C013) and "is the basis of the cold light of the future" (p.100, C032).
- The only novel atomic mass anywhere: Luminon *2.92 "*Approximate" (C020). Every other invented tone's mass/melting cell is printed empty.
- p.98 ninth-octave table shows a printed one-row misalignment between the NAME column and the SYMBOL/MASS columns (e.g. "Tantalum" on the 3K− line while "Ta 181.5" aligns with 3L−) — a typesetting defect of the 1926 printing, observed at native resolution; the full-cell treatment is recorded in the transcription log.

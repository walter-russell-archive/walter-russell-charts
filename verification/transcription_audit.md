# R12 — Dual-source verification audit of `data/russell_1926_elements.json`

Prepared 2026-09-11 (project item R12). This is the independent audit of the frozen transcription: four fresh blind
readers re-read the plates, and every cell was compared against the dataset. The auditor did not produce the
dataset. It supports `data/russell_1926_elements.json`, `data/disagreements.tsv` and `tools/audit_diff.py`.

The audit's own working files stay in `data/audit_work/`, `data/audit_crops/` and `data/elements_work/`, which are
private staging and are not published.

WITNESS INDEPENDENCE (per R5, quoted verbatim from the R11 record):

> WITNESS INDEPENDENCE (per R5): the 1974 USP plates are photographic reproductions of the 1926
> plates. The two witnesses therefore give SCAN-LEVEL independence only — independent imaging and
> independent readers of one 1926 printing. That establishes what the book printed; it is NOT
> edition-level independence and is never claimed as such.

The same applies to the chart plates: the USP chart pages are the same physical artwork as the
1926 plates; reading both scans is reading one source twice, imaged twice.

## Verdict up front

The frozen dataset survives a from-scratch, four-witness re-derivation intact.

| R12 count (published for the methods page) | n |
|---|---|
| row-cells total (137 rows × 7 fields) | **959** |
| agreed (fresh witnesses match dataset under the declared normalization) | **956** |
| resolved by adjudication at 4× (all dataset-correct; print sign-spacing only) | **3** |
| left uncertain | **0** |

Supplementary chart-witness column (137 row-cells, not part of the 959):

| chart-witness classification | n |
|---|---|
| agreed | 134 |
| adjudicated at 4× | 3 (2 dataset-correct, **1 dataset-error candidate**) |
| chart-illegible | 0 |

No glyph of any of the 959 table cells differs between the dataset and either fresh witness.

## ⚠ DATASET-ERROR CANDIDATE (report only — frozen input NOT modified)

**`o5.r3 (Beryllium)`, field `witnesses.chart`: dataset records `BERYLLIUM`; the plates print
`BERYLIUM` (single L).** Verified letter-by-letter at 4× in BOTH scans of the octave-5 wheel
(LoC 0111 / USP p.109 artwork, box at 502+), and both blind chart readers independently recorded
`BERYLIUM` on the frontispiece as well. Evidence:
`data/audit_crops/chart_o5r3_berylium_loc0111_4x.png`,
`data/audit_crops/chart_o5r3_berylium_usp109_4x.png`,
`data/audit_crops/chart_o5r3_berylium_loc0111_readercrop.png`.
The table cells for this row are unaffected (name prints `Beryllium` in both table witnesses,
agreeing with the dataset). Scope: one letter in one supplementary chart-witness string; none of
the 959 primary cells is implicated.

Amendment since this audit: the dataset's `witnesses.chart` value for this row was afterwards corrected to
`BERYLIUM`, logged under "Post-audit amendment" in `data/transcription_log_r11.md`. The audit's own ruling and the
counts above are unchanged.

## Protocol

Design: the auditor never re-read the plates itself for the primary passes; all four primary
readings were made by **fresh, blind readers in separate contexts** with an explicit forbidden-file list
(the dataset JSON/TSV, the R11 log, R11's pass files, R11's tesseract outputs and crops, the
claims files, `verification/`, and each other's pass files). Disclosure: the auditor's own record
necessarily included a summary of the R11 transcription work; the fresh-eyes property is therefore
enforced at the reader level, which is the stronger guarantee (the readers had no access to any
prior reading at any time). A first round of readings stopped on an API rate limit before
any output was written; those readings were discarded and the passes were re-run from scratch by
new blind readers, each writing its partial JSON to disk immediately after every page.

Pass order and readers (reader identity + full command list recorded in each file's `meta`):

1. **(a) LoC table** — `data/audit_work/pass_loc_table.json`; reader "vision (claude, subagent
   TranscriptAudit.LocTableRead2) + tesseract 5.5.2". Images: LoC IIIF natives 0112/0114/0116/
   0118/0120 (= printed 92/94/96/98/100). Vision on 1.5–5× LANCZOS crops
   (`data/audit_work/loc_table_crops/`), fresh tesseract runs (`data/audit_work/tess/loc_table_*`,
   `--psm 4` txt+tsv, `--psm 6` variants) as cross-check only.
2. **(b) USP table** — `data/audit_work/pass_usp_table.json`; reader "vision (claude, subagent
   TranscriptAudit.UspTableRead2) + tesseract 5.5.2". Images: `data/elements_work/usp/usp-110…118.png`
   (USP pdf pp.110–118 even, 2496×3488). Crops `data/audit_work/usp_table_crops/`,
   tesseract `data/audit_work/tess/usp_table_*`. Space-vs-tight sign judgments settled by measured
   ink-run gaps (≥13 px = space); dash-vs-minus by ink-run width (minus 33–36 px, dash ≈55 px).
3. **(c) LoC chart** — `data/audit_work/pass_loc_chart.json`; reader "vision (claude, subagent
   TranscriptAudit.LocChartRead) + tesseract 5.5.2". Plates 0016, 0103, 0107, 0109, 0111, 0113,
   0115, 0117, 0119, 0121. Wheel plates read exhaustively box-by-box; frontispiece 0016
   systematically by region (140 labels; dense micro-lettering beyond element boxes counted
   toward plate notes, not element labels). Tesseract run per plate for the record only
   (useless on rotated hand lettering, as expected).
4. **(d) USP chart** — `data/audit_work/pass_usp_chart.json`; reader "vision (claude, subagent
   TranscriptAudit.UspChartRead2) + tesseract 5.5.2". Plates `data/audit_work/usp_chart/usp015,
   101, 105, 107, 109, 111, 113, 115, 117, 119` extracted at native resolution
   (`pdfimages -f N -l N -png "source_scans/the-universal-one-by-walter-russell/The Universal One
   by Walter Russell.pdf" data/audit_work/usp_chart/uspNNN`). Frontispiece: 157 labels,
   8 illegible under overlapping display text.
5. **Diff** — `python3 tools/audit_diff.py` (auditor-written, in repo): loads the frozen dataset
   plus the four pass files plus `data/audit_work/adjudications.json`; classifies every cell;
   writes `data/audit_work/audit_cells.json` (all 959 table cells + 137 chart cells with class)
   and `data/disagreements.tsv`. Row locations for crops from fresh tesseract TSVs
   (`data/audit_work/adjud_tess/`, `--psm 4`).
6. **Adjudication** — every non-agreed cell re-examined by the auditor at 4× (LANCZOS) in BOTH
   scans; crops saved under `data/audit_crops/`; rulings in
   `data/audit_work/adjudications.json` (merged into the tsv by the diff script).

### Declared comparison normalization (N)

Agreement = equality after: NFC; outer whitespace strip; typographic→straight quotes (page
furniture only); internal whitespace removed in `position_col`/`number`/`symbol`/`atomic_mass`/
`melting_point_c` (the print sets a loose quad space before sigils — a documented typesetting
convention; the dataset canonical form is space-free and each row's `witnesses.loc/usp` strings
preserve the raw spacing); leading ASCII hyphen → U+2212 on numeric values; typography synonyms
folded; name internal whitespace collapsed to single space, case-sensitive. **Em dash (U+2014)
is never folded into minus — dash identity is data.** Symbol trailing periods, asterisks and
daggers are never normalized. Under N, 96 LoC-read cells and 86 USP-read cells differed from the
dataset only by this sign-spacing (glyph-identical); they are classified agreed and are exactly
the phenomenon R11 recorded as its 81 spacing-convention resolutions (the fresh readers marked
spaces slightly more often, e.g. `904 ‡`, matching their own ink-gap measurements).

## Disagreements and adjudications (all rows of `data/disagreements.tsv`)

Table cells (3 — all resolved **dataset-correct**, 0 uncertain):

| cell | dataset | LoC read | USP read | ruling |
|---|---|---|---|---|
| o8.r8 name | `Mate to 3D−` | `Mate to 3D −` | `Mate to 3D−` | print sets a thin/quad space before the sign inside the embedded code (cf. `803D +` on the same line); glyphs identical; spacing is typesetting, not data |
| o9.r8 name | `Mate to 3D−` | `Mate to 3D −` | `Mate to 3D−` | same |
| o10.r2 name | `Mate to 1−` | `Mate to 1 −` | `Mate to 1−` | same |

Chart-witness cells (3):

| cell | dataset | ruling |
|---|---|---|
| o4.r3 chart `ETHLOGEN` | **dataset-correct** | first glyph of the 402+ box on the first-four-octaves wheel is an anomalous hooked glyph in BOTH scans (LoC reader: damaged E; USP reader: Y). Frontispiece prints `ETHLOGEN` cleanly in both scans; table prints `Ethlogen` in both witnesses. Wheel glyph flagged as printing anomaly. |
| o4.r8 chart `HELIONON` | **dataset-correct** | LoC chart reader reported `HELONON` at 1.6×; auditor re-read the box at 4–5× in BOTH scans: `HELIONON` (cramped I between L and O). Reader low-zoom error, corrected. |
| o5.r3 chart `BERYLLIUM` | **dataset-error candidate** | see the loud section above. |

Crops for every non-agreed cell are in `data/audit_crops/` (paths in the tsv; both witnesses per
cell, semicolon-separated).

## Corroborations of R11's flagged anomalies (independent confirmation, both witnesses)

Both fresh table readers, blind to R11 and to each other, independently re-reported:
octave-6 margin misprint `ENDOTHERMAL EXHALATION`; the octave-9 exhalation-side symbol/mass/
melting one-line upward displacement with leader lines (transcribed row-wise, matching the
dataset's `layout_anomaly` transcription exactly, e.g. Ta 181.5 2900 on the `Mate to 3L+` line);
the octave-10 thousands-digit drop (`104‡`, `103E−`…`100=`, leading-plus `+103−/+102−/+101−`);
octave-7 `4E−…4A−` vs octave-8/9 `3E−…3A−` mid-tone lettering; the em-dash melting points
(Kr `—169`, Xe `—140`, Hg-row `—39`) re-confirmed by independent ink-run measurement in both
scans (≈49–55 px vs 33–36 px minus at each reader's scale); the full symbol-period inconsistency
pattern (o1 mixed, o2 all, o3 `Gn.` only, o5 `He.` only, o8 `Kr. Rb. Sr. Yt. Zr.` only, none in
o4/6/7/9/10); starred masses `*2.92`/`*127.5`/`*126.92` with their footnotes; `Disbrossium`
verbatim; `725` for the Phosphorus melting cell (no decimal point in either scan at ≥2.7×);
the p.92 master title with typographic quotes; all footnotes and trailing lines (the two
"Observe…" lines recorded by both readers as page trailing lines — placement category differs
from the dataset's per-octave footnote attachment; text identical). Copy-specific, not artwork:
USP handwritten `$ 750 000` (p.100 margin area), the rotated German stamp
`Hergestellt auf Kosten des Landes Steiermark` bleeding through USP right margins, catalogued
specks (near `At.`, after `Sa`) — consistent with R11's copy-noise adjudications.

## Chart witness notes (supplementary)

- UNKNOWN boxes: both chart passes found exactly the per-plate counts the dataset implies —
  1 (o7/8 wheel), 4 (o9 wheel), 1 (o10 wheel), 6 on the frontispiece. The two o9 rows with no
  chart box in the dataset (`Mate to 3L+`, `Mate to 3E+`) likewise have no box in either fresh
  pass. (The LoC reader's prose note said "two + three" UNKNOWNs on the o9 wheel; its structured
  label list, like the USP pass and the dataset, has four.)
- Chart-internal spelling variances between plates (artwork inconsistency, not dataset error —
  the dataset takes the wheel-plate spellings, which the fresh passes confirm): frontispiece
  `NICKEL` / `BLACKTON` / `MARGANESE` vs wheel `NICKLE` / `BLACTON` / `MANGANESE` — each
  frontispiece form verified in BOTH scans by the auditor (MARGANESE letter-by-letter:
  `data/audit_crops/chart_frontis_marganese_loc0016.png`,
  `chart_frontis_marganese_usp015_5x.png`); frontispiece 10th-octave axis label `TOMIUM`
  (vs wheel `TOMION`) attested in the LoC scan only — the corresponding USP radial was among the
  USP reader's 8 unresolved frontispiece labels; plate-0109 artwork `HELIONON` box vs
  plate-0111 annotation text "helionon"; `HELENINE` (301− box) confirmed in both scans on the
  first-four-octaves wheel.
- Diagram plates LoC 0103/0107 carry no element-name labels (both passes). The USP pdf pages at
  the −2 offset for those two (usp101) and for LoC 0121 (usp119) contain body text in the USP
  reader's identification, i.e. the 1974 pdf does not hold those plates at the uniform offset;
  irrelevant to the table audit (no element labels at stake) but recorded here.

## Reproducibility

Every step is re-runnable: reader commands are in each pass file's `meta.commands`; crop scripts
are retained (`data/audit_work/*_crops/crop.py`, `make_crops.py`); the classification is
`python3 tools/audit_diff.py` (deterministic; re-emits `data/audit_work/audit_cells.json` and
`data/disagreements.tsv` from the four pass files + `data/audit_work/adjudications.json`);
adjudication crops under `data/audit_crops/` name their source scan and zoom. USP-derived pixels
remain internal (all under `data/audit_work/` and `data/audit_crops/`; the USP scan is a
transcription witness only — no USP pixel may reach publication assets).

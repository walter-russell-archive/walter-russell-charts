# R17 — The deuterium/tritium negative in *The Universal One* (1926)

**Status: VERIFIED NEGATIVE** (both witnesses, term search + visual page confirmation).
Prepared 2026-09-11 (project item R17). This document tests one attributed prediction against the 1926 text and records the search terms, the two witnesses, and the pages read at native resolution. It supports scoreboard entry V001. Supporting images and extracted text stay in `data/deuterium_negative/`, which is private working staging and is not published.

## 1. Claim under test

Community folklore: Walter Russell "predicted deuterium and tritium" in *The Universal One* (1926).

Tested question, stated precisely: does the 1926 text contain (a) the words *deuterium*, *tritium*, *heavy hydrogen*, *isotope*, or any equivalent designation of a heavier variant of hydrogen, or (b) a description of any substance as a heavier form of hydrogen?

Answer on both counts: **no**. What the text does say about the tones adjacent to and below hydrogen is quoted in §5; the entities it places before hydrogen are described as *unseen* / *undiscovered*, their mass columns are left blank, and the one it characterizes explicitly (Hydron) is stated to be **"much lighter"** than hydrogen.

Historical context (not itself proof, but framing): the word absence is unsurprising — deuterium was discovered in 1931–32 (Urey, Brickwedde, Murphy, "A Hydrogen Isotope of Mass 2 and its Concentration," *Phys. Rev.* 40, 1–15 (1932), following the *Phys. Rev.* 39, 164 (1932) letter; https://doi.org/10.1103/PhysRev.40.1, retrieved 2026-09-11) and tritium in 1934 (Oliphant, Harteck, Rutherford, "Transmutation Effects Observed with Heavy Hydrogen," *Proc. R. Soc. A* 144, 692–703 (1934); https://royalsocietypublishing.org/rspa/article/144/853/692/3593/Transmutation-effects-observed-with-heavy-hydrogen, retrieved 2026-09-11). The folklore claim is therefore necessarily about the *substances*, not the words — so §5 examines what substances the 1926 text actually places near hydrogen, and what it says about their weights.

## 2. Corpora searched (two independent witnesses)

| Witness | Provenance | Local file | Size / checksum (md5) |
|---|---|---|---|
| **W1 — LoC OCR fulltext** | Library of Congress item `gdc.27004508`, *The Universal One*, Brieger Press, New York, c1926 (290 page images); canonical item page https://www.loc.gov/item/27004508/ (retrieved 2026-09-11 via tile.loc.gov; www.loc.gov serves a bot challenge). Continuous OCR, **no page breaks**. | `source_scans/loc/loc_fulltext.txt` | 760,326 B, `16fa5e74eb2d3d38f16101e126d0b363` |
| **W2 — USP 1974 scan text layer** | Private scan `source_scans/the-universal-one-by-walter-russell/The Universal One by Walter Russell_text.pdf` (OCR layer; 283 pages). **Private staging — verification use only; no pixel for publication.** | text extracted to `data/deuterium_negative/usp_text.txt` (283 form-feed page breaks) | source PDF md5 `3e518650bc5393ef5647caf96f4180af`; extracted text 786,425 B |
| **W3 — page images (visual)** | LoC IIIF: `https://tile.loc.gov/image-services/iiif/public:gdc:27004508:NNNN/full/full/0/default.jpg` (NNNN = 0001–0290), retrieved 2026-09-11, sequential low-rate fetches. Native-res copies of the confirmation pages saved to `data/deuterium_negative/loc_0111_full.jpg`, `loc_0113_full.jpg`, `loc_0114_full.jpg`, `loc_0120_full.jpg`; `source_scans/loc/full/p0112.jpg` pre-existing local mirror; low-res thumbs `source_scans/locthumbs/L-NNN.png`. | — | e.g. 0111: 2560×3208 grayscale JPEG |

Of the local files named in this table, one is published: `source_scans/loc/full/p0112.jpg`, alongside the two other Library of Congress page images that travel with the edition (`p0016.jpg`, `p0113.jpg`). The rest — `source_scans/loc/loc_fulltext.txt`, `source_scans/locthumbs/`, `data/deuterium_negative/`, and the USP 1974 scan directory — is private working staging and is not published. The USP scan is a transcription witness only; no pixel of it reaches a published asset. The independence the two witnesses give is scan-level only: the 1974 plates are photographic reproductions of the 1926 artwork (R5 finding), so reading both is reading one 1926 printing, imaged and read twice.

Text extraction command (W2):

```
pdftotext "source_scans/the-universal-one-by-walter-russell/The Universal One by Walter Russell_text.pdf" data/deuterium_negative/usp_text.txt
```

## 3. Term search — commands and hit table

Exact command run (case-insensitive substring counts; `grep -o` counts every occurrence, not lines):

```
for t in deuterium tritium "heavy hydrogen" isotope isotop deuter trit \
         "hydrogen 2" "hydrogen 3" "hydrogen-2" "hydrogen-3" "heavy water" protium; do
  a=$(grep -o -i -- "$t" source_scans/loc/loc_fulltext.txt | wc -l)
  b=$(grep -o -i -- "$t" data/deuterium_negative/usp_text.txt | wc -l)
  printf '%-16s LoC=%s USP=%s\n' "$t" "$a" "$b"
done
```

| Term (case-insensitive) | W1 LoC hits | W2 USP hits |
|---|---|---|
| deuterium | 0 | 0 |
| tritium | 0 | 0 |
| heavy hydrogen | 0 | 0 |
| isotope / isotop (stem) | 0 | 0 |
| deuter (stem, catches OCR-mangled endings) | 0 | 0 |
| trit (stem) | 0 | 0 |
| hydrogen 2 / hydrogen-2 | 0 | 0 |
| hydrogen 3 / hydrogen-3 | 0 | 0 |
| heavy water | 0 | 0 |
| protium | 0 | 0 |

OCR-corruption sweep for buried variants — every token containing `tium` or `deut`:

```
grep -o -i -E '[a-z]*tium[a-z]*|[a-z]*deut[a-z]*' source_scans/loc/loc_fulltext.txt data/deuterium_negative/usp_text.txt | sort | uniq -c
```

Result: every `tium` hit is **strontium** (incl. one line-break split "stron-/tium"); zero `deut` hits in either witness.

Positive controls (proves the OCR is not blind in the relevant vocabulary; same command form):

| Control term | W1 LoC | W2 USP |
|---|---|---|
| hydrogen | 55 | 54 |
| helium | 17 | 16 |
| carbon | 34 | 33 |
| octave | 323 | 319 |

Small W1/W2 count differences are ordinary OCR noise between two independent scans of two printings; no control term differs by more than 1.

## 4. Visual confirmation (an OCR zero is not proof by itself)

The passages where hydrogen-isotope language would have to appear — the octave tables and the sub-hydrogen/hydrogen-octave discussion — were read visually on the page images. In every case the terms of §3 are absent from the page, and the tables contain what is transcribed below.

| LoC image | Printed page | USP scan page | Content confirmed visually |
|---|---|---|---|
| 0024 (thumb L-024) | 6 | p-021 | "cycle … descends … through man's unseen universe until hydrogen" passage (§5.1) |
| 0111 (`data/…/loc_0111_full.jpg`, native res) | unnumbered plate | p-109 | 4th/5th/6th-octave wheel; "STARS INDICATE UNDISCOVERED ELEMENTS LOCATED BY THE AUTHOR"; caption §5.2; no isotope terms anywhere on page |
| 0112 (`source_scans/loc/full/p0112.jpg`, native res) | 92 | p-110 | Table of the Ten Octaves, octaves 1–3 (Alphanon → Boston): **ATOMIC MASS and MELTING POINT columns entirely blank** for all 24 rows; no isotope terms |
| 0114 (`data/…/loc_0114_full.jpg`, native res) | 94 | p-112 | Fourth-octave table (§5.4): only two numeric masses on the whole hydrogen-octave block — hydrogen 1.008 and Luminon \*2.92 ("\*Approximate"); no isotope terms |
| 0120 (thumb L-120; also USP text) | 100 | p-118 | Hydron "much lighter" passage (§5.5); no isotope terms |
| 0222–0223 (thumbs L-222, L-223) | 202–203 | p-219–220 | spectroscope chapter; "unseen universe of the first three octaves"; "six empty spaces which follow hydrogen" (§5.6) |

Page concordance used (verified on the folios visible in the images): in the front matter LoC image = USP scan page + 3 (LoC 0024 = USP p-021 = printed p. 6); in the octave-table region LoC image = USP scan page + 2 = printed page + 20 (LoC 0112 = USP p-110 = printed p. 92, matching the program anchor); around the spectroscope chapter LoC 0223 = printed p. 203 = USP p-220. Plates carry no folio; they are cited by LoC image index + USP scan page.

## 5. What the text says instead (verbatim, dual-witnessed)

All quotes below were matched verbatim in both W1 (LoC OCR, line numbers of `loc_fulltext.txt`) and W2 (USP text layer, scan page), and the cited pages were read visually per §4. OCR line-wrap hyphens are silently joined; nothing else is altered.

**5.1 The elements before hydrogen are "unseen"; hydrogen is the first perceivable element** — printed p. 6 (LoC 0024; W1 lines 915–922; W2 p-021):

> "The cycle begins with the highest note and descends the scale sequentially through man's unseen universe until hydrogen, the first element perceivable to man, is reached.
> There is no unseen universe.
> Those tones which follow hydrogen are man's visible or "physical" universe of matter and continue into the tenth octave."

(The one-line paragraph "There is no unseen universe" is Russell's rhetorical point that the "unseen" octaves are knowable through light; it does not retract the placement of those tones below the perceivable range.)

**5.2 In the fourth octave the physical universe begins with hydrogen** — unnumbered plate, LoC 0111 (W1 lines 10518–10520; W2 p-109), caption in capitals:

> "FOURTH, FIFTH AND SIXTH OCTAVES. IN THE FOURTH OCTAVE THE SO-CALLED PHYSICAL UNIVERSE BEGINS WITH BUT ONE OF ITS ELEMENTS KNOWN TO MAN. THE ELEMENT HYDROGEN"

Same plate, explanatory paragraph (W1 lines 10511–10514; W2 p-109) — the mass-ordering rule:

> "Each element is greater in its mass than its predecessor because of the generative power of electricity which acts as a brake against high axial speed and diverts it into accumulating mass."

Legend on this plate and its companions: "★ STARS INDICATE UNDISCOVERED ELEMENTS LOCATED BY THE AUTHOR."

**5.3 The first-octave (sub-hydrogen) table gives no atomic masses at all** — printed p. 92 (LoC 0112, native-res read; W1 lines 10529–10543; W2 p-110). "TABLE OF THE TEN OCTAVES … FIRST OCTAVE WAVE, *Beginning of the Cyclic Inhalation at Tomion*." Rows: Alphanon 100=, Irenon 101+, Vijaon 102+, Marvaon 103+, TOMION 104‡, Alberton 103−, Blackton 102−, Boston 101−. The ATOMIC MASS and MELTING POINT columns are **blank white paper for every row**, likewise for the second- and third-octave tables on the same page. (Row name "Irenon": USP text layer and native-res LoC image agree on *Irenon*; the LoC bulk OCR alone misreads it "Trenon".)

**5.4 The fourth-octave (hydrogen-octave) table** — printed p. 94 (LoC 0114, native-res read; W2 p-112):

| Position | Name | Number | Symbol | Atomic mass | Melting pt. °C |
|---|---|---|---|---|---|
| 0= | Hydron | 400= | Hy | *(blank)* | *(blank)* |
| 1+ | Hydrogen | 401+ | H | 1.008 | −259 |
| 2+ | Ethlogen | 402+ | Eg | *(blank)* | *(blank)* |
| 3+ | Bebegen | 403+ | Bb | *(blank)* | *(blank)* |
| 4‡ | CARBOGEN | 404‡ | Cb | *(blank)* | *(blank)* |
| 3− | Luminon | 403− | Ln | \*2.92 | *(blank)* |
| 2− | Halanon | 402− | Ha | *(blank)* | *(blank)* |
| 1− | Helionon | 401− | Hi | *(blank)* | *(blank)* |

Footnote under the table: "\*Approximate". The only non-standard atomic mass Russell prints anywhere in the ten-octave tables is Luminon's \*2.92; every other novel tone, including all 24 sub-hydrogen rows of octaves 1–3 and Hydron 400=, has an empty mass cell.

**5.5 Hydron, the tone immediately preceding hydrogen, is stated to be LIGHTER than hydrogen** — printed p. 100 (LoC 0120; W1 lines 11273–11286; W2 p-118):

> "Hydron (400=) the master-tone of its octave, is a non-inflammable inert gas which is in every way superior for transportation to hydrogen because it is much lighter, absolutely non-injurious and easier to produce.
> It has all of the safety qualities of helium and its carrying capacity exceeds that of helium by eight times and is double that of hydrogen.
> Both hydron and helium can be produced by transmutation in unlimited quantities at an expense which is negligible…"

(The connective "and" is garbled in both OCR layers — W1/W2 both render "by eight times i is double" — but a native-res read of `data/deuterium_negative/loc_0120_full.jpg` confirms the printed sentence: "It has all of the safety qualities of helium and its carrying capacity exceeds that of helium by eight times and is double that of hydrogen.") Same page, on Luminon (403−): "Luminon (403−), is the basis of the cold light of the future." — a radiative gas for lighting, presented as a distinct element, not as a form of hydrogen.

**5.6 The positions after hydrogen (402+ … 401−) are "empty spaces", not predicted isotopes with properties** — printed p. 203 (LoC 0223; W1 lines 21599–21608; W2 p-220):

> "The three red lines of helium are the antecedents of hydrogen in octaves of the "unseen" universe, and other prominent lines tell the story of the six empty spaces which follow hydrogen."

and (W1 lines 21564–21566; W2 p-220):

> "The unseen universe of the first three octaves and the greater part of the fourth is clearly written in hydrogen and helium."

## 6. Analysis

- **The words are absent** from both independent OCR witnesses (13 term variants, all 0/0; §3) — expected for a 1926 book, since the words did not exist before 1932–34 (§1). The folklore claim must therefore rest on the substances.
- **The substances do not match.** Deuterium (mass ≈ 2.014) and tritium (≈ 3.016) are *heavier* isotopes of hydrogen. Russell's scheme has (a) no isotope concept anywhere (the word and the idea of one element with several masses are both absent; each numbered tone is a distinct named element with its own symbol), and (b) a stated ordering rule — "Each element is greater in its mass than its predecessor" (§5.2) — under which every tone preceding hydrogen (the 24 tabulated tones of octaves 1–3, plus Hydron 400=) is *lighter* than hydrogen. [INFERENCE from his stated rule; his tables print no masses for these tones at all, §5.3.] The one explicit weight characterization of a sub-hydrogen-position gas says exactly that: Hydron is "much lighter" than hydrogen (§5.5).
- **Closest candidates examined honestly.** The fourth-octave positions after hydrogen — Ethlogen 402+, Bebegen 403+, and the exhalation-side Luminon 403− — sit between hydrogen (1.008) and helium (4.0), and Luminon carries the tables' only novel mass value, "\*2.92 (\*Approximate)" (§5.4). If anything in the 1926 text were to be retro-fitted to the hydrogen isotopes it would be these. But the text (a) never links any of them to hydrogen chemically or by name; (b) calls the post-hydrogen positions "six empty spaces" whose story is told only in spectral lines (§5.6); (c) describes Luminon as an inert radiative gas, "the basis of the cold light of the future" (§5.5) — none of which describes a hydrogen isotope; and (d) marks all such tones as "UNDISCOVERED ELEMENTS LOCATED BY THE AUTHOR" (§5.2), i.e., new elements, which deuterium and tritium are not. Ethlogen's only other appearance in the running text concerns "genero-active absorptions of ethlogen (402+)" opposite radium's ejections (W1 line 21922 region) — nothing about weight or hydrogen. Whether later USP-affiliated literature retro-identified 402+/403+ with deuterium/tritium is outside this note's scope; the 1926 text itself does not.
- **Limits of the negative.** Both witnesses are OCR of the same 1926 text (two printings/scans); an OCR miss simultaneous in both is conceivable in principle, which is why the pages where isotope language would have to occur (the ten-octave tables and the hydrogen-octave prose, §4) were read visually at native resolution. No occurrence was found. This note makes no claim about other Russell works or later editions.

## 7. Verdict

In *The Universal One* (1926; LoC gdc.27004508 witness and USP 1974-scan witness), the words *deuterium*, *tritium*, *heavy hydrogen*, *isotope* (and 9 further variants incl. OCR-corruption stems) occur **zero** times in either witness. The text nowhere describes any substance as a heavier form of hydrogen. Its novel gases at and below hydrogen's position are presented as undiscovered distinct elements of the "unseen universe" with blank mass columns; the one it characterizes by weight, Hydron (400=), is stated to be "much lighter" than hydrogen. The claim "Russell predicted deuterium and tritium in *The Universal One*" is unsupported by the 1926 text.

## 8. Reproduction

```
# W2 extraction
pdftotext "source_scans/the-universal-one-by-walter-russell/The Universal One by Walter Russell_text.pdf" data/deuterium_negative/usp_text.txt

# term counts (both witnesses)   -> §3 table
for t in deuterium tritium "heavy hydrogen" isotope isotop deuter trit \
         "hydrogen 2" "hydrogen 3" "hydrogen-2" "hydrogen-3" "heavy water" protium hydrogen helium carbon octave; do
  a=$(grep -o -i -- "$t" source_scans/loc/loc_fulltext.txt | wc -l)
  b=$(grep -o -i -- "$t" data/deuterium_negative/usp_text.txt | wc -l)
  printf '%-16s LoC=%s USP=%s\n' "$t" "$a" "$b"
done

# OCR-variant sweep              -> §3
grep -o -i -E '[a-z]*tium[a-z]*|[a-z]*deut[a-z]*' source_scans/loc/loc_fulltext.txt data/deuterium_negative/usp_text.txt | sort | uniq -c

# confirmation page images       -> §4 (native res; be polite: sequential, ~2 req/s)
for n in 0111 0113 0114 0120; do
  curl -s -o data/deuterium_negative/loc_${n}_full.jpg \
    "https://tile.loc.gov/image-services/iiif/public:gdc:27004508:${n}/full/full/0/default.jpg"
  sleep 1
done
# printed p.92 table already mirrored at source_scans/loc/full/p0112.jpg
```

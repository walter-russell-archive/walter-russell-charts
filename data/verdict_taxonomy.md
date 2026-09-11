# R18 — Verdict taxonomy and scoring rules

Prepared 2026-09-11 (project item R18). This document sets the verdict vocabulary, the evidence standards, and the
scoring rules the scoreboard runs on. It supports `data/scoreboard.json` and `data/scoreboard_schema.json`.

Inputs: `data/claims.json` (46 claims, frozen), `data/claims_notes.md`, `verification/deuterium_negative.md` (R17),
`essay/comparison.md` (R19), `data/modern_elements.json` (R14), `data/russell_1926_elements.json` (R11, frozen).
Two of those inputs, `data/claims_notes.md` and `essay/comparison.md`, are private working notes and are not
published; where a rule below rests on one of them, the figure or the finding is stated here as well.
Downstream: the scoreboard build writes `data/scoreboard.json`, one entry per adjudicated question, validating against
`data/scoreboard_schema.json`. The five worked examples in §5 are embedded verbatim as `examples` in the
schema file and validate against it (`tools/validate_scoreboard.py`; output in §7).

Register: every rule here operates under the ten editorial checks first written as `data/editorial_rules.md`. That
file is private working staging and is not published; the ten checks themselves are published, with their
numbering, as `data/editorial_standards_public.md`. In particular:
verdicts attach to claims, never to persons; no mockery; opinion framed on disclosed facts; measured fact vs
[INFERENCE] always distinguished.

## 1. The verdict vocabulary (closed)

Seven verdicts. No entry may use any other value. Additions or merges to this list require a written justification
appended to this section; the scoreboard build may not extend it silently.

| # | Verdict | Meaning |
|---|---|---|
| 1 | `confirmed` | Every checkable component of the claim, read plainly as printed, is true against the modern record. |
| 2 | `partially confirmed` | The claim splits into checkable components of which at least one is confirmed and at least one is refuted or unfalsifiable. |
| 3 | `refuted` | At least one novel checkable component is false against the modern record, and no novel component is confirmed. |
| 4 | `unfalsifiable` | As printed, the claim yields no component that any observation could confirm or refute — either because its terms have no measurable definition, or because the book itself absorbs every derived consequence by amendment. |
| 5 | `never claimed` | The claim under test is folklore attributed to the 1926 text; the text, searched and read, does not make it. |
| 6 | `terminology only` | The printed matter records period nomenclature or notation, not an assertion by the author; there is nothing of his to score. |
| 7 | `undetermined` | The verdict cannot be issued without resting on an uncertain datum (rule 4.5) or on modern evidence that is genuinely unsettled; the entry states exactly what would resolve it. |

**Justification for the one addition (`undetermined`).** The starting vocabulary had six verdicts. The
uncertain-datum rule (§4.5) forbids a verdict from resting on an `[uncertain]` cell; when every admissible resolution
of the uncertainty leads to a *different* verdict, a closed six-term vocabulary would force either false precision or
silent omission of the claim. `undetermined` is the abstain class with strict entry conditions: it may be used only
when the stability test of §4.5 fails, and the entry must name the blocking datum and the observation (e.g. a
higher-resolution read of a named cell) that would unblock it. It is expected to be rare.

**Additions considered and rejected.**
- *"true but not novel"* as a verdict — rejected. Truth against the modern record and novelty against the 1926
  state of knowledge are different axes. Folding them into one scale would let prior art masquerade as refutation, or
  let a restated textbook fact inflate the confirmed count. Novelty is instead a mandatory annotation (§3.2) and the
  headline counts must always report `confirmed` broken out by novelty.
- *"misattributed" / "exaggerated"* — rejected. Every such case decomposes into a `never claimed` entry for the
  folklore version plus an ordinary entry for what the text actually printed (worked example §5.2 shows the pattern).

## 2. Evidence standards per verdict

Common rule (**dual-evidence rule**): **every non-`unfalsifiable` verdict must cite BOTH (a) a 1926 quote — a
`claims.json` id with the verbatim quote and printed page — and (b) a modern source** — a source object in the shape
used throughout `data/modern_elements.json` (`name`, `url`, `retrieved`, optional `note`). `unfalsifiable` requires
the 1926 quote(s) only; a modern source is optional there (nothing is being compared), though it may be cited to
ground the analysis.

Per-verdict standards (what must be cited, beyond the common rule):

1. **`confirmed`** — for every checkable component: the modern datum that matches it, with source. A component-level
   table (§4.1) is required, plus the novelty annotation (§3.2). If the claim is one instance of a printed class, the
   class base rate must be stated (§3.4).
2. **`partially confirmed`** — the full component split with per-component status and per-component modern evidence;
   the entry must show at least one confirmed and at least one non-confirmed component. Novelty annotation required.
3. **`refuted`** — the modern datum contradicting each refuted component, with source. The refuting component must
   not rest on an uncertain datum (§4.5). The plain reading governs: no strengthening of the claim to make it easier
   to refute, and no weakening to spare it.
4. **`unfalsifiable`** — the verbatim 1926 statement(s), plus a demonstration: either that the claim's terms have no
   measurable definition anywhere in the book, or that the sole consequence(s) the book derives from the claim are
   withdrawn or absorbed by amendment in the book itself (cite the passage doing so).
5. **`never claimed`** — three things: (a) the folklore statement with its provenance (where the attribution
   circulates); (b) the absence verification — an exhaustive-search document with method, terms, witnesses, and
   visual confirmation (for the deuterium case this is `verification/deuterium_negative.md`, which is cited, never
   re-derived); (c) what the text says *instead*, as claims.json quotes — these are the entry's 1926 evidence. The
   modern source under the dual-evidence rule is the actual discovery record of the thing folklore says was
   predicted.
6. **`terminology only`** — the printed matter in context (row or passage), the adopted reading with the evidence
   for it (§4.6), a period-nomenclature source or note establishing the term as period usage, and the modern
   identification of the referent.
7. **`undetermined`** — the 1926 quote(s), the named blocking datum, the admissible readings and the verdict each
   would yield, and the observation that would resolve the block.

## 3. Cross-cutting rules

### 3.1 Premise vs assertion
A claim's quoted data premises (e.g. "the spectrum of helium, wave length 4922.1" — a real line Russell cites) are
*verified for accuracy* but are **not creditable components**: quoting a true measured datum of the period record
confirms nothing about what the claim asserts on top of it. Premises are recorded with role `premise`; only
components with role `assertion` enter the verdict aggregation. A false premise is likewise reported without itself
deciding the verdict; the assertions are still scored as stated.

### 3.2 Novelty axis
Every `confirmed` or `partially confirmed` entry carries `novelty_1926`:
- `novel` — the confirmed content exceeded contemporaneous accepted science (the Mendeleev-gap standard of
  `essay/comparison.md` §1.2);
- `period-standard` — the confirmed content restates what standard 1926 sources already held (e.g. the Moseley gaps
  Z = 43, 61, 72, 75, 85, 87; `essay/comparison.md` §1.4);
- `period-contested` — the content sided with one party of a live 1926 dispute.
Headline reporting must never state a confirmed count without the novelty breakdown.

### 3.3 Aggregation rule (compound claims)
Components are scored individually, then:
1. `never claimed` and `terminology only` are entry-level classifications; their components document the analysis
   and are not aggregated.
2. Otherwise, let **N** be the assertion components with novelty `novel`.
   - If N is non-empty, the verdict follows N: all confirmed → `confirmed`; at least one confirmed and at least one
     not confirmed → `partially confirmed`; none confirmed and at least one refuted → `refuted` (unfalsifiable
     residue noted); none confirmed, none refuted → `unfalsifiable`.
   - If N is empty (the claim's checkable content is wholly period-standard), the verdict aggregates over *all*
     assertion components by the same table, and `novelty_1926` is `period-standard`.
3. If a component that would decide the verdict is `undetermined` under §4.5, the entry verdict is `undetermined`.

The rationale for step 2: a period-standard premise or restatement must not dilute the failure of what the claim
newly asserts (no partial credit for citing real data next to a nonexistent element), while a claim that is entirely
a restatement can still be scored true or false — with its lack of novelty disclosed rather than hidden.

### 3.4 Class base rate (no cherry-picking)
When a claim is one instance of a printed class — the canonical case is the starred/placeholder class of C015/C024:
40 named invented elements plus 8 unnamed "Mate to …" slots — the entry must state the class denominator and the
class hit/miss tally. Crediting a hit without the denominator, or debiting a miss without it, is special pleading
and fails review. The tally for the placeholder class, from the frozen R11 dataset:

- **8 unnamed placeholder slots**; **6** coincide with the position of a real element — 803D+ (between Mo and Ru) →
  Tc (Z=43, 1937); 903D+ (between Nd and Sm) → Pm (Z=61, 1945); one of 903M−/903L− (between Lutecium and Tantalum) →
  Hf (Z=72, already discovered 1923); 903I− (between Tungsten and Osmium) → Re (Z=75, already discovered 1925);
  901− (after Polonium) → At (Z=85, 1940); 1001+ (between Niton and Radium) → Fr (Z=87, 1939). **2** coincide with
  no element: the second of the 903M−/903L− pair (only one element, Hf, exists between Lu and Ta) and 903E−
  (between Platinum and Gold — Z runs 78, 79 with no gap).
- Every one of the six positional matches was either a gap already fixed by Moseley's X-ray sequence (43, 61, 85,
  87) and listed in standard tables, or an element already discovered before the 1926 printing (Hf 1923, Re 1925).
- The **40 named invented elements** (Alphanon … Urium; count per `data/claims_notes.md` §3) correspond to **zero**
  members of the modern record of 118 elements.

### 3.5 One entry, one question
A scoreboard entry adjudicates exactly one question. It may **consolidate** several claims.json ids that print the
same physical claim (rule 4.2), or **split** one id that bundles separable assertions (e.g. C027 carries both the
"Uranium XII" designation and the Uridium/Urium rows; §5.5 splits it). `claim_scope` records which; a split entry
states what it does *not* adjudicate.

## 4. Scoring rules

### 4.1 Compound claims split
Every entry with a truth verdict (verdicts 1–4) lists its components: `role` (premise/assertion), `statement`,
`status`, `novelty`, whether it rests on an uncertain datum, and per-component modern evidence where the status
depends on it. The aggregation of §3.3 must be checkable by a reader from the component table alone.

### 4.2 The same physical claim printed twice with different numbers
Real case: the beta-emanation ejection speed is printed **186,400** miles per second on the [97] plate (C022) and
**"exactly 186,330"** miles per second on p.188 (C035, three occurrences). Rule: one consolidated entry citing both
ids; **both figures are reported; neither is averaged, and the entry may not select whichever figure fares better**
against the modern value (for reference, c = 299,792,458 m/s exactly by the 1983 SI definition ≈ 186,282.4 mi/s;
neither printed figure matches, and beta particles travel below c on a continuous spectrum in any case). The
internal discrepancy of 70 mi/s — against a claim of "exactly" — is itself a printed-record fact and is recorded in
`printed_variants`. The verdict is scored on the physical content common to both printings, under the plain reading.

### 4.3 Typography-only variants
Spelling and typesetting variance (Tomium/Tomion; "hydrogene"; NICKLE on the chart; trailing-period inconsistency in
symbols; em-dash melting points; the p.98 name/symbol column misalignment) is **never scored** — not as error, not
as evidence. It lives in the transcription log (R11) and in `uncertainty_flags` where relevant. Where the book
itself equates variants ("1004 ‡ equals 104 ‡", C023, hence Tomium ≡ Tomion), the equation is honored and the
variants are one entity. No verdict may draw any weight from orthography.

### 4.4 Register rule for verdict prose
Every `verdict_sentence` and `analysis` field passes the ten checks of `data/editorial_standards_public.md`. Operationally:
the grammatical subject of the verdict sentence is **the claim** (schema enforces the sentence starting "The …",
the checklist enforces the rest); "wrong" is never rendered as "dishonest"; where the evidence supports "not
supported by the cited text/record" rather than "false", the former is written; guardrail-list items appear only as
claims under examination; no sarcasm. Entries carry `register_checked: true` as the reviewer's attestation.

### 4.5 Uncertain-datum rule
A verdict may not rest on a datum flagged `[uncertain]` in claims.json or in the R11 transcription. Procedure:
enumerate the admissible resolutions of the uncertain datum; re-derive the verdict under each. If the verdict is the
same under all resolutions, it stands, and the flag is recorded in `uncertainty_flags` with resolution
`verdict-stable`. If any resolution changes the verdict, the entry is `undetermined` with resolution `blocking`.
Components record `rests_on_uncertain_datum`; a refuting component with `true` there cannot carry a `refuted`
verdict (schema-enforced).

### 4.6 Interpretation rule
Where the printed glyphs are certain but their *reading* is interpretive (the C027 "Uranium XII" case), the entry
states `reading_adopted` with the evidence for it and the alternatives with their consequences. The no-special-
pleading check: the entry must show that the adopted reading was chosen on printed evidence, not on which verdict it
yields — concretely, by stating the verdict consequence of each alternative and showing the credit total does not
depend on the choice, or else by going to `undetermined`.

## 5. Worked examples (the five hard cases)

Full machine-readable entries are embedded as `examples[0..4]` in `data/scoreboard_schema.json` and validate against
the schema (§7). Prose summaries with the reasoning follow; quotes are verbatim from `claims.json`.

### 5.1 V001 — "Russell predicted deuterium and tritium" → `never claimed`
Folklore provenance: community attribution, guardrail item 5 of `data/editorial_standards_public.md`; stated as the claim under
test in `verification/deuterium_negative.md` §1. Absence verification: that document — 13 term variants at 0 hits in
both independent OCR witnesses, OCR-corruption sweep, positive controls, and native-resolution visual reads of every
page where isotope language would have to occur. What the text says instead (1926 evidence): C008 (the octaves
before hydrogen are "man's unseen universe"; hydrogen is "the first element perceivable to man") and C030 (Hydron,
the tone before hydrogen, "is in every way superior for transportation to hydrogen because it is much lighter") —
deuterium and tritium are *heavier* than hydrogen. Modern evidence: Urey, Brickwedde & Murphy 1932 (deuterium);
Oliphant, Harteck & Rutherford 1934 (tritium) — the words and substances postdate the book by 6–8 years. Verdict
sentence: *The claim that "The Universal One" (1926) predicted deuterium and tritium is unsupported by the 1926
text: the terms are absent from both witnesses, and the substances the text places at and below hydrogen's position
are presented as distinct undiscovered elements, the only weight-characterized one as "much lighter" than hydrogen.*

### 5.2 V002 — elemental tone/colour assignments → `unfalsifiable`
Claims consolidated: C039 ("Every state of motion is indicated by its own particular color line…"), C041 (red side
= genero-active, blue side = radio-active), C046 (every energy expression has "its own particular tonal sound"),
with C040 and C043; C042 is the diagnostic passage. The book prints **no element→wavelength and no element→pitch
assignment anywhere** — the sole quantitative spectral assignment (He 4922.1 → luminon) is scored separately (V004,
where it is refuted). "Genero-active" and "radio-active [color pressure]" are given no measurable definition. The
one consequence the book itself derives from the color law — sodium's red line should be prominent and its yellow
line weak — is stated at p.205 *as an observed contradiction* and immediately absorbed: "If sodium were perfectly
consistent with the law, its red line should be prominent and its yellow line weak, instead of which they are the
reverse. The explanation is simple. Sodium (601+) is the first positive tone of the sixth octave." (C042). A law
whose sole derived test is conceded to fail and retained by an octave-position exception leaves no checkable
content standing. Modern grounding (optional under the dual-evidence rule, supplied anyway): the Na D doublet at
5889.95/5895.92 Å is the strongest feature of the sodium spectrum (NIST). Why not `refuted`: the book never asserts
the false consequence — it disclaims it in the same breath — so there is no printed false component to refute; what
remains asserted is untestable. Note the folklore variant "Russell gave each element its true frequency" would be
`never claimed`: the book asserts that assignments exist but never states one.

### 5.3 V003 — the unknown element (1001+) preceding radium → `confirmed` (novelty: `period-standard`)
Selection audit for the confirmed-leaning case, per the no-cherry-picking rule:
- **Uridium/Urium (C027)** — examined and rejected as the lead case. Elements beyond uranium do exist (Np 1940,
  Pu 1940). But the printed content beyond "the table continues" is exactly: two named tones (names and symbols
  match nothing), no properties (cells empty), and a terminus — after 1003E+ the cycle *ends* at Tomium. The modern
  record has 26 elements beyond uranium, not two-then-end. Expected scoreboard outcome: `partially confirmed` at
  best (existence of transuranics confirmed; count-and-terminus refuted; names empty).
- **Starred-slot class (C015)** — as a class, refuted-dominated: 40 named inventions, zero exist (§3.4).
- **Inert-gas claims** — C007 ("3½ octaves are missing" of inert gases → Alphanon, Betanon, Gammanon, Hydron: none
  exists) and C045 (noble gases "unite very readily with each other … as interlocking substances": no such gas-gas
  chemistry exists; the 1962-onward noble-gas compounds are fluorides/oxides) lean refuted.
- **C044** is the strongest: *"…caesium (901+) for the ninth octave and the unknown element (1001+) preceding
  radium for the tenth octave."* — the 1+ series named is hydrogen, lithium, sodium, potassium, rubidium, caesium,
  i.e. the alkali column, and the frozen table prints exactly one empty slot ("Mate to 1−", 1001+) between Niton
  (radon, 222.4) and Radium (226.0).
Components: (a) an element, then unknown, exists in the single position between radon and radium — **confirmed**:
francium, Z=87, Perey 1939, the last element discovered in nature; (b) it is the valency-one alkali homolog of the
1+ series — **confirmed**: francium is a group-1 alkali metal; (c) nothing further is checkable — the row prints no
mass and no melting point. Both confirmed components are `period-standard`: the Z=87 gap ("eka-caesium") was fixed
by Moseley's sequence in 1913–14 and carried in standard interwar tables, so under §3.3 step 2 the verdict
aggregates over all assertion components → `confirmed`, `novelty_1926: period-standard`, class base rate stated
(1 of 8 placeholder slots; 6/8 positional matches, all previously identified gaps or already-discovered elements;
0/40 for the named inventions). Verdict sentence: *The claim that an unknown element (1001+) precedes radium as the
tenth row's valency-one position is confirmed by the discovery of francium (Z=87, Perey 1939) — with the
qualification that a gap at that position was standard knowledge from Moseley's 1913–14 sequence, so the
confirmation records no location not already in the period literature.* This entry credits no priority and does not
transfer to the octave scheme.

### 5.4 V004 — luminon and the helium 4922.1 line → `refuted`
Claims consolidated: C013 (plate [89] annotation: "The spectrum of helium, wave length 4922.1 tells the existence
of luminon."), C020 (Luminon's mass "*2.92 … *Approximate" — the only novel mass printed anywhere in the tables),
C032 ("Luminon (403−), is the basis of the cold light of the future…" with the 1/40,000-of-tungsten figure);
related: C014, C029. Premise (verified, not creditable): helium does have a line there — He I 4921.93 Å; the
printed 4922.1 is 0.17 Å off the modern value; the verdict does not rest on that difference. Assertions:
(a) the line evidences an undiscovered element — **refuted**: He I 4921.93 Å is a classified transition of neutral
helium itself (1s2p ¹P° – 1s4d ¹D, singlet system; NIST), fully accounted for by helium's two-electron structure;
(b) an element of atomic mass ≈2.92 exists between hydrogen and helium — **refuted**: atomic number is integral
nuclear charge (Moseley 1913); there is no element between Z=1 and Z=2; the mass-≈3 nuclides ³H and ³He are
isotopes of hydrogen and helium, not new elements (and the 1926 scheme has no isotope concept — R17 §6);
(c) cold light has luminon as its chemical basis — **refuted as stated**: efficient non-incandescent lighting
exists (discharge, fluorescent, LED) and involves no such element; the efficiency figure attaches to a substance
that does not exist. All novel assertions refuted, none confirmed → `refuted`. The `[uncertain]` flags on C013
(hand-lettered comma, quote/period order) are typography-only: verdict-stable under §4.5. Verdict sentence: *The
claim that the helium line at wave length 4922.1 tells the existence of a distinct element luminon is refuted: the
line is a classified transition of neutral helium itself, and no element exists between hydrogen and helium.*

### 5.5 V005 — "Uranium XII" → `terminology only`
Split from C027 (this entry adjudicates only the "Uranium XII" row; the Uridium/Urium content of the same claim id
is a separate scoreboard question — §5.3 selection audit). Printed matter (certain): row "Uranium XII", position
1003B+, symbol "UrXII", mass and melting cells empty, between Thorium (1003A+, Th, 232.15) and Uranium (1003C+, Ur,
238.2). Reading adopted (per §4.6): the period radioelement designation **Uranium X II (UX₂)**. Evidence for the
reading: the symbol "UrXII" is Russell's uranium symbol "Ur" + "XII", matching the UX₂ designation pattern rather
than his coinage pattern (his inventions are proper names — Uridium, Urium, Whitnion — never roman-numeral
designators); the position between thorium and uranium matches the period placement of UX₂ by atomic weight
(≈234 between 232 and 238); radioelement designations of exactly this form (UX₁, UX₂) were standard in the
1913–1926 literature. Alternative reading (an invented element named "Uranium XII"): under it the row joins the
40-name invented class with zero confirmations — under **neither** reading does the row yield credit, so the
verdict choice is not driven by outcome (no-special-pleading check passed). Modern identification: UX₂ = ²³⁴ᵐPa,
identified by Fajans and Göhring in 1913 and named "brevium"; protactinium (Z=91) indeed lies between thorium (90)
and uranium (92) (CIAAW, via the frozen `data/modern_elements.json` protactinium record and its `aliases_1926`).
The `[uncertain]` interpretation flag on C027 is handled by §4.6 as above. Verdict sentence: *The printed row
"Uranium XII" (1003B+, UrXII) is read as the period radioelement designation Uranium X II (UX₂ = ²³⁴ᵐPa), recorded
as nomenclature of the 1913–1926 radiochemical literature rather than an assertion by the author; the row itself
prints no checkable content.*

## 6. Discrepancies found in frozen inputs

None. All facts used here match `data/claims.json`, `data/russell_1926_elements.json`, `data/claims_notes.md`, and
`data/modern_elements.json` as frozen. Two observations recorded for completeness (already documented upstream, not
discrepancies): the p.98 name/symbol column misalignment (R11 `layout_anomaly`; claims_notes §7) is what the
placeholder mapping of §3.4 reads *through*, per the documented intended alignment; and the printed He wavelength
4922.1 (C013) differs from the modern 4921.93 Å — a fact about the 1926 printing, not about the transcription.

## 7. Schema and validation

`data/scoreboard_schema.json` is a JSON Schema (draft 2020-12) for `data/scoreboard.json` entries, with the five
worked entries embedded in `examples`. `tools/validate_scoreboard.py` validates (a) every example against the
schema, (b) referential integrity: every cited `claim_id` exists in the frozen `data/claims.json` and every
`quote_verbatim` in `evidence_1926` is a verbatim substring of that claim's quote, (c) the conditional rules
(dual evidence, never-claimed requirements, refuted-not-on-uncertain-datum) fire as designed. Validation command:

```
python3 tools/validate_scoreboard.py            # validates the schema's embedded examples
python3 tools/validate_scoreboard.py data/scoreboard.json   # future: validates the built scoreboard
```

The validator needs the locally installed
`jsonschema` package (4.23.0 in the run of record) for the schema step; the referential checks are stdlib-only. It is a
validation-time tool, not part of any publication pipeline.

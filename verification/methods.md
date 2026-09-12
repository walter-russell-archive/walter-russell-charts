# Methods

Where the images come from, how the data was read, what the machines did, and how to re-derive every artifact on this site.

Every file this page names ships in the repository behind the site,
[walter-russell-archive/walter-russell-charts](https://github.com/walter-russell-archive/walter-russell-charts).
Paths are relative to its root, and the checksum table at the end covers all of them.

## Sources

Every published image derives from one digitization. The Library of Congress scanned *The Universal One* (New York: Brieger Press, Inc., c1926) as item [27004508](https://www.loc.gov/item/27004508/). The scan holds 290 page images. Each image is served over IIIF at this URL pattern:

```
https://tile.loc.gov/image-services/iiif/public:gdc:27004508:NNNN/full/full/0/default.jpg
```

`NNNN` is the zero-padded image index, `0001`–`0290`. The map from image index to printed folio is `data/loc_page_map.tsv`. All fetches and rights checks in this project were made on 2026-09-11.

The Library states the rights plainly. Its item record says, verbatim:

> The books in this collection are in the public domain and are free to use and reuse.
>
> Credit Line: Library of Congress

Source: `https://www.loc.gov/item/27004508/?fo=json`, field `item.rights`, retrieved 2026-09-11. The full capture, with the collection and legal pages, is in `verification/loc_rights.md`.

Each facsimile plate carries the short credit "Library of Congress". Front matter carries the fuller credit:

> Reproduced from Walter Russell, *The Universal One* (New York: Brieger Press, Inc., c1926), Library of Congress, General Collections, call number Q173 .R85, digitized copy at https://www.loc.gov/item/27004508/. The Library of Congress states that the books in its Selected Digitized Books collection "are in the public domain and are free to use and reuse." Credit Line: Library of Congress.

### The second witness

A 1974 University of Science and Philosophy reprint scan served as a second transcription witness. It is a reading source only. No pixel from it appears in any published image, and none ever will.

The two witnesses are independent only at the scan level. The 1974 plates are photographic reproductions of the 1926 plates. Reading both scans therefore reads one 1926 printing, imaged twice, by independent readers. That establishes what the book printed. It is not independence across editions, and this project never claims that. (Finding R5; restated in `verification/transcription_audit.md`.)

## The dual-source protocol

The dataset `data/russell_1926_elements.json` records 137 element rows with 7 fields each: 959 cells.

Transcription ran as two blind passes. Pass 1 read the Library of Congress scan. Pass 2 read the 1974 scan in a separate context, blind to pass 1. The comparison rules were declared before the passes were compared. The full protocol, every disagreement, and every resolution are in `data/transcription_log_r11.md`.

The frozen dataset was then audited from scratch by four fresh witnesses. Four new blind readers re-read the plates: LoC table, 1974 table, LoC chart, 1974 chart. Each reader worked under an explicit forbidden-file list. None saw the dataset, the transcription log, or any other reader's output. A deterministic diff (`tools/audit_diff.py`) classified every cell. An adjudicator, who was none of the four readers, re-examined every non-agreed cell at 4× zoom in both scans. The full audit is `verification/transcription_audit.md`.

The audit counts:

| Table cells (137 rows × 7 fields) | n |
|---|---|
| total | 959 |
| agreed | 956 |
| resolved by adjudication | 3 |
| left uncertain | 0 |

| Chart-witness cells (supplementary, one per row) | n |
|---|---|
| total | 137 |
| agreed | 134 |
| resolved by adjudication | 3 |
| chart-illegible | 0 |

No glyph in any of the 959 table cells differs between the dataset and either fresh witness. The three adjudicated table cells differ only in a printed space before a sign; the glyphs are identical.

One chart-witness correction came out of the audit, and we disclose it here. In the octave-5 chart label the plates print `BERYLIUM`, with a single L, in both scans. The audit verified this letter by letter at 4×. The first transcription pass had recorded `BERYLLIUM`, so the dataset was amended once, after the audit, to the plate spelling. The table cells for that row are unaffected: the table prints `Beryllium` in both witnesses. A later check found that the same amendment had also been written to the other octave-5 row numbered 502, whose chart label reads `OXYGEN`. That row was restored, and the derived TSV was regenerated from the dataset so that both files agree. Both amendments are logged in `data/transcription_log_r11.md`, and the audit evidence is in `data/disagreements.tsv` and the audit file.

## Machine assistance

This project used machine readers and discloses exactly where.

**Transcription.** Vision language models read the plates from zoomed crops. Tesseract 5 OCR ran on the same images as a cross-check. Readings from the two scans were compared mechanically. An adjudicating agent ruled every disagreement from the pixels, at 4× zoom, in both scans. Every ruling and its evidence crop is on file. No reading entered the dataset unexamined.

**Image restoration.** The facsimile cleanup is deterministic from end to end. The pipeline (`tools/restore.py`, parameters chosen by the study in `verification/restoration_study.md`) performs, in order:

1. Background estimation: grayscale morphological closing, window 101 px.
2. Flattening: divide the scan by the estimated background.
3. Binarization: global Otsu threshold on the flattened image.
4. Despeckle: remove ink components of area ≤ 8 px.
5. Frame removal: drop ink components touching the image boundary.
6. Stroke repair: none.

What was **not** done: no generative or diffusion enhancement, no learned upscaling, no inpainting, no synthesis of any pixel, no manual retouching, no resampling. Every output pixel is a deterministic function of the input scan.

**Geometry.** The redraw is generated from measurements, not traced. `tools/measure_geometry.py` measures the chart's rings, spiral, sector dividers, and label clusters from the LoC scan. It uses only recorded deterministic algorithms: Otsu thresholding, connected components, gradient-vote center accumulation, polar resampling, ridge tracking, trimmed least-squares circle fits, and linear pitch fits. `tools/render_chart.py` then draws the SVG from the frozen dataset plus the measured geometry. Of its 137 element placements, 117 snap to measured label clusters and 20 come from the recorded placement model. Each SVG group declares which, in a `data-placement` attribute.

## The disagreement log

Every disagreement in the project is logged with its evidence.

- Transcription (two-pass): 874 of 959 cells agreed first-pass. 85 were resolved: 81 were a documented spacing convention of the metal type, and 4 were glyph adjudications. 0 remained uncertain. Log: `data/transcription_log_r11.md`.
- Audit (four-witness): 3 table cells and 3 chart-witness cells went to adjudication. All 3 table cells and 2 chart cells ruled dataset-correct. 1 chart cell was the `BERYLIUM` error, corrected in the dataset as described above. 0 remained uncertain. Log: `data/disagreements.tsv`, one row per cell, with the crop paths for both witnesses.

### What stays private, and why

The logs above cite evidence crops and pass files under `data/audit_crops/`,
`data/audit_work/` and `data/elements_work/`. Those directories are private
working staging and are not published. One reason decides it: half of every
comparison pair is cut from the 1974 printing, and no pixel of that printing is
published here. The published side is fully reproducible without them. Each
disagreement row names its octave, row and cell, the three published Library of
Congress pages carry the printed source, and the reader can cut the same crop.

## Re-derive it yourself

The commands below rebuild the published artifacts from the public scan. Dependencies: Python 3.11, numpy, Pillow; Inkscape only for the optional overlay proof. The Library asks automated clients to stay under 10 requests per minute; honor that.

```
# 1. Fetch the source plates from the Library of Congress
curl -s "https://tile.loc.gov/image-services/iiif/public:gdc:27004508:0016/full/full/0/default.jpg" \
     -o source_scans/loc/full/p0016.jpg
curl -s "https://tile.loc.gov/image-services/iiif/public:gdc:27004508:0113/full/full/0/default.jpg" \
     -o source_scans/loc/full/p0113.jpg

# 2. Facsimile cleanup (raw scan -> cleaned bitonal plate)
python3 tools/restore.py source_scans/loc/full/p0016.jpg --outdir data/restoration_study/final

# 3. Chart geometry (raw scans -> measured geometry JSON + overlay proofs)
python3 tools/measure_geometry.py

# 4. Redraw (frozen dataset + measured geometry -> charts/russell_periodic.svg)
python3 tools/render_chart.py

# 5. Derived table (dataset JSON -> data/russell_1926_elements.tsv)
python3 tools/elements_json_to_tsv.py

# 6. Scoreboard validation (schema + referential integrity + rule checks)
python3 tools/validate_scoreboard.py data/scoreboard.json

# 7. Site, then the two manifests, in this order
python3 tools/build_site.py
python3 tools/make_image_provenance.py
python3 tools/make_checksums.py

# 8. Verify the manifests against the files on disk
python3 tools/check_image_provenance.py
python3 tools/make_checksums.py --check
```

Step 7 has a required order: the image manifest records the hashes of the built
images, and the checksum table records the hash of the image manifest. The site
build refuses to run against a stale checksum table, so a skipped step fails
loudly rather than publishing a wrong number.

Verify your fetched plates against the checksums below before running the pipeline.

Byte-determinism, as verified:

- `tools/restore.py`: re-run on 2026-09-11; all five outputs matched the recorded outputs byte for byte.
- `tools/render_chart.py`: re-run on 2026-09-11; `charts/russell_periodic.svg` came out byte-identical (same SHA256 as below).
- `tools/measure_geometry.py`: the R13 record verified byte-identical geometry files on re-run from the same scans.
- `tools/validate_scoreboard.py` is read-only and deterministic; it exits 0 only when every check passes.

## Checksums

SHA256 of every published artifact, its sources, and the tools that build them. The same list, machine-readable, is `verification/checksums.tsv`.

| File | Bytes | SHA256 |
|---|---|---|
| `data/russell_1926_elements.json` | 74187 | `f3021dc85e72e9e39cff108085f20cf48f2138e74a40d38929db90f628ed938a` |
| `data/russell_1926_elements.tsv` | 21330 | `0e92525a24efb36f34cbb4253127d2818f619622627d5e3b4f996df3ec839544` |
| `data/claims.json` | 30256 | `cd28aeb70aa52ca1010b07e5f145410d2aa37d97cd612805ed6e2b7de4522da9` |
| `data/modern_elements.json` | 220571 | `621a70cf5633c5a67755874a163b905c5ffe6a940d6c1e2d72692da935153102` |
| `data/reconciliation.tsv` | 14615 | `cec97d3d928cfab397c710bda84cda7338ac8b127c2c4b3b952579da947e3104` |
| `data/scoreboard.json` | 117743 | `989d3a9671fd4bacca1b5af08b5027edcf306870438780945132e62b50160a44` |
| `data/disagreements.tsv` | 1361 | `8b516019f22770de72e3c6bfb12baf795200fc0f75f7ad3fbb832859d13b552d` |
| `data/chart_geometry.json` | 604864 | `3bc443f6166d81df2785a2d72799d2b56f6aa1ffda83d1decdecda1ccc12a598` |
| `data/wheel_geometry.json` | 110463 | `62951162611d2c9cc2c8321e6da8899f07edf4d0baf84dcf0c610e4f6956efbc` |
| `data/scoreboard_schema.json` | 40480 | `1cec72a43c9d500306f8427c990ecf57be737deee55f0014f124164902989bf5` |
| `data/verdict_taxonomy.md` | 26558 | `06ae4ccba1ac3055dbbcaeb8c021a852e3e543bfd1faefab42f9e287f12e6502` |
| `data/loc_page_map.tsv` | 18464 | `ca63777d2fb0df82ed5249953ca2d8e2f1e5c724b0220cf0b65702ff11fb8a91` |
| `data/transcription_log_r11.md` | 15935 | `f5ce73d04a2be816bb2118b12e35ecafd82a1452e011de5f347ac54c8a267d76` |
| `data/editorial_standards_public.md` | 2970 | `622bb1fc455b82635b9c068bb7a36042a0c6394383b2667f252061b084055c05` |
| `data/claims_notes.md` | 14909 | `8866d7b7a7c8f83a4e4c2e8740b6b0a206ddc1cb1a0f8903f27bd18eb324de99` |
| `data/plate_audit.md` | 12856 | `59d8801a3b56755ac64e3fb0b0f241fc665a5400824a19eff453f28977ea2ed8` |
| `data/comparison.tsv` | 7606 | `2e4458efe7f372a75360e74b52facf8f2819d57ce4a6046427713f8a200ff67a` |
| `data/restoration_study/scoring_protocol.json` | 3073 | `03ee92dc469a5fc357b30db4dc65dff9245a7756c50a405de87c4dbc1db6aaf6` |
| `charts/russell_periodic.svg` | 122550 | `2e43c1834b058005303f14b649709385e7300c00606e74fe22fcc04871416d71` |
| `essay/comparison.md` | 15550 | `86a8b4b1b5b411519155286080ca922e1830463a9f732bcb818a2bf7f45e004d` |
| `verification/transcription_audit.md` | 13066 | `5a8cd7a4eb46e5f840838d9b1b42d144265f344ce47e5422e466c63ba4ac2d95` |
| `verification/restoration_study.md` | 16938 | `f6124faf10a7fe2c803bce1944e48bce8ff34804cb830566643f1865be8c8691` |
| `verification/loc_rights.md` | 5996 | `3b5a53fc9808037c9b44b0a041f0bc158e61656b315e43269632400124bf2494` |
| `verification/deuterium_negative.md` | 17578 | `a0b0e870a4f337e4edbe4cfa305bb04b55e92de0dc1f4bdb3ac09b199d055303` |
| `verification/image_provenance.tsv` | 8725 | `47692800932877266a340d6a98f407ab1baa141c0162bafb0add5231b3d31ba1` |
| `source_scans/loc/full/p0016.jpg` | 1409306 | `b718e70c57942324cc191ba42d63d5aacd0fcd249f3cae2a9b488b61b7726e37` |
| `source_scans/loc/full/p0112.jpg` | 655191 | `bf32acd2c03157b5695740dd3f33d1592dd811271c12e9b4ca3055f67064bbe8` |
| `source_scans/loc/full/p0113.jpg` | 620077 | `cce0990a61133affc4a908d4f6b3002df0d9b547a24395a82a473eca5d9979f0` |
| `tools/restore.py` | 12287 | `be860d5ac9896976fe10eb1d97d59cffc155f37b50cc9a399424cc803fb89ee4` |
| `tools/measure_geometry.py` | 40385 | `00b3f090aa0ffd670962fff2f50463ee90093de7bac0cc761550e883a5a12ec0` |
| `tools/render_chart.py` | 34623 | `e58960e30fa04758759351f4b250951d0ea7ea3267f824fa44c709f88e017b53` |
| `tools/elements_json_to_tsv.py` | 1400 | `4a36ffc2d08b7b1b9cbf41a68a1980d9ccff9726756134fb7459bf8f948e3697` |
| `tools/validate_scoreboard.py` | 5192 | `1b6b21cc21918b885a0887d7d6cf70c7d656b288d59f486e9c6fc5798eaf46a8` |
| `tools/audit_diff.py` | 10230 | `1045e88650d381ac4ef985a956b09cabdffbb653612ecee6b2c0ed25c9c2571f` |
| `tools/make_image_provenance.py` | 23230 | `87db69a457385ec92368b11aa394c9014c5ea916a4437c3f0978af787392598a` |
| `tools/check_image_provenance.py` | 7216 | `6e52c05e65bc4f718cfea3d0068afb3dbd0e7ae5c237b54bb14d56884444fcab` |
| `tools/make_checksums.py` | 4818 | `2017b31e53f39fb5b13ce97ae0950328b528dac74038a51c303a7f96bf53019a` |

The table above and `verification/checksums.tsv` come from one list in
`tools/make_checksums.py`, so they cannot disagree. Regenerate both from the
repository root:

```
python3 tools/make_checksums.py
```

To verify without writing anything, which is what the site build runs:

```
python3 tools/make_checksums.py --check
```

To check any single file: `shasum -a 256 <file>` on macOS, or `sha256sum <file>` on Linux.

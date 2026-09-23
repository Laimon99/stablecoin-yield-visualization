# Refined submission, September 2026

The current submission is `outputs/submission/refined/Simone_Ragusini_945119.pdf`.
The original and first revised submissions remain unchanged for comparison.
The 17-page refined PDF is self-contained; the editable PowerPoint is in
`outputs/refinement/Simone_Ragusini_945119_Stablecoin_Yield_refined.pptx`.

## Corrections and sensitivity checks

- **Daily event trigger:** the previous code used changes between successive
  observations, including missing calendar days. Ten of the first 453 selections
  were nonconsecutive. Enforcing consecutive dates *before* selecting the first
  three valid events per pool gives 450 events in 174 pools; later valid events
  can replace excluded selections. Corrected medians are 18.08823% at day 0 and
  8.24371% at day 30, with median TVL ratio 1.692026. The code change applies to
  future full-pipeline runs. Historical report files retain their original data.
- **Composition:** 394 events appear at day -7, 450 at day 0 and 439 at day 30.
  A paired endpoint check retains the same 439 events with valid APY and positive
  TVL at both endpoints. APY medians are 17.96071% and 8.24371%; median TVL ratio
  is 1.692026. This check does not impose complete observations between endpoints,
  identify causal effects or make overlapping events independent.
- **Survival uncertainty:** the historical Kaplan-Meier S(30) remains 6.2247%.
  The original lifelines pointwise 95% interval is 5.3434%-7.1938%. Resampling
  all 250 pools with replacement, with all their episodes retained together,
  gives a 95% percentile interval of 4.7611%-7.8564%. There are 2,000 replicates,
  using NumPy default_rng seed 945119. This is conditional on the selected pool
  sample and original observed-run definition, not a correction for selection,
  left boundaries or missingness. Seventy episodes begin at pool entry and 56
  terminate before gaps longer than two calendar days. No claim is made that
  these are known economic failures.
- **Mechanisms:** each component median uses its available pool-days. Zero
  reward medians are real zeros; absent values are not imputed as zero. Group
  counts and coverage are in `outputs/refinement/mechanism_coverage.csv`.
  Reward coverage varies from 15.9% to 91.9%. Component medians are not additive.
- **Joint screen:** inclusive comparisons use unrounded medians. The TVL
  threshold is USD 17,736,233. Bubble area is proportional to TVL up to p95,
  using one scale for both colors, with a numerical size key. The earlier
  graphic used a radius offset that did not make area exactly proportional.
- **Depeg:** the shown minimum is a daily observation in the selected window,
  not an intraday market low. Daily pool counts vary between 9 and 10, with
  9 at day 0. The APY comparison is descriptive and composition can change.
- **Delivery:** actual PDF URI links, larger source notes and darker text
  improve navigation and readability. All 17 pages retain the original style.

## Public aggregate reconstruction

From a clone of the repository, with Python 3.11+ and uv:

```sh
uv sync --frozen --extra dev
uv run python scripts/refine_submission.py
```

This command reads `outputs/refinement/report_summary.json`, corrected event
aggregates and the historical published survival/depeg tables. It checks event
headlines against the event table and rebuilds the Matplotlib graphics without
provider API calls. `--output-dir PATH` writes graphics to a separate directory.
It does not independently reconstruct the private historical raw data or the
pool bootstrap. On Windows with Python 3.11 and accented checkout paths, use
`$env:PYTHONPATH = (Resolve-Path src).Path` if editable imports fail.

With the author's existing historical analytical panel:

```sh
uv run python scripts/refine_submission.py --refresh-local
```

This regenerates corrected event aggregates, mechanism coverage, the paired
endpoint sensitivity, bootstrap interval and refined summary. The JSON audit
records the input panel SHA-256 and random seed. It does not collect live data
or redistribute raw or row-level provider records.

## Presentation rebuilding

The optional builder requires Artifact Tool. The Plotly heatmap remains the
existing export in `outputs/revision/ranking_plotly.png`; the refined evidence
command must run before the builder. The original survival audit is retained.

```sh
node scripts/build_revised_presentation.mjs --skip-preview --output tmp/revision/refined-candidate.pptx
```

Finalize and inspect the candidate, then on Windows export with PowerPoint:

```powershell
./scripts/render_presentation_powerpoint.ps1 -InputPptx tmp/revision/refined-candidate.pptx -OutputDir tmp/refinement/rendered -OutputPdf tmp/refinement/candidate.pdf
uv run python scripts/link_submission_pdf.py tmp/refinement/candidate.pdf outputs/submission/refined/Simone_Ragusini_945119.pdf
```

The PDF linker refuses to overwrite an existing file. Choose a new destination
for later revisions. Rights and third-party data exclusions remain as in
`LICENSE` and `NOTICE.md`.

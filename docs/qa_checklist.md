# QA Checklist

Final QA date: 2026-07-08. Pipeline mode: `full`.

## Data QA

- [x] Raw, processed and analytical counts reconcile in `scripts/reproduce_all.py --mode full`.
- [x] Unique keys validated: `pool_day.unique_key` passed.
- [x] UTC/day timestamps used in raw envelopes and panel dates.
- [x] No future timestamps in analytical output.
- [x] Nulls distinct from zero; TVL missingness warning retained.
- [x] Duplicates handled through source IDs and quality checks.
- [x] Outliers flagged and preserved: 32 APY observations above 1000 percent.
- [x] Manual entity mapping rules documented in `docs/entity_resolution.md`.
- [x] Checksums recorded in raw manifest and release manifest.
- [x] Missingness by critical field reported in `outputs/quality/data_quality_report.md`.
- [x] Entity resolution confidence reported and low-confidence check passed.
- [x] Data freeze represented by full regenerated artifacts dated 2026-07-08.

## Statistical QA

- [x] Outcomes defined before analysis in `config/metrics.yaml` and `docs/methodology.md`.
- [x] Sample size reported: 250 pools and 137,095 pool-days.
- [x] Baselines included through market overview and robustness checks.
- [x] Heavy tails handled with medians, quantiles and explicit outlier warnings.
- [x] Survival analysis includes Kaplan-Meier confidence intervals and censoring.
- [x] Threshold sensitivity checked at 5, 10 and 20 percent APY.
- [x] No causal overclaim; TVL is described as observed proxy.
- [x] No future leakage in event windows.
- [x] Alternative explanations documented in insight registry and limitations.

## Figure QA

- [x] Each figure has a question.
- [x] Each figure has a one-sentence message.
- [x] Figure titles are conclusive.
- [x] Units and sample sizes included.
- [x] Source notes included.
- [x] Transformations declared in report/methodology.
- [x] Accessible restrained palette used.
- [x] No clipped text found in inspected hero/depeg/presentation contact sheet.
- [x] PNG/SVG/PDF exported for the figure package.
- [x] Figure registry paths are relative and point to existing files.

## Release QA

- [x] `uv run ruff check src scripts tests`.
- [x] `uv run pytest tests/unit tests/contract tests/integration tests/regression`.
- [x] `uv run python scripts/reproduce_all.py --mode full`.
- [x] Release manifest generated at `outputs/release_manifest.json`.
- [x] Report and slides regenerated from full-mode tables.
- [x] Oral defense notes prepared in `docs/oral_defense.md` and slide speaker notes.

Residual warnings are intentional and documented: 26 missing TVL values and 32 APY values above 1000 percent in the full panel.

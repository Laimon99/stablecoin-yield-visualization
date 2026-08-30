# Course Requirements Matrix

Extraction date: 2026-07-08. Final verification date: 2026-07-08.

The official course PDFs, slide exports, examples and audio were reviewed in the private course
workspace. They are intentionally excluded from the public portfolio repository because they
are third-party teaching materials. Audio files were not transcribed because reproducible local
ASR tooling was unavailable at the time of the academic analysis.

| Requirement | Source | Evidence | Status |
| --- | --- | --- | --- |
| Define a clear research question before analysis. | Lecture 1, p.4; lecture 3, p.4; notes sec. 3.1 | `docs/project_charter.md`, `docs/research_questions.md` | Done |
| Use machine-readable data. | Lecture 1, pp.7-8; notes sec. 1.3 | Raw JSON envelopes, processed parquet/csv, analytical parquet/csv under `data/` | Done |
| Provide metadata and data dictionary. | Lecture 1, pp.9-10; notes sec. 1.4 | `docs/source_registry.md`, `docs/data_dictionary.md`, `data/raw/manifest.jsonl`, `outputs/release_manifest.json` | Done |
| Verify source trustworthiness, methodology, limits and bias. | Lecture 1, pp.30-33; notes sec. 1.6 | `docs/source_feasibility.md`, `docs/source_registry.md`, contract tests, raw verification samples | Done |
| Check licenses and ethical/legal reuse. | Lecture 1, pp.34-39; notes sec. 1.7 | `NOTICE.md`, `docs/source_registry.md`, raw and row-level provider data excluded from public release | Done |
| Preserve original data and document cleaning steps. | Lecture 2, p.36; notes sec. 2.5.3 | Append-only `data/raw/`, transformations in `src/stablecoin_yield/transformation/`, `outputs/quality/data_quality_report.md` | Done |
| Ensure one row per observation and one variable per column. | Lecture 2, p.10; notes sec. 2.3 | `data/analytical/pool_day_panel.parquet`, `pool_day.unique_key` quality check | Done |
| Standardize formats, types, nulls and measurement conventions. | Lecture 2, pp.10-11 | `src/stablecoin_yield/validation/quality.py`, `outputs/quality/data_quality_checks.csv` | Done |
| Disambiguate entities and remove true duplicates only after review. | Lecture 2, pp.7, 11, 33 | `docs/entity_resolution.md`, confidence fields in `data/processed/pools.parquet` | Done |
| Use distributions, mean, median, min, max and mode to understand data. | Lecture 3, pp.5-15; notes sec. 3.2 | `outputs/tables/market_overview.csv`, `outputs/figures/fig_02_apy_distribution.*` | Done |
| Investigate outliers rather than hide them. | Lecture 3, pp.17-20; notes sec. 3.3 | APY extreme warning retained in `outputs/quality/data_quality_checks.csv`; report limitations | Done |
| Compare meaningful groups. | Lecture 3, pp.21-26; notes sec. 3.4 | Pool type, chain, protocol and mechanism figures/tables, especially `fig_01`, `fig_06`, `fig_09` | Done |
| Normalize using rates/ratios when groups differ in scale. | Lecture 3, pp.27-30; notes sec. 3.5 | Persistence ratios, reward shares, TVL event index in `outputs/tables/` | Done |
| Design for a defined audience. | Lecture 4, pp.4-7; notes sec. 4.2 | `docs/project_charter.md`, report, slide deck | Done |
| Let chart function determine chart form. | Lecture 4, pp.8-12; notes sec. 4.3 | Figure registry and storyboard: `outputs/figures/figure_registry.csv`, `docs/visualization_storyboard.md` | Done |
| Use visual hierarchy to guide attention. | Lecture 4, p.13; notes sec. 4.4 | `config/visualization.yaml`, final figure package, presentation contact sheet | Done |
| Communicate uncertainty, missingness and imperfect data. | Lecture 4, pp.14-17; notes sec. 4.5 | Survival CI table, quality warnings, limitations sections | Done |
| Use accessible, respectful visual design. | Lecture 4, p.18; notes sec. 4.6 | Colorblind-aware figure palette, source notes, no financial recommendation framing | Done |
| Avoid misleading charts. | Lecture 4, pp.21-28; notes sec. 4.8 | Figure QA, no 3D/pie charts, axis/source notes, `presentation_qa.md` | Done |
| Provide data source, limitations and license in final deliverable. | Assignment example pp.2, 6; Vlad example pp.3-4, 28 | Report references, slide footers, `docs/limitations_ethics.md` | Done |
| Convert analysis into a coherent story, not a chart dump. | Lecture 4, p.44; examples Vlad and assignment | `outputs/report/stablecoin_yield_report.pdf`, `outputs/presentation/stablecoin_yield_presentation.pptx` | Done |

Residual caveat: course audio could not be transcribed locally; this historical limitation is
documented in `docs/decision_log.md` and `docs/limitations_ethics.md`. The course files themselves
are not part of the public portfolio release.

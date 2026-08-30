# Implementation Plan

Final status: all stages G0-G8 were executed in full mode on 2026-07-08. Evidence is summarized in `docs/completion_audit.md` and `outputs/release_manifest.json`.

## Stage G0 - Project Framing

Tasks:

- C00: Extract course requirements.
- C01: Freeze project charter.
- Draft research questions, risk register, decision log and limitations.

Acceptance criteria:

- `docs/course_requirements.md`, `docs/project_charter.md`, `docs/research_questions.md` and `docs/risk_register.md` exist.
- Primary question is measurable and not a pool ranking.

## Stage G1 - Source Feasibility

Tasks:

- S00: Verify DeFiLlama yields current pools and history endpoints.
- Verify DeFiLlama stablecoin metadata endpoint.
- Verify CoinGecko market/price endpoint and public limits.
- Save raw samples and update source registry.
- Create contract tests.

Acceptance criteria:

- Live raw sample for each critical source.
- `tests/contract/` validates minimum schema offline against samples.
- Feasibility memo documents coverage, limits and blockers.

## Stage G2 - Data Pipeline and Canonical Model

Tasks:

- C03: Bootstrap environment, package and scripts.
- C04: Implement raw envelope, checksum, manifest, retry, rate limiting and cache.
- S01-S05: Define population, collect histories, map stablecoins and enrich prices.
- S02-S03: Pool and stablecoin entity resolution.

Acceptance criteria:

- Repeated ingestion is idempotent.
- Raw files are append-only and checksummed.
- Processed tables match canonical schema.

## Stage G3 - Data Quality

Tasks:

- C05: Validation framework.
- S07-S10: APY/TVL cleaning, stale series, outliers, duplicates and quality report.

Acceptance criteria:

- Completeness, validity, uniqueness, consistency, timeliness and coverage reported.
- Critical failures block full pipeline; sample pipeline produces a documented report.

## Stage G4 - Yield Episodes

Tasks:

- S09: Implement episode segmentation for absolute and percentile thresholds.
- Add unit tests for gaps, missing dates, censoring and boundaries.

Acceptance criteria:

- `yield_episodes` table generated and reconciled.
- Episode tests pass.

## Stage G5 - Analysis

Tasks:

- S11: Kaplan-Meier survival and at-risk counts.
- S12: Yield frontier.
- S13: Ranking churn.
- S14: APY/TVL event response.
- S15: Depeg event study.
- S16: Archetypes and cases.
- Robustness and insight registry.

Acceptance criteria:

- At least three validated insights with robustness records.
- Tables and figures are generated from analytical data only.

## Stage G6 - Visualization

Tasks:

- C06: Design system and figure specs.
- S17: Required figure package and hero visualization.

Acceptance criteria:

- Each figure has question, one-sentence message, source note, period, units, sample size and exported PNG/SVG/PDF where possible.
- Visual QA detects no missing outputs.

## Stage G7 - Report, Presentation and Oral Defense

Tasks:

- Build Markdown and PDF report.
- Build presentation assets and PPTX deck.
- Build oral defense Q&A.

Acceptance criteria:

- Report answers primary question by research question and insight.
- Slide numbers match tables.
- Oral defense uses Direct answer, Evidence, Method, Limitation, Implication.

## Stage G8 - Reproducibility and Release

Tasks:

- C07: one-command reproduction.
- Regression tests and release manifest.
- Clean environment check.

Acceptance criteria:

- `make reproduce-sample` passes.
- `make test` passes.
- Full mode either passes or documents exact external blocker and human input required.

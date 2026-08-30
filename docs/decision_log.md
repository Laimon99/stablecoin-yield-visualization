# Decision Log

## D-001 - Stablecoin Yield selected as final project

**Date:** 2026-07-08
**Context:** The user explicitly requested full implementation of the Stablecoin Yield project.
**Options considered:** Develop Stablecoin Yield; compare both finance/crypto candidates first.
**Decision:** Develop Stablecoin Yield directly to final delivery.
**Rationale:** User instruction overrides the earlier dual-track prototype framework.
**Consequences:** Memecoin playbook remains private reference material; the selected project is
the sole focus of the public repository.
**Evidence:** User prompt and attached specification.
**Owner:** Codex.

## D-008 - Curate a clean public portfolio repository

**Date:** 2026-08-30
**Context:** The academic repository included course recordings, example submissions, raw API
payloads, generated row-level datasets and the project under a nested path.
**Decision:** Promote the project to the repository root, remove unrelated teaching material,
exclude provider payloads and row-level generated datasets, and publish a clean `main` history.
**Rationale:** A public portfolio should contain authored work, portable paths, clear attribution
and no ambiguous redistribution of third-party material.
**Consequences:** Frozen aggregate outputs remain visible; exact historical raw payloads remain in
the verified local backup rather than the public repository.
**Evidence:** `docs/portfolio_readiness_audit.md`, `NOTICE.md`.
**Owner:** Codex.

## D-009 - Freeze the accepted exam presentation

**Date:** 2026-08-30
**Context:** Repository cleanup must not alter the deck used for the exam.
**Decision:** Preserve the accepted PPTX byte-for-byte and record its SHA-256.
**Rationale:** Repository improvements and report portability must not introduce presentation
regressions before the exam.
**Consequences:** Future presentation revisions require a new filename; the committed exam deck
remains immutable.
**Evidence:** `docs/exam_presentation_integrity.md`.
**Owner:** Codex.

## D-002 - Primary unit and grain

**Date:** 2026-07-08  
**Context:** The playbook requires DeFi pool and pool-day analysis.  
**Options considered:** pool-day, protocol-day, stablecoin-day.  
**Decision:** Use pool-day as the primary analytical grain.  
**Rationale:** It preserves duration, APY, TVL and ranking dynamics while supporting aggregation.  
**Consequences:** All figures and analyses must reconcile to the pool-day panel.  
**Evidence:** Stablecoin playbook sections 2 and 7.  
**Owner:** Codex.

## D-003 - Primary high-yield threshold

**Date:** 2026-07-08  
**Context:** Specification requires thresholds 5, 10, 20 percent and cross-sectional percentile.  
**Options considered:** 5 percent, 10 percent, 20 percent, daily top decile.  
**Decision:** Use APY >= 10 percent as the preregistered primary threshold, with alternatives for robustness.  
**Rationale:** 10 percent is high enough to represent a headline high-yield regime but common enough to support survival analysis.  
**Consequences:** All threshold-dependent claims must report robustness at 5 percent, 20 percent and top-decile definitions.  
**Evidence:** Stablecoin playbook section 6.3 and config template.  
**Owner:** Codex.

## D-004 - No single opaque risk score

**Date:** 2026-07-08  
**Context:** The specification warns against hidden ratings and investment-like ranking.  
**Options considered:** single Yield Quality Score; multi-dimensional frontier.  
**Decision:** Use a multi-dimensional frontier as the primary hero visualization.  
**Rationale:** It communicates trade-offs without implying a universal best pool.  
**Consequences:** Any optional score must be transparent, componentized and supplemental.  
**Evidence:** User specification sections 14, 19 and stablecoin playbook sections 10.13, 15.  
**Owner:** Codex.

## D-005 - Audio material not transcribed locally

**Date:** 2026-07-08  
**Context:** Course audio files exist in `.m4a` format. The specification says to analyze them when tools permit.  
**Options considered:** local transcription; document limitation.  
**Decision:** Document limitation because `ffmpeg`, `whisper` and `speech_recognition` are unavailable locally.  
**Rationale:** Adding an ASR dependency or using paid/cloud transcription would introduce non-trivial external requirements.  
**Consequences:** Requirements extraction relies on PDFs, images and examples.  
**Evidence:** Local tool checks on 2026-07-08.  
**Owner:** Codex.

## D-006 - Stablecoin symbol overrides for entity resolution

**Date:** 2026-07-08  
**Context:** Stablecoin symbols are not globally unique across DeFiLlama records. For example, tickers such as `USDS`, `USDE`, `USD0` and wrapped/yield-bearing variants can map to multiple source assets.  
**Options considered:** Use last symbol match; use only exact source IDs; maintain a documented preferred-symbol override table for common stablecoin tickers.  
**Decision:** Use source IDs where available and a documented preferred-symbol override table for high-impact ticker collisions.  
**Rationale:** The project needs stable pool exposure mapping for depeg windows and pool categorization. A pure ticker lookup silently maps some pools to the wrong stablecoin entity.  
**Consequences:** Pools retain `entity_resolution_confidence`, `manual_review_required` and `entity_resolution_note`; manual overrides are visible and testable rather than hidden.  
**Evidence:** `src/stablecoin_yield/transformation/entities.py`, `docs/entity_resolution.md`, regression test for observed depeg exposure.  
**Owner:** Codex.

## D-007 - Depeg event selection uses reviewed historical stress events before raw maxima

**Date:** 2026-07-08  
**Context:** In full mode, choosing the maximum absolute price deviation among exposed major stablecoins can select an extreme source outlier that dominates the visual narrative.  
**Options considered:** Always choose maximum deviation; manually hard-code one event; prefer documented historical events if they are present in the data and have exposed pools, then fall back to bounded source deviations.  
**Decision:** Prefer the USDC/DAI March 12, 2023 stress window when present and observed in the panel; otherwise fall back to deviations above 1 percent, ignoring unreviewed deviations above 20 percent unless no bounded candidate exists.  
**Rationale:** The depeg study is a context visualization, not anomaly hunting. It should show a defensible peg-stress episode with observed pool exposure.  
**Consequences:** Extreme source price deviations remain in `stablecoin_prices` and `risk_events`, but the main figure uses a reviewed event selection rule.  
**Evidence:** `src/stablecoin_yield/analysis/pipeline.py`, `outputs/tables/depeg_event_study.csv`, `outputs/figures/fig_08_depeg_event_study.png`.  
**Owner:** Codex.

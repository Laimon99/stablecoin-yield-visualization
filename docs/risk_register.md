# Risk Register

Final review date: 2026-07-08.

| ID | Risk | Likelihood | Impact | Mitigation | Residual status |
| --- | --- | --- | --- | --- | --- |
| R-001 | APY semantics differ across protocols or are not fully documented by provider. | Medium | High | Preserve source APY fields; avoid realized-return claims; report APY as quoted annualized APY. | Mitigated with caveat |
| R-002 | Base/reward APY missing for many pools. | High | Medium | Quantify coverage in quality/report; interpret component figures only where provider fields exist. | Mitigated with caveat |
| R-003 | Stablecoin/pool entity resolution ambiguous due to ticker collisions and bridged assets. | Medium | High | Preferred-symbol overrides, confidence fields, manual review flags, `docs/entity_resolution.md`. | Mitigated with caveat |
| R-004 | CoinGecko public API rate limits or key requirements restrict price history. | Medium | Medium | Use DeFiLlama stablecoin prices as primary price context; CoinGecko as small fallback/check. | Mitigated |
| R-005 | TVL change misinterpreted as capital flow. | Medium | High | Use "observed TVL proxy" language throughout figures/report/slides. | Mitigated |
| R-006 | Depeg events not well represented in selected pool window. | Medium | Medium | Prefer reviewed USDC/DAI March 2023 stress windows when present and require observed exposed pools. | Mitigated |
| R-007 | Full live collection is slow due to per-pool history endpoints. | Medium | Medium | Incremental raw caching, sample mode, full limit of 250 pools. | Mitigated |
| R-008 | Final report/deck rendering dependency fails on clean Windows environment. | Low | Medium | Report uses ReportLab in project dependencies; deck builder locates Codex `@oai/artifact-tool` or accepts `ARTIFACT_TOOL_PACKAGE_DIR`. | Mitigated with environment caveat |
| R-009 | Course audio contains additional requirements not present in readable materials. | Low | Medium | Document ASR limitation; base requirements on PDFs/images/examples. | Accepted |
| R-010 | Visuals become dashboard-like rather than narrative. | Medium | Medium | Figure registry, storyboard, report structure and 11-slide narrative deck. | Mitigated |

The remaining caveats are explicitly described in `docs/limitations_ethics.md`, `outputs/report/stablecoin_yield_report.md` and slide speaker notes.

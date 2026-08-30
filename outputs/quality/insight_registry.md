# Insight Registry

Analytical sample pools: 250.0

## I-001

**Question:** RQ1 Persistence

**Claim:** High-yield episodes are finite observed regimes, not permanent pool traits.

**Population:** Stablecoin pools in the analytical sample

**Metric:** Median duration of APY >= 10 percent episodes

**Estimate:** 2.0 days across 2668 episodes

**Uncertainty:** Kaplan-Meier confidence intervals in survival table

**Figure/table:** episode_survival, yield_episodes

**Robustness:** Checked at 5, 10 and 20 percent thresholds

**Alternative explanation:** Provider APY methodology and missing periods can affect episode boundaries

**Limitations:** APY is quoted annualized APY, not realized return

**Status:** validated

## I-002

**Question:** RQ3 Ranking stability

**Claim:** Top-yield membership changes materially over observation horizons.

**Population:** Daily top-k stablecoin pools

**Metric:** Comparison-weighted average top-k churn

**Estimate:** {"1": 0.135, "7": 0.236, "30": 0.333}

**Uncertainty:** Distribution over dates retained in ranking_churn table

**Figure/table:** ranking_churn

**Robustness:** Top 10 and top 20, horizons 1/7/30 days

**Alternative explanation:** Small APY differences around the threshold may reshuffle ranks

**Limitations:** Not a measure of investment opportunity

**Status:** validated

## I-003

**Question:** RQ5 Risk frontier

**Claim:** Only a subset of pools combine above-median APY, persistence and TVL.

**Population:** Pools with analytical history

**Metric:** Frontier candidate share

**Estimate:** 15.2% of 250 pools

**Uncertainty:** Depends on sample and median thresholds

**Figure/table:** yield_frontier

**Robustness:** No hidden score; components shown directly

**Alternative explanation:** Selection favors pools with sufficient history and TVL

**Limitations:** Does not fully measure smart contract or legal risk

**Status:** validated


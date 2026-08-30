# Stablecoin Yield

**Project title:** The Price of Yield: Persistence, Mechanisms and TVL Response in Stablecoin DeFi

**Pipeline mode:** `full`

## Abstract

This project studies stablecoin-denominated DeFi yield as an observed data visualization problem, not as an investment ranking. The analysis combines DeFiLlama yield histories, DeFiLlama stablecoin price context, CoinGecko fallback checks and documented protocol classifications into a canonical pool-day panel. The core question is whether high APY is persistent once duration, TVL, reward dependence, stablecoin peg stress and pool mechanism are shown together.

The full panel covers 250 pools, 137,095 pool-days, 25 chains and 84 protocols from 2022-02-11 to 2026-07-08. The pool-day median APY is 4.29 percent, while the pool-day mean is 8.03 percent, indicating a heavy-tailed yield distribution.

## Research Questions

1. How long do high-yield regimes last for stablecoin pools?
2. Which yield components and pool mechanisms explain headline APY?
3. How stable are top-yield memberships over one-day, seven-day and thirty-day horizons?
4. How do peg-stress windows change the interpretation of nominal APY?
5. Which pools clear transparent APY, persistence and capacity thresholds simultaneously?

## Data Sources

| source                 | endpoint                                                          | role                                           | auth              | evidence                                                   |
|:-----------------------|:------------------------------------------------------------------|:-----------------------------------------------|:------------------|:-----------------------------------------------------------|
| DeFiLlama yields       | yields.llama.fi/pools and /chart/{pool}                           | Pool universe, APY components, TVL and history | No key            | 15,669 live pools observed; 250 selected for full analysis |
| DeFiLlama stablecoins  | stablecoins.llama.fi/stablecoins and /stablecoinprices            | Stablecoin metadata and peg-price context      | No key            | 404 assets and 2,012 price date records verified           |
| CoinGecko Demo         | coins/markets                                                     | Fallback checks for selected stablecoins       | Optional demo key | Keyless sample returned 3 assets on 2026-07-08             |
| Protocol documentation | Aave, Compound, Curve, Yearn, Sky/Maker, Ethena and selected docs | Mechanism labels and caveats                   | No key            | Classification is metadata, not a safety rating            |

## Data Pipeline And Canonical Schema

Raw API responses are stored as request envelopes with payload checksums under `data/raw/`. The pipeline then builds canonical pool, stablecoin, protocol, yield mechanism and risk-event tables before producing the pool-day analytical panel.

| asset                 |   rows | role                | path                                     |
|:----------------------|-------:|:--------------------|:-----------------------------------------|
| raw request envelopes |    254 | Raw provenance      | data/raw/manifest.jsonl                  |
| pools                 |    250 | Canonical entities  | data/processed/pools.parquet             |
| pool snapshots        | 137095 | Clean observations  | data/processed/pool_snapshots.parquet    |
| stablecoins           |    394 | Stablecoin metadata | data/processed/stablecoins.parquet       |
| stablecoin prices     | 176176 | Peg context         | data/processed/stablecoin_prices.parquet |
| risk events           |   7763 | Event context       | data/processed/risk_events.parquet       |
| pool-day panel        | 137095 | Analysis grain      | data/analytical/pool_day_panel.parquet   |
| yield episodes        |   9490 | Episode analysis    | data/analytical/yield_episodes.parquet   |
| pool metrics          |    250 | Pool summaries      | data/analytical/pool_metrics.parquet     |

## Data Quality

The quality suite ran 12 checks with 0 critical failures and 2 warning checks. Warning rows are retained and documented rather than hidden.

| check_id                          | severity   | status   |   evaluated_rows |   failed_rows |   failure_rate |
|:----------------------------------|:-----------|:---------|-----------------:|--------------:|---------------:|
| panel.exists                      | critical   | passed   |           137095 |             0 |    0           |
| pool_day.unique_key               | critical   | passed   |           137095 |             0 |    0           |
| pool_day.apy_total.completeness   | error      | passed   |           137095 |             0 |    0           |
| pool_day.tvl_usd.completeness     | warning    | warning  |           137095 |            26 |    0.00018965  |
| pool_day.chain.completeness       | warning    | passed   |           137095 |             0 |    0           |
| pool_day.protocol_id.completeness | warning    | passed   |           137095 |             0 |    0           |
| pool_day.pool_type.completeness   | warning    | passed   |           137095 |             0 |    0           |
| apy.non_negative                  | error      | passed   |           137095 |             0 |    0           |
| apy.extreme_gt_1000               | warning    | warning  |           137095 |            32 |    0.000233415 |
| tvl.positive                      | error      | passed   |           137095 |             0 |    0           |
| apy.total_vs_components           | warning    | passed   |           137095 |             0 |    0           |
| entity_resolution.low_confidence  | warning    | passed   |              250 |             0 |    0           |

## Methodology

High-yield episodes use the main threshold APY >= 10 percent. Episodes are continuous runs above the threshold and active episodes at the final observation are treated as censored in the Kaplan-Meier survival calculation.

Ranking churn compares top-k APY sets across one-day, seven-day and thirty-day horizons. TVL response is an observational event-time proxy, not a direct measure of wallet-level capital flow. The joint screen marks pools above the pool-level sample medians for APY, persistence and TVL without constructing a score or claiming a Pareto frontier.

## Main Results

The main APY >= 10 percent rule detects 2,668 episodes. The median duration is 2.0 days and the 90th percentile duration is 16.0 days.

Comparison-weighted average top-yield churn rises from 13.5% at one day to 23.6% at seven days and 33.3% at thirty days.

38 of 250 pools (15.2%) sit above the pool-level sample medians for APY, persistence and TVL. The APY threshold is 4.47 percent, distinct from the 4.29 percent pool-day median.

### Pool Type Metrics

| pool_type                |   pools |   median_apy |   median_tvl_usd |   median_persistence |
|:-------------------------|--------:|-------------:|-----------------:|---------------------:|
| single_stable_lending    |     108 |         4.7  |      2.11842e+07 |                0.058 |
| incentive_driven         |      90 |         5.35 |      1.40661e+07 |                0.135 |
| stable_stable_lp         |      25 |         0.42 |      1.76482e+07 |                0.002 |
| yield_bearing_stablecoin |      19 |         2.98 |      4.28419e+07 |                0.002 |
| vault_aggregator         |       8 |         5.59 |      3.20717e+06 |                0.233 |

### Archetypes

| label       |   count |
|:------------|--------:|
| archetype_1 |     138 |
| archetype_3 |      61 |
| archetype_2 |      48 |
| archetype_4 |       3 |

## Peg Stress And Event Response

The selected peg-stress case is `usd_coin` on 2023-03-12. The minimum observed price is 0.9611 USD. APY and TVL response are read as observed context, not causal estimates.

Event response checkpoints: {"-7": {"median_apy": 6.53, "median_tvl_index": 1.001, "event_count": 395}, "0": {"median_apy": 18.24, "median_tvl_index": 1.0, "event_count": 453}, "7": {"median_apy": 9.93, "median_tvl_index": 1.233, "event_count": 449}, "30": {"median_apy": 8.33, "median_tvl_index": 1.694, "event_count": 441}}

## Robustness Checks

| check            | family          |   pool_count |   panel_rows |   threshold_percent |   max_gap_days |   episode_count |   median_duration_days |   censored_share |   median_apy |   mean_apy |
|:-----------------|:----------------|-------------:|-------------:|--------------------:|---------------:|----------------:|-----------------------:|-----------------:|-------------:|-----------:|
| threshold_5      | apy_threshold   |          250 |       137095 |                   5 |              1 |            3688 |                      2 |       0.027115   |      4.28701 |    8.02876 |
| threshold_10     | apy_threshold   |          250 |       137095 |                  10 |              1 |            2668 |                      2 |       0.011994   |      4.28701 |    8.02876 |
| threshold_20     | apy_threshold   |          250 |       137095 |                  20 |              1 |             964 |                      2 |       0.00829876 |      4.28701 |    8.02876 |
| min_tvl_500000   | minimum_tvl     |          250 |       132699 |                  10 |              1 |            2536 |                      2 |       0.0126183  |      4.28327 |    7.96051 |
| min_tvl_1000000  | minimum_tvl     |          250 |       130069 |                  10 |              1 |            2470 |                      2 |       0.0129555  |      4.24573 |    7.83331 |
| min_tvl_5000000  | minimum_tvl     |          235 |       111512 |                  10 |              1 |            1758 |                      2 |       0.0108077  |      3.85102 |    6.85193 |
| min_history_90   | minimum_history |          250 |       137095 |                  10 |              1 |            2668 |                      2 |       0.011994   |      4.28701 |    8.02876 |
| min_history_180  | minimum_history |          250 |       137095 |                  10 |              1 |            2668 |                      2 |       0.011994   |      4.28701 |    8.02876 |
| min_history_365  | minimum_history |          141 |       108155 |                  10 |              1 |            1919 |                      2 |       0.00677436 |      4.06    |    6.28227 |
| max_gap_0        | episode_gap     |          250 |       137095 |                  10 |              0 |            2683 |                      2 |       0.0119269  |      4.28701 |    8.02876 |
| max_gap_1        | episode_gap     |          250 |       137095 |                  10 |              1 |            2668 |                      2 |       0.011994   |      4.28701 |    8.02876 |
| max_gap_3        | episode_gap     |          250 |       137095 |                  10 |              3 |            2646 |                      2 |       0.0120937  |      4.28701 |    8.02876 |
| winsor_0.01_0.99 | winsorization   |          250 |       137095 |                  10 |              1 |            2668 |                      2 |       0.011994   |      4.28701 |    6.03916 |

## Visual Evidence

### Yield universe

![Yield universe: APY comparisons need category and capacity context](outputs/figures/fig_01_yield_universe.png)

**Question:** What is the observed stablecoin yield universe?  
**Message:** The sample covers multiple pool types and chains, so APY should not be compared without stratification.  
**Sample:** pools=250, pool-days=137095

### APY distribution

![Headline APY is heavy-tailed, so medians matter](outputs/figures/fig_02_apy_distribution.png)

**Question:** How are APY observations distributed?  
**Message:** A small number of extreme APY observations pulls the mean above the median.  
**Sample:** pool-days=137095

### Episode survival

![Most high-yield episodes fade quickly in the observed sample](outputs/figures/fig_03_episode_survival.png)

**Question:** How long do APY >= 10 percent episodes last?  
**Message:** Kaplan-Meier survival declines steeply at short durations, with censored active episodes retained.  
**Sample:** episodes=2668

### Ranking churn

![Top-yield membership changes as the horizon widens](outputs/figures/fig_04_ranking_churn.png)

**Question:** How stable are top-yield rankings?  
**Message:** Heatmap cells show separate top-k means; pooled text summaries weight each valid observed-date/top-k comparison equally.  
**Sample:** date comparisons=7938

### APY and TVL event response

![After APY jumps, yield and TVL move on different clocks](outputs/figures/fig_07_apy_tvl_relationship.png)

**Question:** Are APY jumps followed by TVL changes and compression?  
**Message:** Event-time patterns are observational and use TVL change only as a proxy.  
**Sample:** event-time rows=38

### Peg-stress context

![Peg stress changes the denominator behind nominal yield](outputs/figures/fig_08_depeg_event_study.png)

**Question:** How do APY and price behave around stablecoin peg stress?  
**Message:** A depeg window makes nominal APY harder to interpret without price context.  
**Sample:** event-window rows=61

### Pool archetypes

![Pool archetypes separate yield level, persistence and capacity](outputs/figures/fig_09_pool_archetypes.png)

**Question:** Do pools cluster into interpretable profiles?  
**Message:** Exploratory clusters summarize patterns but are not labels of safety or quality.  
**Sample:** pools=250

### Hero joint screen

![High yield is common; persistent high yield with capacity is rarer](outputs/figures/fig_10_hero_yield_frontier.png)

**Question:** Which pools combine APY, persistence and TVL?  
**Message:** Only a subset sits above median APY, persistence and TVL simultaneously; this is a joint threshold screen, not a recommendation.  
**Sample:** pools=250


## Limitations And Ethics

APY is quoted annualized APY, not realized return. TVL change is an observed balance proxy, not direct capital flow. Protocol risk, smart contract risk, legal risk and user-specific costs are not fully measured. The project intentionally avoids recommendations, portfolio advice and a universal pool ranking.

## Technical Appendix

Run `uv sync --extra dev` and then `uv run python scripts/reproduce_all.py --mode sample` for a local reproducibility check. Run with `--mode full` to refresh live data within public API limits. The final manifest is written to `outputs/release_manifest.json`.

## References

- DeFiLlama API documentation: https://api-docs.defillama.com/llms-free.txt
- DeFiLlama yields live host: https://yields.llama.fi
- DeFiLlama stablecoins live host: https://stablecoins.llama.fi
- CoinGecko Demo API documentation: https://docs.coingecko.com/demo/reference/coins-markets
- Course requirements and notes under `docs/Project/`, `docs/Slide/` and `docs/data_visualization_notes.pdf`.

# Oral Defense Preparation

Each answer follows: Direct answer, Evidence, Method, Limitation, Implication. Final metrics refer to the full pipeline output generated on 2026-07-08.

## What is the main finding?

Direct answer: High stablecoin yield is common in snapshots, but persistent high yield with capacity and interpretable risk context is rarer.

Evidence: The full panel has 250 pools and 137,095 pool-days. Across pool-day observations, median APY is 4.29 percent and mean APY is 8.03 percent. The joint screen instead uses the 4.47 percent median of pool-level median APYs; 38 of 250 pools, or 15.2 percent, clear all three pool-level thresholds.

Method: Pool-day panel, pool-level metrics, survival analysis and a joint threshold screen.

Limitation: The joint screen is descriptive and does not fully measure smart-contract, legal, bridge or counterparty risk.

Implication: The appropriate visual answer is a joint threshold screen, not a pool ranking or Pareto frontier.

## How were the 250 pools selected?

Direct answer: The project uses a deliberate analytical sample, not a random market sample.

Evidence: Eligible pools are stablecoin pools with at least USD 1 million TVL and 180 provider history observations. The final unbalanced panel spans 2022-02-11 to 2026-07-08 and contributes a median of 411 observed days per pool.

Method: Seventy percent of the 250-pool cap is allocated to the highest-TVL eligible pools and the remaining capacity to the highest-current-APY eligible pools, with deterministic TVL-ranked fill after deduplication.

Limitation: The selection intentionally emphasizes capacity and yield extremes, so it is not statistically representative of the full DeFi pool universe.

Implication: Results apply to the selected analytical universe and should not be generalized as population estimates.

## Is APY realized return?

Direct answer: No. APY is a quoted annualized source value, not realized investor return.

Evidence: DeFiLlama reports APY fields at pool-day level; no investor wallet path or compounding path is reconstructed.

Method: The project studies APY level, duration, components and changes over time.

Limitation: It excludes gas, slippage, compounding behavior, reward-token liquidation and tax treatment.

Implication: Results describe offered yield regimes, not investment performance.

## How long do high-yield episodes last?

Direct answer: In the full dataset, episodes under the main 10 percent APY specification are usually short.

Evidence: The analysis detects all 2,668 contiguous episodes under that specification and the median duration is 2.0 days; it does not select one primary episode per pool.

Method: Episodes are contiguous pool-day runs above 10 percent APY with one-day maximum gap; active episodes are censored and included in Kaplan-Meier survival.

Limitation: Provider APY methodology and missing dates can affect boundaries.

Implication: A high APY snapshot is a weak proxy for a durable yield opportunity.

## Why not create a ranking?

Direct answer: A ranking would hide duration, capacity, reward dependence and peg context.

Evidence: Comparison-weighted average top-yield churn rises by horizon: 13.5 percent at one day, 23.6 percent at seven days and 33.3 percent at thirty days.

Method: Daily top-k sets are compared across horizons; churn is `1 - retention`. Heatmap cells are separate top-10 and top-20 means. The headline values pool valid observed-date/top-k comparisons, so they are weighted by the available comparison counts rather than being a simple mean of the two rounded cells.

Limitation: Churn is sensitive to close APY values around rank thresholds.

Implication: The hero visualization is a joint threshold screen, not a leaderboard.

## Is TVL change capital flow?

Direct answer: No. It is an observed TVL proxy.

Evidence: Across 453 APY-jump events, median APY falls from 18.24 percent on event day to 8.33 percent by day 30, while the median normalized TVL index reaches 1.69.

Method: The event study normalizes TVL within each event before aggregating.

Limitation: Wallet-level deposits and withdrawals are not reconstructed.

Implication: Claims are phrased as associations, not causal capital-flow statements.

## Why was USDC March 2023 selected for depeg context?

Direct answer: It is a reviewed historical peg-stress event that is present in the source data and has observed exposed pools.

Evidence: `outputs/tables/depeg_event_study.csv` selects USDC on 2023-03-12 with peak absolute deviation 0.0389 and up to 10 exposed pools. Median exposed-pool APY rises from 2.39 percent on day -1 to 3.77 percent on day 0, a descriptive increase of 1.38 percentage points.

Method: The selector prefers reviewed USDC/DAI March 2023 stress windows before raw maximum deviations, then falls back to bounded deviations if needed.

Limitation: This is a case study, not a complete causal estimate of all depeg effects.

Implication: The figure gives price context for nominal APY without over-weighting unreviewed source outliers.

## What are the main data-quality warnings?

Direct answer: No critical quality checks fail; two warning categories remain.

Evidence: Full quality report shows 26 missing TVL values and 32 APY observations above 1000 percent.

Method: Warnings are retained and reported rather than silently dropped.

Limitation: Extreme APY can be a true short-lived incentive or a provider artifact.

Implication: The report uses medians and flags heavy tails explicitly.

## Is the short-duration result robust?

Direct answer: Yes within the configured sensitivity checks.

Evidence: Median episode duration remains 2 days at 5, 10 and 20 percent APY thresholds. Episode counts change from 3,688 to 2,668 and 964 as the threshold rises.

Method: The pipeline materializes 13 checks across five families: APY threshold, minimum TVL, minimum history, allowed episode gaps and p1-p99 winsorization.

Limitation: Robustness to observed specifications does not solve provider dependence or convert quoted APY into realized return.

Implication: The claim is about short observed regimes, not a precise causal law or forecast.

## What makes the project reproducible?

Direct answer: The full pipeline is executable from raw collection through final report, presentation and manifest.

Evidence: `uv run python scripts/reproduce_all.py --mode full` completed with `fetched_charts=0` from cached raw data and generated `outputs/release_manifest.json`.

Method: Raw request envelopes include checksums; transformation, analysis, figure, report and deck builders are versioned.

Limitation: Live refresh still depends on public API availability and rate limits; the final deck builder expects Codex `@oai/artifact-tool` or `ARTIFACT_TOOL_PACKAGE_DIR`.

Implication: The project can be audited and rerun without manually editing tables, figures or slides.

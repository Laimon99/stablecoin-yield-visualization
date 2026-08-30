# Methodology

## Analytical Grain

The project uses a pool-day panel. Each row represents one DeFi pool on one UTC day with APY, TVL, chain, protocol, pool type and stablecoin exposure fields.

Distribution summaries such as the 4.29 percent median APY are calculated across pool-day observations. The joint threshold screen first summarizes each pool across time and then uses the median of those 250 pool-level APY values, 4.47 percent. The two medians therefore answer different questions and are not interchangeable.

## Population

The full analytical panel spans 2022-02-11 to 2026-07-08. Eligible DeFiLlama pools must be flagged as stablecoin pools, report at least USD 1 million TVL and expose at least 180 provider history observations. The 250-pool full-mode cap is deterministic: 70% of capacity is allocated to the highest-TVL eligible pools and the remaining capacity to the highest-current-APY eligible pools, followed by a TVL-ranked fill if deduplication leaves open slots. This is a deliberate analytical sample, not a random or market-representative sample.

The panel is unbalanced. Pools contribute only dates observed by the provider between their first and last records; entry and exit are retained and no synthetic historical backfill is created. The selected pools contribute a median of 411 observed days, with 181 to 1,609 observed days across pools.

## High-Yield Episodes

The primary definition is `apy_total >= 10%`. An episode starts when a pool crosses the threshold and ends when it falls below the threshold or when the time gap exceeds the configured maximum gap. Episodes still active at the final observation are marked censored and included in Kaplan-Meier survival analysis.

The configured maximum gap is one missing calendar day. A two-day date difference can therefore remain inside one episode; a larger gap breaks it. Robustness checks cover five families: APY thresholds at 5%, 10% and 20%; minimum TVL at USD 0.5 million, 1 million and 5 million; minimum history at 90, 180 and 365 days; maximum episode gaps of 0, 1 and 3 days; and APY winsorization from p1 to p99.

## Ranking Churn

For each date, pools are ranked by `apy_total`. Top-k sets are compared across 1-day, 7-day and 30-day horizons. Retention is the intersection share of two top-k sets; churn is `1 - retention`. Heatmap cells report the mean separately for top-10 and top-20 sets. The headline values pool all valid observed-date/top-k comparisons and therefore weight each top-k cell by its number of valid date comparisons: 2,669 at 1 day, 2,657 at 7 days and 2,612 at 30 days. The result is a stability diagnostic, not an investment ranking.

## APY And TVL Event Response

APY jump events are defined as a one-day APY increase of at least 5 percentage points with current APY at least 10%. For each event, the panel is aligned from 7 days before to 30 days after the event. TVL is normalized within each event before aggregation, so the event-time curve shows a median index rather than a raw dollar-weighted series.

The event response is observational. TVL can change because of capital movement, price movement, accounting changes, migrations or source reporting changes.

## Depeg Event Study

Stablecoin prices are scanned for major exposed stablecoins. The selected peg-stress event must have both a price deviation and at least one observed exposed pool in the +/-30 day panel window. The figure shows price and median exposed-pool APY around the selected event.

## Joint Threshold Screen

The hero visualization plots pool-level median APY, persistence above the main 10 percent threshold and pool-level median TVL. Joint-screen candidates are pools above the pool-level sample median on all three dimensions. This is a transparent descriptive filter, not a Pareto frontier, hidden score or recommendation.

## Archetypes

Pool archetypes are generated with standardized pool-level features and k-means clustering when the sample is large enough. These labels are exploratory summaries and are not safety ratings.

## Responsible Interpretation

APY is quoted annualized APY, not realized return. The analysis excludes individual wallet paths, gas, slippage, reward liquidation, tax treatment and legal suitability. All outputs are educational visual analytics only.

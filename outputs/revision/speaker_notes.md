# Speaker notes

## Slide 1

Open with the precise scope: persistence, mechanisms and observed TVL response. State that this is not a protocol-risk model or a recommendation list.

## Slide 2

State the five research questions and the decision to use pool-day as the analytical grain.

## Slide 3

Explain the eligibility rules: stablecoin flag, at least USD 1 million TVL and 180 history observations. The 250-pool cap combines 70 percent highest TVL with the remaining capacity highest APY.

## Slide 4

Define the main 10% episode specification, one-missing-day tolerance, right censoring, churn formula, APY-jump event trigger and the three-median joint screen. Emphasize that the screen is not a Pareto frontier.

## Slide 5

Use the p99 display cap and preserved extreme-value flags to justify robust summaries without deleting source observations.

## Slide 6

Explain Kaplan-Meier survival and right censoring. Report 2,668 episodes, median 2 days, p90 16 days and 1.2 percent censored.

## Slide 7

Define churn as one minus top-k retention. The heatmap cells are separate top-10 and top-20 date means. The text summary pools all valid observed-date/top-k comparisons, so it is weighted by their counts: 2,669 at 1 day, 2,657 at 7 days and 2,612 at 30 days.

## Slide 8

Use the chart. Contrast incentive-driven pools with base-yield categories and report 90.3 percent base coverage versus 61.6 percent reward coverage.

## Slide 9

Describe the event trigger and show the four event-time points. State immediately that TVL is an observational balance-sheet proxy, not a causal wallet-flow estimate.

## Slide 10

Report the selected reviewed event, the 10-pool exposure window and the descriptive APY change. Do not generalize one event into a causal risk estimate.

## Slide 11

Call this a joint threshold screen, not a Pareto frontier. Bubble size encodes median TVL; highlighted points clear all three medians.

## Slide 12

Show that episode counts change with the threshold but the median duration does not. Mention all five robustness families materialized by the pipeline.

## Slide 13

Name the unmeasured dimensions: smart-contract, counterparty, bridge, chain, oracle, liquidity and collateral quality. This boundary is why the project avoids recommendations.

## Slide 14

The interval is the existing lifelines 95% pointwise log-log confidence interval. It is not simultaneous and is not clustered by pool. S(30) means probability of an observed episode lasting more than 30 calendar days. Left-boundary episodes can be incomplete, and the original specification treats long observation gaps as episode endings rather than known economic failures. Gap sensitivity is reassuring for the observed median but does not establish non-informative censoring. The history-90 check operates within a sample already selected for at least 180 provider observations. Sources: outputs/tables/episode_survival.csv, outputs/tables/robustness_checks.csv, src/stablecoin_yield/metrics/episodes.py, docs/methodology.md.

## Slide 15

The PDF includes the actual Plotly heatmap on page 7 and Matplotlib plots on pages 6, 9 and 10. No live demonstration is needed. The two distinct visualization libraries are Matplotlib and Plotly; Seaborn is documented as supporting Matplotlib, not counted as an independent rendering system. Matplotlib code: src/stablecoin_yield/visualization/figures.py. Plotly code: scripts/reproduce_published.py. Presentation charts are assembled separately by @oai/artifact-tool. Versions are locked in uv.lock and recorded in outputs/revision/published_evidence_audit.json. Repository: https://github.com/Laimon99/stablecoin-yield-visualization

## Slide 16

Repository URL: https://github.com/Laimon99/stablecoin-yield-visualization . Exact package versions: uv.lock. Published evidence reconstruction needs only the aggregate CSVs and report_summary.json. This is computational verification of published statistics, not independent reconstruction from the historical raw data. Full live collection can return a changed sample and provider revisions. PowerPoint rebuilding is optional and requires @oai/artifact-tool; rendered deliverables remain accessible without it. Code licence: MIT, https://opensource.org/license/mit . Original authored presentation/report/text: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Third-party data excluded. DeFiLlama: https://defillama.com/terms . CoinGecko: https://www.coingecko.com/en/api_terms .

## Slide 17

Close with the one-sentence defense, reproducibility and the no-financial-advice boundary.
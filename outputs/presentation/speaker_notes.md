# Speaker Notes

## Slide 1: Stablecoin Yield

Open with the precise scope: persistence, mechanisms and observed TVL response. State that this is not a protocol-risk model or a recommendation list.

## Slide 2: Research Frame

State the five research questions and the decision to use pool-day as the analytical grain.

## Slide 3: A Deliberate Analytical Sample

Explain the eligibility rules: stablecoin flag, at least USD 1 million TVL and 180 history observations. The 250-pool cap combines 70 percent highest TVL with the remaining capacity highest APY.

## Slide 4: Auditable Definitions

Define the main 10% episode specification, one-missing-day tolerance, right censoring, churn formula, APY-jump event trigger and the three-median joint screen. Emphasize that the screen is not a Pareto frontier.

## Slide 5: APY Is Heavy Tailed

Use the p99 display cap and preserved extreme-value flags to justify robust summaries without deleting source observations.

## Slide 6: High Yield Is Usually Short

Explain Kaplan-Meier survival and right censoring. Report 2,668 episodes, median 2 days, p90 16 days and 1.2 percent censored.

## Slide 7: Rankings Lose Members Over Time

Define churn as one minus top-k retention. The heatmap cells are separate top-10 and top-20 date means. The text summary pools all valid observed-date/top-k comparisons, so it is weighted by their counts: 2,669 at 1 day, 2,657 at 7 days and 2,612 at 30 days.

## Slide 8: Mechanism Changes What APY Means

Use the native chart. Contrast incentive-driven pools with base-yield categories and report 90.3 percent base coverage versus 61.6 percent reward coverage.

## Slide 9: APY Falls Faster Than TVL Responds

Describe the event trigger and show the four event-time points. State immediately that TVL is an observational balance-sheet proxy, not a causal wallet-flow estimate.

## Slide 10: Peg Stress Changes the Yield Denominator

Report the selected reviewed event, the 10-pool exposure window and the descriptive APY change. Do not generalize one event into a causal risk estimate.

## Slide 11: Few Pools Clear All Three Thresholds

Call this a joint threshold screen, not a Pareto frontier. Bubble size encodes median TVL; highlighted points clear all three medians.

## Slide 12: The Main Duration Result Is Robust

Show that episode counts change with the threshold but the median duration does not. Mention all five robustness families materialized by the pipeline.

## Slide 13: This Is Market Context, Not Total Risk

Name the unmeasured dimensions: smart-contract, counterparty, bridge, chain, oracle, liquidity and collateral quality. This boundary is why the project avoids recommendations.

## Slide 14: Conclusion

Close with the one-sentence defense, reproducibility and the no-financial-advice boundary.

# Limitations and Ethics

## Responsible Scope

This project is educational and analytical. It does not recommend pools, protocols, stablecoins or investment strategies.

## APY Interpretation

APY is a quoted annualized value reported by data providers. It is not realized investor return. Realized return would require transaction-level deposits, withdrawals, compounding, fees, slippage, reward-token conversion and stablecoin price path.

## TVL Interpretation

Observed TVL change is not equivalent to net capital flow. It may include deposits, withdrawals, price changes, oracle/reporting changes, protocol accounting changes and pool migrations.

## Source Dependence

The project depends primarily on DeFiLlama yield data. Provider methodology, backfills, revisions and field definitions may affect results.

Raw provider payloads and row-level generated datasets are not included in the public repository.
This respects current redistribution restrictions and means that a fresh public run reproduces
the method against then-current data rather than the exact private 2026-07-08 snapshot.

## Stablecoin Risk

Stablecoin depeg analysis uses observed price deviations from selected sources. It does not fully measure counterparty risk, legal risk, collateral quality, smart-contract risk or redemption constraints.

## Protocol Risk

Protocol mechanism classification is descriptive, not a safety rating. Audits or documentation references do not imply security.

## Entity Resolution

Ticker-based identification is insufficient. The project uses mapping, confidence and manual review, but ambiguous bridged assets, renamed pools and migrated pools may remain.

## Missing Data

Missing base/reward APY, missing stablecoin mappings or missing historical observations are preserved and reported. They are not replaced with plausible values.

## Visual Ethics

Figures must avoid misleading encodings, unsupported causality, sensational APY framing and red/green-only risk language. Claims must be phrased as observed associations in the sample.

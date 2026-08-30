# Entity Resolution

## Goal

The canonical unit is a DeFi pool observed by day. Entity resolution links each pool to stablecoin entities, protocol identifiers and analytical pool types without relying on a ticker alone.

## Rules

1. Preserve the source pool ID as `source_pool_id`.
2. Build the project `pool_id` from the DeFiLlama pool ID because it is already stable and unique for the yield endpoint.
3. Parse pool symbols into candidate underlying assets.
4. Match candidate assets to DeFiLlama stablecoin IDs by exact source ID where available.
5. Use preferred-symbol overrides for common ticker collisions:
   `USDC`, `USDT`, `DAI`, `FRAX`, `FRXUSD`, `USDE`, `SUSDE`, `USDS`, `SUSDS`, `USD0`, `BUSD0`, `FXUSD`, `MSUSD`, `PMUSD`, `CRVUSD`, `EURC`.
6. Store unresolved assets as raw symbols rather than forcing a low-confidence match.
7. Mark `manual_review_required` when confidence is below 0.7 or no stablecoin entity is mapped.

## Why Overrides Are Needed

Stablecoin tickers are not globally unique. A symbol-only map can silently choose the wrong stablecoin when several DeFiLlama assets share a ticker or when a yield-bearing/wrapped form uses the same base symbol. The documented override table makes these choices auditable and keeps the depeg event study tied to actual exposed pools.

## Quality Controls

- `entity_resolution_confidence` is included in `pools`.
- `entity_resolution.low_confidence` is checked in `outputs/quality/data_quality_checks.csv`.
- The depeg regression test verifies that the selected peg-stress event has observed exposed-pool APY.
- Raw symbol fields are preserved for manual inspection.

## Limitations

Entity resolution remains imperfect for bridged assets, migrated pools and historical changes in pool composition. The current project treats pool composition as an observed interval summary, not as an intraday balance reconstruction.

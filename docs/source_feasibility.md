# Source Feasibility Report

Date: 2026-07-08.

## Summary

The project is feasible using public, live data. DeFiLlama yields provides the core pool universe and per-pool history. DeFiLlama stablecoins provides stablecoin metadata and price context. CoinGecko provides fallback/enrichment for selected stablecoin prices and reward-token metadata, but full historical use may require a demo/pro key because the public Demo API historical chart is documented as restricted to the past 365 days.

## Live Request Evidence

| Source | Endpoint | Status | Observed rows | Minimum fields verified |
| --- | --- | --- | ---: | --- |
| DeFiLlama yields | `/pools` | 200 | 15,669 pools | `chain`, `project`, `symbol`, `tvlUsd`, `apyBase`, `apyReward`, `apy`, `pool`, `stablecoin`, `count`, `outlier`, `underlyingTokens` |
| DeFiLlama yields | `/chart/{pool}` | 200 | 503 observations for Sky Lending SUSDS | `timestamp`, `tvlUsd`, `apy`, `apyBase`, `apyReward`, `pricePerShare` |
| DeFiLlama stablecoins | `/stablecoins` | 200 | 404 assets | `id`, `name`, `symbol`, `gecko_id`, `pegType`, `pegMechanism`, `chains`, `price` |
| DeFiLlama stablecoins | `/stablecoinprices` | 200 | 2,012 date records | `date`, `prices` |
| CoinGecko | `/coins/markets` | 200 | 3 assets in keyless sample | `id`, `symbol`, `name`, `current_price`, `market_cap`, `last_updated` |

## Feasibility Checks

- Critical variable `apy` is available in current pool and historical chart responses.
- `apyBase` and `apyReward` are available but can be null, so coverage must be measured.
- Critical variable `tvlUsd` is available in current and historical chart responses.
- Pool IDs are UUID-like and available as `pool`.
- A live filter found 489 stablecoin candidates with TVL greater than USD 1M and at least 180 historical observations, above the target minimum of 100.
- Stablecoin metadata has enough fields for initial design classification, but manual review remains required for top pools and yield-bearing/bridged assets.

## Documentation Findings

- DeFiLlama official `llms-free.txt` states the Free API requires no authentication and the Pro API is separate and paid for higher limits.
- The same file documents `/pools` and `/chart/{pool}` under Yields & APY, and `/stablecoins` plus `/stablecoinprices` under Stablecoins.
- A discrepancy was observed: `api.llama.fi/pools` and related paths returned 404, while `yields.llama.fi` and `stablecoins.llama.fi` returned 200. This is recorded as a source risk, and the adapter keeps base URLs configurable.
- CoinGecko official Markdown docs state `/coins/markets` supports up to 250 IDs per request and has 60-second cache/update frequency for Demo/Keyless. The market chart endpoint is documented as Demo-limited to the past 365 days.

## Gate Decision

G1 passes for the core project. No human input is required for the sample and main DeFiLlama-based analysis. A CoinGecko API key may improve full historical price fallback, but it is not required to proceed because DeFiLlama stablecoin prices are available and CoinGecko is fallback/enrichment.


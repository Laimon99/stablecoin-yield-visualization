# Source Registry

Last updated: 2026-08-30.

This registry records the verified sources used by the final full pipeline.

## Public Redistribution Policy

The public repository does not include raw API responses or row-level canonical datasets.
DeFiLlama's current terms prohibit republication without permission, while CoinGecko's API terms
restrict copying, storing and redistributing raw data without an appropriate licence. Local runs
write responses under the Git-ignored `data/` directory. The portfolio retains authored code,
methodology, aggregate analytical tables, figures, report and presentation with attribution.

| Source ID | Provider | Official status | Endpoint or documentation | Purpose | Auth | Rate limit | Cost | Coverage | Raw path | Fallback | Last verified | Known issues |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `defillama_yields_pools` | DeFiLlama | Official API | `https://api-docs.defillama.com/llms-free.txt`, live `https://yields.llama.fi/pools` | Current yield pool universe, pool IDs, APY, APY components, TVL, chain, project, symbol | None | Official docs: Free API no auth, standard numeric limit not published. Project cap: 60 rpm. | Free; Pro listed separately at USD 300/mo for higher rate limits | Live sample: 15,669 pools; 489 stable candidates with TVL > 1M and history count >= 180 | `data/raw/defillama_yields/` | Cached raw sample and reduced scope | 2026-07-08 | Official llms file lists `/pools` under `api.llama.fi`, but live `api.llama.fi/pools` returned 404 while `yields.llama.fi/pools` returned 200. Adapter keeps base URL configurable. Prediction fields are not used as observations. |
| `defillama_yields_chart` | DeFiLlama | Official API | `https://api-docs.defillama.com/llms-free.txt`, live `https://yields.llama.fi/chart/{pool_id}` | Historical pool-day APY and TVL | None | Same as above | Free | Live top stable pool sample: 503 observations for Sky Lending SUSDS | `data/raw/defillama_yields/` | Lower pool count, sample mode | 2026-07-08 | History length varies by pool. Timestamp is intraday and normalized to UTC day downstream. |
| `defillama_stablecoins` | DeFiLlama | Official API | `https://api-docs.defillama.com/llms-free.txt`, live `https://stablecoins.llama.fi/stablecoins` and `/stablecoinprices` | Stablecoin metadata, prices and market data context | None | Same as above | Free | Live sample: 404 stablecoin assets; 2,012 stablecoin price records | `data/raw/defillama_stablecoins/` | Manual mapping plus CoinGecko | 2026-07-08 | Official docs list `includePrices`; live endpoint accepts it. Price table includes non-USD pegs and dates requiring filtering. |
| `coingecko_markets` | CoinGecko | Official API | `https://docs.coingecko.com/demo/reference/coins-markets.md`; `https://docs.coingecko.com/demo/reference/coins-id-market-chart.md`; `https://docs.coingecko.com/docs/errors-and-rate-limits.md` | Stablecoin and reward-token price fallback/enrichment | Optional demo key via `COINGECKO_API_KEY`, sent as a non-persisted request header; keyless small request worked on 2026-07-08 | Docs: coins markets cache 60s for Demo/Keyless; max 250 IDs/request; market chart Demo historical data restricted to past 365 days; 429 on rate limit; plan determines credits | Free/demo limited; paid plan for higher/full historical access | Live keyless sample: 3 assets returned for tether, usd-coin, dai | Local `data/raw/coingecko/` | DeFiLlama stablecoin price where available | 2026-07-08 | Full historical depeg windows beyond 365 days may require API key or fallback. Raw payloads are not redistributed. |
| `protocol_docs` | Protocol teams | Official documentation pages | Aave, Compound, Curve, Yearn, Sky/Maker, Ethena and selected protocols | Yield mechanism classification and manual review | None for docs | Not applicable | Free expected | Rule-based classification applied to 250 selected pools with documented caveats | `data/raw/protocol_docs/` | Unknown mechanism category with caveat | 2026-07-08 | Static docs may not match historical mechanism changes; classification is analytical metadata, not a safety rating |

## Privately Preserved Verification Samples

The following live samples were saved locally on 2026-07-08 with request envelopes and checksums.
They are recorded for provenance but are not distributed in the public repository:

- `data/raw/defillama_yields/20260708/pools_511497a752f3.json`
- `data/raw/defillama_yields/20260708/chart_d8c4eff5-c8a9-46fc-a888-057c4c668e72_040872557220.json`
- `data/raw/defillama_stablecoins/20260708/stablecoins_845bdca3f1a6.json`
- `data/raw/defillama_stablecoins/20260708/stablecoinprices_378b23c0d6b7.json`
- `data/raw/coingecko/20260708/coins_markets_b25b1531dab2.json`

G1 feasibility result: the stablecoin project is feasible with publicly accessible APIs. The full
pipeline uses DeFiLlama as the primary source and CoinGecko as fallback/enrichment. Sample mode
reduces request volume but requires live access when no private cache is present.

## Verification Checklist

For each source before use:

1. Record official documentation URL and access date.
2. Record authentication and rate/cost limits.
3. Execute a live request.
4. Save raw envelope.
5. Compare payload with expected schema.
6. Add or update contract test.
7. Document null fields, ambiguous semantics and fallback.

# Data Sources, Attribution and Redistribution Notice

This repository contains original analysis, source code and aggregate visual outputs. It does
not distribute the raw third-party API responses or row-level canonical datasets used for the
frozen exam analysis.

## DeFiLlama

Yield-pool, APY, TVL and stablecoin context are obtained from DeFiLlama's official public APIs.

- API documentation: <https://api-docs.defillama.com/>
- Terms of use: <https://defillama.com/terms>
- Attribution: Data sourced from DeFiLlama.

The terms effective 24 June 2025 prohibit republication of data without permission. Raw
DeFiLlama responses are therefore generated only in the local ignored `data/` directory.

## CoinGecko

CoinGecko is used as a limited stablecoin-price fallback and enrichment source.

- API documentation: <https://docs.coingecko.com/>
- API terms: <https://www.coingecko.com/en/api_terms>
- Attribution: Data provided by CoinGecko, <https://www.coingecko.com/en/api>.

CoinGecko's API terms restrict copying, storing and redistributing raw data without an
appropriate licence. No CoinGecko response payload is distributed in this repository.

## Reproduction

Anyone running the pipeline is responsible for reviewing and accepting the providers' current
terms, rate limits and attribution requirements. Provider terms can change after this notice.
The code does not confer any right to access or redistribute third-party data.

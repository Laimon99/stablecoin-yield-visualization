# Data Dictionary

This file defines the canonical schema. Field-level coverage and observed ranges will be updated after G2/G3.

## `pools`

| Field | Type | Unit | Meaning | Source | Transformation | Valid range | Null meaning | Temporal semantics | Leakage risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `pool_id` | string | none | Internal stable pool identifier | Derived | Hash or stable key from source ID, chain and protocol | unique | Not allowed | Entity-level | Low |
| `source_pool_id` | string | none | Provider pool ID | DeFiLlama | Raw field | non-empty | Not allowed | Entity-level | Low |
| `protocol_id` | string | none | Canonical protocol ID | DeFiLlama, mapping | Normalized project/protocol name | non-empty | Unknown protocol | Entity-level | Low |
| `chain` | string | none | Blockchain/network | DeFiLlama | Standardized chain label | controlled vocabulary | Unknown chain | Entity-level | Low |
| `symbol_raw` | string | none | Provider pool symbol | DeFiLlama | Raw preserved | non-empty | Missing from source | Entity-level | Medium |
| `pool_type` | string | none | Analytical pool category | Mapping/docs | Rule and manual review | six categories or other | Not classified | Valid for interval | Medium |
| `stablecoin_ids` | list[string] | none | Canonical stablecoin IDs in underlying assets | Mapping | Asset parser and overrides | IDs in stablecoins table | Not resolved | Valid for interval | Medium |
| `reward_token_ids` | list[string] | none | Canonical reward token IDs | DeFiLlama/mapping | Parse reward metadata when available | IDs or raw token IDs | No rewards or unknown | Valid for interval | Medium |
| `underlying_assets` | list[string] | none | Raw/parsed underlying assets | DeFiLlama/mapping | Parsed from symbol and metadata | non-empty | Unknown assets | Valid for interval | Medium |
| `entity_resolution_confidence` | float | 0-1 | Confidence in pool-to-stablecoin mapping | Mapping | Exact ID and preferred-symbol evidence | 0 to 1 | Not evaluated | Valid for interval | Medium |
| `manual_review_required` | boolean | none | Whether pool mapping should be manually reviewed | Mapping | Confidence and unmapped asset checks | true/false | Not evaluated | Valid for interval | Medium |
| `entity_resolution_note` | string | none | Mapping note such as exact or manual symbol override | Mapping | Rule label | controlled text | Not evaluated | Valid for interval | Medium |
| `is_single_asset` | boolean | none | Whether pool has one underlying asset | Derived | Asset count | true/false | Unknown | Valid for interval | Low |
| `is_stable_only` | boolean | none | Whether underlying assets are stable/yield-bearing stable | Derived | Asset mapping | true/false | Unknown | Valid for interval | Medium |
| `first_seen_at` | datetime | UTC | First observed pool snapshot | Derived | min date | <= last_seen_at | Not observed | Observation time | Low |
| `last_seen_at` | datetime | UTC | Last observed pool snapshot | Derived | max date | >= first_seen_at | Not observed | Observation time | Low |
| `status` | string | none | observed, inactive, migrated, excluded | Derived | lifecycle rules | controlled vocabulary | Unknown | Freeze-time summary | Medium |

## `pool_snapshots`

| Field | Type | Unit | Meaning | Source | Transformation | Valid range | Null meaning | Temporal semantics | Leakage risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `pool_id` | string | none | Canonical pool ID | Derived | Join to pools | existing pool | Not allowed | Observation key | Low |
| `observed_date` | date | UTC day | Snapshot date | DeFiLlama | UTC date parse | not future | Not allowed | Observation day | Low |
| `apy_total_raw` | float | percent annualized | Raw reported total APY | DeFiLlama | Raw preserved | any finite | Source missing | As reported for day | Low |
| `apy_total` | float | percent annualized | Clean APY used in analysis | Derived | Validated/winsor optional for sensitivity | >= 0 normally | Missing or excluded | As reported for day | Medium |
| `apy_base` | float | percent annualized | Base APY component | DeFiLlama | Raw field normalized | finite | Provider missing or not applicable | As reported for day | Medium |
| `apy_reward` | float | percent annualized | Reward-token APY component | DeFiLlama | Raw field normalized | finite | Provider missing or no rewards | As reported for day | Medium |
| `tvl_usd_raw` | float | USD | Raw TVL | DeFiLlama | Raw preserved | finite | Source missing | As reported for day | Low |
| `tvl_usd` | float | USD | Clean TVL | Derived | Validated | > 0 for core analysis | Missing or excluded | As reported for day | Medium |
| `apy_outlier_flag` | boolean | none | APY flagged as anomalous | Derived | Quality rules | true/false | Not evaluated | Freeze-time quality | Low |
| `tvl_outlier_flag` | boolean | none | TVL flagged as anomalous | Derived | Quality rules | true/false | Not evaluated | Freeze-time quality | Low |
| `exclusion_reason` | string | none | Reason snapshot excluded from specific analysis | Derived | Validation rule | controlled text | Included | Analysis-specific | Medium |
| `source` | string | none | Source ID | Pipeline | Raw envelope source | controlled | Not allowed | Observation provenance | Low |
| `source_payload_id` | string | none | Raw payload checksum or request ID | Pipeline | Envelope checksum | non-empty | Not allowed | Provenance | Low |

## `stablecoins`

| Field | Type | Unit | Meaning | Source | Transformation | Valid range | Null meaning | Temporal semantics | Leakage risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `stablecoin_id` | string | none | Canonical stablecoin ID | Derived | Mapping | unique | Not allowed | Entity-level | Low |
| `name` | string | none | Asset name | DeFiLlama/CoinGecko/docs | Standardized | non-empty | Unknown | Entity-level | Low |
| `symbol` | string | none | Asset symbol | Source/mapping | Uppercase canonical | non-empty | Unknown | Entity-level | Medium |
| `design_type` | string | none | fiat-backed, crypto-collateralized, algorithmic/synthetic, yield-bearing, bridged/wrapped, other | Manual/docs | Documented classification | controlled | Unknown | Valid for interval | Medium |
| `issuer` | string | none | Issuer or protocol | Docs | Manual | text | Unknown | Entity-level | Medium |
| `peg_currency` | string | currency | Peg target | Docs/source | Manual | e.g. USD | Unknown | Entity-level | Low |
| `collateral_type` | string | none | Collateral category | Docs | Manual | controlled | Unknown | Entity-level | Medium |
| `is_yield_bearing` | boolean | none | Whether stablecoin itself accrues yield | Docs | Manual | true/false | Unknown | Valid for interval | Medium |
| `canonical_asset_id` | string | none | External ID if available | CoinGecko/DeFiLlama | Mapping | ID string | Unmapped | Entity-level | Medium |

## Other Tables

The pipeline also produces:

- `stablecoin_prices`: daily stablecoin price and market-cap observations.
- `protocols`: protocol metadata and categories.
- `yield_mechanisms`: versioned pool mechanism classification with evidence URL and confidence.
- `risk_events`: depeg and protocol/stablecoin events with evidence URL.
- `yield_episodes`: continuous high-yield episodes and censoring fields.
- `source_requests`: request envelopes and checksums.

# Data Quality Report

Mode: `full`

## Summary

- Pool-day rows: 137,095
- Pools: 250
- Date range: 2022-02-11 00:00:00 to 2026-07-08 00:00:00
- APY coverage: 100.0%
- Base APY coverage: 90.3%
- Reward APY coverage: 61.6%
- TVL coverage: 100.0%

## Checks

| check_id                          | dataset        | severity   | status   |   evaluated_rows |   failed_rows |   failure_rate |
|:----------------------------------|:---------------|:-----------|:---------|-----------------:|--------------:|---------------:|
| panel.exists                      | pool_day_panel | critical   | passed   |           137095 |             0 |    0           |
| pool_day.unique_key               | pool_day_panel | critical   | passed   |           137095 |             0 |    0           |
| pool_day.apy_total.completeness   | pool_day_panel | error      | passed   |           137095 |             0 |    0           |
| pool_day.tvl_usd.completeness     | pool_day_panel | warning    | warning  |           137095 |            26 |    0.00018965  |
| pool_day.chain.completeness       | pool_day_panel | warning    | passed   |           137095 |             0 |    0           |
| pool_day.protocol_id.completeness | pool_day_panel | warning    | passed   |           137095 |             0 |    0           |
| pool_day.pool_type.completeness   | pool_day_panel | warning    | passed   |           137095 |             0 |    0           |
| apy.non_negative                  | pool_day_panel | error      | passed   |           137095 |             0 |    0           |
| apy.extreme_gt_1000               | pool_day_panel | warning    | warning  |           137095 |            32 |    0.000233415 |
| tvl.positive                      | pool_day_panel | error      | passed   |           137095 |             0 |    0           |
| apy.total_vs_components           | pool_day_panel | warning    | passed   |           137095 |             0 |    0           |
| entity_resolution.low_confidence  | pools          | warning    | passed   |              250 |             0 |    0           |

## Coverage By Pool Type

| pool_type                |   pools |
|:-------------------------|--------:|
| single_stable_lending    |     108 |
| incentive_driven         |      90 |
| stable_stable_lp         |      25 |
| yield_bearing_stablecoin |      19 |
| vault_aggregator         |       8 |


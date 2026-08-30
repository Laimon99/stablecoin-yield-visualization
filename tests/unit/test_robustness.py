from __future__ import annotations

import pandas as pd

from stablecoin_yield.analysis.pipeline import robustness_table


def test_robustness_table_materializes_all_configured_families() -> None:
    dates = pd.date_range("2026-01-01", periods=6, freq="D")
    panel = pd.DataFrame(
        {
            "pool_id": ["a"] * 6 + ["b"] * 6,
            "observed_date": list(dates) * 2,
            "apy_total": [4, 11, 12, 8, 21, 22, 3, 6, 7, 11, 12, 5],
            "tvl_usd": [2_000_000] * 6 + [750_000] * 6,
        }
    )
    config = {
        "yield_episodes": {
            "primary_threshold": {"apy_percent": 10},
            "max_gap_days": 1,
        },
        "robustness": {
            "thresholds_percent": [5, 10, 20],
            "min_tvl_usd": [500_000, 1_000_000],
            "min_history_days": [5],
            "gap_days": [0, 1, 3],
            "winsor_limits": [0.01, 0.99],
        },
    }

    result = robustness_table(panel, config)

    assert set(result["family"]) == {
        "apy_threshold",
        "minimum_tvl",
        "minimum_history",
        "episode_gap",
        "winsorization",
    }
    assert result["median_duration_days"].notna().all()

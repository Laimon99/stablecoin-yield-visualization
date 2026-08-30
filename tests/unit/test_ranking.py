from __future__ import annotations

import pandas as pd

from stablecoin_yield.metrics.ranking import ranking_retention


def test_ranking_retention_for_top_k() -> None:
    data = pd.DataFrame(
        {
            "observed_date": pd.to_datetime(
                ["2026-01-01"] * 3 + ["2026-01-02"] * 3
            ),
            "pool_id": ["a", "b", "c", "a", "c", "d"],
            "apy_total": [30, 20, 10, 25, 22, 21],
            "tvl_usd": [1, 1, 1, 1, 1, 1],
        }
    )
    result = ranking_retention(data, k_values=[2], horizons_days=[1])
    assert len(result) == 1
    assert result.iloc[0]["retention"] == 0.5
    assert result.iloc[0]["churn"] == 0.5


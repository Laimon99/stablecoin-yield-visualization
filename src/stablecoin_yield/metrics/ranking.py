from __future__ import annotations

import pandas as pd


def ranking_retention(panel: pd.DataFrame, k_values: list[int], horizons_days: list[int]) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    data = panel.dropna(subset=["observed_date", "apy_total"]).copy()
    top_by_date: dict[tuple[pd.Timestamp, int], set[str]] = {}
    for date, group in data.groupby("observed_date"):
        ranked = group.sort_values(["apy_total", "tvl_usd"], ascending=[False, False])
        for k in k_values:
            top_by_date[(date, k)] = set(ranked.head(k)["pool_id"])
    records = []
    dates = [pd.Timestamp(date) for date in sorted(data["observed_date"].dropna().unique())]
    date_set = set(dates)
    for date in dates:
        for horizon in horizons_days:
            future = date + pd.Timedelta(int(horizon), unit="D")
            if future not in date_set:
                continue
            for k in k_values:
                current_top = top_by_date.get((date, k), set())
                future_top = top_by_date.get((future, k), set())
                if len(current_top) < k or len(future_top) < k:
                    continue
                retention = len(current_top & future_top) / k
                records.append(
                    {
                        "observed_date": date,
                        "horizon_days": horizon,
                        "k": k,
                        "retention": retention,
                        "churn": 1 - retention,
                    }
                )
    return pd.DataFrame.from_records(records)

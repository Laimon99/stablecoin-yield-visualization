from __future__ import annotations

import pandas as pd


def threshold_label(threshold: float | str) -> str:
    if isinstance(threshold, str):
        return threshold
    return f"apy_ge_{threshold:g}"


def segment_episodes(
    panel: pd.DataFrame,
    *,
    threshold: float = 10.0,
    max_gap_days: int = 1,
    threshold_name: str | None = None,
) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    label = threshold_name or threshold_label(threshold)
    records = []
    for pool_id, group in panel.sort_values(["pool_id", "observed_date"]).groupby("pool_id"):
        data = group.copy()
        data["above"] = pd.to_numeric(data["apy_total"], errors="coerce") >= threshold
        active_rows = []
        previous_date = None
        episode_number = 0
        for row in data.itertuples(index=False):
            current_date = row.observed_date
            gap_break = (
                previous_date is not None
                and pd.notna(current_date)
                and (current_date - previous_date).days > max_gap_days + 1
            )
            if (not row.above or gap_break) and active_rows:
                records.append(_episode_record(pool_id, label, episode_number, active_rows, data))
                active_rows = []
                episode_number += 1
            if row.above:
                active_rows.append(row)
            previous_date = current_date if pd.notna(current_date) else previous_date
        if active_rows:
            records.append(_episode_record(pool_id, label, episode_number, active_rows, data))
    return pd.DataFrame.from_records(records)


def _episode_record(pool_id: str, label: str, number: int, rows: list, full_group: pd.DataFrame):
    start = rows[0]
    end = rows[-1]
    apys = [float(r.apy_total) for r in rows if pd.notna(r.apy_total)]
    tvls = [float(r.tvl_usd) for r in rows if pd.notna(r.tvl_usd)]
    full_last_date = full_group["observed_date"].max()
    return {
        "episode_id": f"{pool_id}_{label}_{number}",
        "pool_id": pool_id,
        "threshold_definition": label,
        "start_date": start.observed_date,
        "end_date": end.observed_date,
        "duration_days": int((end.observed_date - start.observed_date).days + 1),
        "start_apy": float(start.apy_total) if pd.notna(start.apy_total) else None,
        "peak_apy": max(apys) if apys else None,
        "end_apy": float(end.apy_total) if pd.notna(end.apy_total) else None,
        "start_tvl": float(start.tvl_usd) if pd.notna(start.tvl_usd) else None,
        "peak_tvl": max(tvls) if tvls else None,
        "end_tvl": float(end.tvl_usd) if pd.notna(end.tvl_usd) else None,
        "is_censored": end.observed_date == full_last_date,
    }


def percentile_threshold_episodes(
    panel: pd.DataFrame, *, percentile: float = 90.0, max_gap_days: int = 1
) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    data = panel.copy()
    daily_threshold = data.groupby("observed_date")["apy_total"].transform(
        lambda s: s.quantile(percentile / 100)
    )
    data["apy_percentile_threshold"] = daily_threshold
    data["above_percentile"] = data["apy_total"] >= data["apy_percentile_threshold"]
    transformed = data.copy()
    transformed["apy_total_for_threshold"] = transformed["apy_total"]
    records = []
    label = f"cross_sectional_p{percentile:g}"
    for pool_id, group in transformed.sort_values(["pool_id", "observed_date"]).groupby("pool_id"):
        active_rows = []
        previous_date = None
        episode_number = 0
        for row in group.itertuples(index=False):
            current_date = row.observed_date
            gap_break = (
                previous_date is not None
                and pd.notna(current_date)
                and (current_date - previous_date).days > max_gap_days + 1
            )
            if (not row.above_percentile or gap_break) and active_rows:
                records.append(_episode_record(pool_id, label, episode_number, active_rows, group))
                active_rows = []
                episode_number += 1
            if row.above_percentile:
                active_rows.append(row)
            previous_date = current_date if pd.notna(current_date) else previous_date
        if active_rows:
            records.append(_episode_record(pool_id, label, episode_number, active_rows, group))
    return pd.DataFrame.from_records(records)


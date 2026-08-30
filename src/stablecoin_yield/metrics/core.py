from __future__ import annotations

import numpy as np
import pandas as pd


def robust_mad(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return float("nan")
    median = clean.median()
    return float((clean - median).abs().median() * 1.4826)


def max_drawdown(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return float("nan")
    running_max = clean.cummax()
    drawdown = clean / running_max - 1
    return float(drawdown.min())


def persistence_ratio(values: pd.Series, threshold: float) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return float("nan")
    return float((clean >= threshold).mean())


def yield_half_life(group: pd.DataFrame) -> float:
    data = group.sort_values("observed_date")
    apy = pd.to_numeric(data["apy_total"], errors="coerce")
    if apy.dropna().empty:
        return float("nan")
    peak_idx = apy.idxmax()
    peak_value = apy.loc[peak_idx]
    if pd.isna(peak_value) or peak_value <= 0:
        return float("nan")
    after = data.loc[data.index >= peak_idx].copy()
    below = after[pd.to_numeric(after["apy_total"], errors="coerce") <= 0.5 * peak_value]
    if below.empty:
        return float("nan")
    return float((below.iloc[0]["observed_date"] - data.loc[peak_idx, "observed_date"]).days)


def pool_metrics(panel: pd.DataFrame, threshold: float = 10.0) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    records = []
    for pool_id, group in panel.groupby("pool_id"):
        apy = pd.to_numeric(group["apy_total"], errors="coerce")
        tvl = pd.to_numeric(group["tvl_usd"], errors="coerce")
        reward_share = pd.to_numeric(group.get("reward_share"), errors="coerce")
        first = group.iloc[0]
        records.append(
            {
                "pool_id": pool_id,
                "protocol_id": first.get("protocol_id"),
                "protocol_name": first.get("protocol_name"),
                "chain": first.get("chain"),
                "symbol_raw": first.get("symbol_raw"),
                "pool_type": first.get("pool_type"),
                "median_apy": float(apy.median()) if not apy.dropna().empty else np.nan,
                "mean_apy": float(apy.mean()) if not apy.dropna().empty else np.nan,
                "apy_robust_volatility": robust_mad(apy),
                "median_base_apy": float(group["apy_base"].median())
                if "apy_base" in group and not group["apy_base"].dropna().empty
                else np.nan,
                "median_reward_apy": float(group["apy_reward"].median())
                if "apy_reward" in group and not group["apy_reward"].dropna().empty
                else np.nan,
                "median_reward_share": float(reward_share.median())
                if not reward_share.dropna().empty
                else np.nan,
                "persistence_ratio_10": persistence_ratio(apy, threshold),
                "median_tvl_usd": float(tvl.median()) if not tvl.dropna().empty else np.nan,
                "tvl_volatility": robust_mad(tvl.pct_change(fill_method=None)),
                "tvl_drawdown": max_drawdown(tvl),
                "pool_history_length": int(group["observed_date"].nunique()),
                "first_seen": group["observed_date"].min(),
                "last_seen": group["observed_date"].max(),
                "yield_half_life_days": yield_half_life(group),
                "entity_resolution_confidence": first.get("entity_resolution_confidence"),
            }
        )
    return pd.DataFrame.from_records(records)

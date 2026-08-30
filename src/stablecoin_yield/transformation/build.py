from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stablecoin_yield.config import get_paths, load_config
from stablecoin_yield.raw import latest_raw_file, read_envelope
from stablecoin_yield.transformation.entities import build_pools_table, stablecoin_table


def load_latest_payload(root: Path, source: str, endpoint: str) -> Any:
    path = latest_raw_file(get_paths(root).raw_dir, source, endpoint)
    if path is None:
        raise FileNotFoundError(f"Missing raw sample for {source} {endpoint}")
    return read_envelope(path).payload


def all_chart_envelopes(root: Path) -> list[tuple[Path, Any]]:
    raw = get_paths(root).raw_dir / "defillama_yields"
    if not raw.exists():
        return []
    files = sorted(raw.glob("**/chart_*.json"))
    return [(path, read_envelope(path).payload) for path in files]


def select_candidate_pools(
    pools_payload: dict[str, Any], *, min_tvl: float, min_history: int, limit: int
) -> pd.DataFrame:
    rows = pools_payload.get("data", [])
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    candidates = frame[
        (frame["stablecoin"] == True)  # noqa: E712
        & (pd.to_numeric(frame["tvlUsd"], errors="coerce") >= min_tvl)
        & (pd.to_numeric(frame["count"], errors="coerce") >= min_history)
        & frame["pool"].notna()
    ].copy()
    if candidates.empty:
        return candidates
    candidates["apy_rank"] = pd.to_numeric(candidates["apy"], errors="coerce").rank(
        ascending=False, method="first"
    )
    candidates["tvl_rank"] = pd.to_numeric(candidates["tvlUsd"], errors="coerce").rank(
        ascending=False, method="first"
    )
    by_tvl = candidates.sort_values("tvlUsd", ascending=False).head(max(int(limit * 0.7), 1))
    by_apy = candidates.sort_values("apy", ascending=False).head(max(limit - len(by_tvl), 1))
    selected = pd.concat([by_tvl, by_apy]).drop_duplicates(subset=["pool"])
    if len(selected) < limit:
        selected = pd.concat([selected, candidates.sort_values("tvlUsd", ascending=False)]).drop_duplicates(
            subset=["pool"]
        )
    return selected.head(limit).reset_index(drop=True)


def build_snapshots(root: Path, pools: pd.DataFrame) -> pd.DataFrame:
    source_to_pool = dict(zip(pools["source_pool_id"], pools["pool_id"], strict=False))
    records: list[dict[str, Any]] = []
    for path, payload in all_chart_envelopes(root):
        raw_name = path.name
        pool_id_from_name = raw_name.removeprefix("chart_").split("_", 1)[0]
        canonical_id = source_to_pool.get(pool_id_from_name)
        if canonical_id is None:
            continue
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        envelope = read_envelope(path)
        for row in rows:
            records.append(
                {
                    "pool_id": canonical_id,
                    "source_pool_id": pool_id_from_name,
                    "observed_at": row.get("timestamp"),
                    "observed_date": pd.to_datetime(row.get("timestamp"), utc=True).date()
                    if row.get("timestamp")
                    else pd.NaT,
                    "apy_total_raw": row.get("apy"),
                    "apy_base": row.get("apyBase"),
                    "apy_reward": row.get("apyReward"),
                    "tvl_usd_raw": row.get("tvlUsd"),
                    "il_7d": row.get("il7d"),
                    "apy_base_7d": row.get("apyBase7d"),
                    "price_per_share": row.get("pricePerShare"),
                    "source": envelope.source,
                    "source_payload_id": envelope.payload_checksum,
                }
            )
    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        return frame
    frame["observed_date"] = pd.to_datetime(frame["observed_date"])
    frame["apy_total_raw"] = pd.to_numeric(frame["apy_total_raw"], errors="coerce")
    frame["apy_base"] = pd.to_numeric(frame["apy_base"], errors="coerce")
    frame["apy_reward"] = pd.to_numeric(frame["apy_reward"], errors="coerce")
    frame["tvl_usd_raw"] = pd.to_numeric(frame["tvl_usd_raw"], errors="coerce")
    frame = frame.sort_values(["pool_id", "observed_date", "observed_at"]).drop_duplicates(
        subset=["pool_id", "observed_date"], keep="last"
    )
    return clean_snapshots(frame).reset_index(drop=True)


def clean_snapshots(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["apy_negative_flag"] = out["apy_total_raw"] < 0
    out["apy_extreme_flag"] = out["apy_total_raw"] > 1000
    out["apy_component_mismatch_flag"] = False
    component_sum = out["apy_base"].fillna(0) + out["apy_reward"].fillna(0)
    has_components = out["apy_base"].notna() | out["apy_reward"].notna()
    out.loc[has_components, "apy_component_mismatch_flag"] = (
        (out.loc[has_components, "apy_total_raw"] - component_sum.loc[has_components]).abs() > 1.0
    )
    out["apy_outlier_flag"] = (
        out["apy_negative_flag"] | out["apy_extreme_flag"] | out["apy_component_mismatch_flag"]
    )
    out["apy_total"] = out["apy_total_raw"].where(~out["apy_negative_flag"])
    out["tvl_negative_or_zero_flag"] = out["tvl_usd_raw"] <= 0
    out["tvl_usd"] = out["tvl_usd_raw"].where(~out["tvl_negative_or_zero_flag"])
    out["exclusion_reason"] = ""
    out.loc[out["apy_negative_flag"], "exclusion_reason"] = "negative_apy"
    out.loc[out["tvl_negative_or_zero_flag"], "exclusion_reason"] = "non_positive_tvl"
    out["reward_share"] = np.where(
        (out["apy_total"] > 0) & out["apy_reward"].notna(),
        out["apy_reward"].clip(lower=0) / out["apy_total"],
        np.nan,
    )
    return out


def build_stablecoin_prices(root: Path, stablecoins: pd.DataFrame) -> pd.DataFrame:
    payload = load_latest_payload(root, "defillama_stablecoins", "/stablecoinprices")
    gecko_to_stable = {
        str(row.gecko_id): row.stablecoin_id
        for row in stablecoins.itertuples(index=False)
        if pd.notna(row.gecko_id)
    }
    records: list[dict[str, Any]] = []
    if not isinstance(payload, list):
        return pd.DataFrame()
    for row in payload:
        timestamp = row.get("date")
        if not timestamp:
            continue
        date = pd.to_datetime(int(timestamp), unit="s", utc=True).date()
        prices = row.get("prices") or {}
        for gecko_id, price in prices.items():
            stablecoin_id = gecko_to_stable.get(str(gecko_id))
            if stablecoin_id:
                records.append(
                    {
                        "stablecoin_id": stablecoin_id,
                        "gecko_id": gecko_id,
                        "observed_date": pd.to_datetime(date),
                        "price_usd": pd.to_numeric(price, errors="coerce"),
                        "source": "defillama_stablecoins",
                    }
                )
    return pd.DataFrame.from_records(records).drop_duplicates(
        subset=["stablecoin_id", "observed_date"], keep="last"
    )


def build_protocols(pools: pd.DataFrame) -> pd.DataFrame:
    if pools.empty:
        return pd.DataFrame()
    protocols = (
        pools[["protocol_id", "protocol_name"]]
        .drop_duplicates()
        .assign(
            category=lambda d: d["protocol_id"].map(protocol_category),
            chain_scope="multi_or_unknown",
            governance_model=None,
            audited_status="not_assessed",
            launch_date=None,
            documentation_url=None,
        )
    )
    return protocols


def protocol_category(protocol_id: str) -> str:
    text = str(protocol_id).lower()
    if any(token in text for token in ["aave", "compound", "morpho", "maple", "sky", "spark"]):
        return "lending"
    if any(token in text for token in ["curve", "uniswap", "balancer", "aerodrome", "pancake"]):
        return "dex_lp"
    if any(token in text for token in ["yearn", "beefy", "convex", "pendle"]):
        return "vault_aggregator"
    if any(token in text for token in ["ethena", "usual", "maker"]):
        return "stablecoin_protocol"
    return "other"


def build_yield_mechanisms(pools: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for row in pools.itertuples(index=False):
        reward_source = "reward_tokens" if row.reward_token_ids else "none_or_unobserved"
        records.append(
            {
                "pool_id": row.pool_id,
                "valid_from": row.first_seen_at,
                "valid_to": row.last_seen_at,
                "mechanism_type": row.pool_type,
                "base_source": protocol_category(row.protocol_id),
                "reward_source": reward_source,
                "reward_tokens": row.reward_token_ids,
                "leverage": row.pool_type == "leveraged_recursive",
                "lockup": None,
                "withdrawal_constraints": None,
                "manual_confidence": row.pool_type_confidence,
                "evidence_url": None,
                "evidence_note": row.pool_type_evidence,
            }
        )
    return pd.DataFrame.from_records(records)


def build_risk_events(stablecoin_prices: pd.DataFrame) -> pd.DataFrame:
    if stablecoin_prices.empty:
        return pd.DataFrame()
    prices = stablecoin_prices.copy()
    prices["depeg_abs"] = (prices["price_usd"] - 1.0).abs()
    events: list[dict[str, Any]] = []
    for stablecoin_id, group in prices.sort_values("observed_date").groupby("stablecoin_id"):
        stressed = group[group["depeg_abs"] > 0.01]
        if stressed.empty:
            continue
        stressed = stressed.copy()
        stressed["gap"] = stressed["observed_date"].diff().dt.days.fillna(1)
        block = (stressed["gap"] > 1).cumsum()
        for block_id, block_frame in stressed.groupby(block):
            peak = block_frame.loc[block_frame["depeg_abs"].idxmax()]
            events.append(
                {
                    "event_id": f"depeg_{stablecoin_id}_{int(block_id)}",
                    "event_type": "stablecoin_depeg",
                    "entity_type": "stablecoin",
                    "entity_id": stablecoin_id,
                    "start_at": block_frame["observed_date"].min(),
                    "end_at": block_frame["observed_date"].max(),
                    "severity": classify_depeg(float(peak["depeg_abs"])),
                    "peak_abs_deviation": float(peak["depeg_abs"]),
                    "description": "Detected by price deviation from USD 1.0 in DeFiLlama stablecoin prices",
                    "evidence_url": "https://stablecoins.llama.fi/stablecoinprices",
                }
            )
    return pd.DataFrame.from_records(events)


def classify_depeg(value: float) -> str:
    if value > 0.03:
        return "severe"
    if value > 0.01:
        return "material"
    if value > 0.005:
        return "minor"
    return "none"


def build_canonical_dataset(root: Path, mode: str = "sample") -> dict[str, pd.DataFrame]:
    paths = get_paths(root)
    config = load_config(root)
    metrics = config["metrics"]
    project_cfg = config["project"]["reproducibility"]
    limit = (
        project_cfg["sample_mode_pool_limit"]
        if mode == "sample"
        else project_cfg["full_mode_pool_limit"]
    )
    min_tvl = float(metrics["pool_filters"]["min_tvl_usd"])
    min_history = int(metrics["pool_filters"]["min_history_days"])

    pools_payload = load_latest_payload(root, "defillama_yields", "/pools")
    stable_payload = load_latest_payload(root, "defillama_stablecoins", "/stablecoins")
    stablecoins = stablecoin_table(stable_payload)
    selected = select_candidate_pools(
        pools_payload, min_tvl=min_tvl, min_history=min_history, limit=limit
    )
    all_pools = build_pools_table({"data": selected.to_dict("records")}, stablecoins)
    snapshots = build_snapshots(root, all_pools)
    if not snapshots.empty:
        dates = snapshots.groupby("pool_id")["observed_date"].agg(["min", "max"]).reset_index()
        all_pools = all_pools.merge(dates, on="pool_id", how="left")
        all_pools["first_seen_at"] = all_pools["min"]
        all_pools["last_seen_at"] = all_pools["max"]
        all_pools = all_pools.drop(columns=["min", "max"])
    stablecoin_prices = build_stablecoin_prices(root, stablecoins)
    protocols = build_protocols(all_pools)
    mechanisms = build_yield_mechanisms(all_pools)
    risk_events = build_risk_events(stablecoin_prices)
    panel = snapshots.merge(
        all_pools[
            [
                "pool_id",
                "source_pool_id",
                "protocol_id",
                "protocol_name",
                "chain",
                "symbol_raw",
                "pool_type",
                "stablecoin_ids",
                "reward_token_ids",
                "is_stable_only",
                "current_tvl_usd",
                "entity_resolution_confidence",
            ]
        ],
        on=["pool_id", "source_pool_id"],
        how="left",
    )

    outputs = {
        "pools": all_pools,
        "pool_snapshots": snapshots,
        "stablecoins": stablecoins,
        "stablecoin_prices": stablecoin_prices,
        "protocols": protocols,
        "yield_mechanisms": mechanisms,
        "risk_events": risk_events,
        "pool_day_panel": panel,
    }
    write_tables(outputs, paths)
    return outputs


def write_tables(outputs: dict[str, pd.DataFrame], paths) -> None:
    for name, frame in outputs.items():
        if frame is None:
            continue
        target_dir = paths.analytical_dir if name == "pool_day_panel" else paths.processed_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        if not frame.empty:
            frame.to_parquet(target_dir / f"{name}.parquet", index=False)
        frame.to_csv(target_dir / f"{name}.csv", index=False)


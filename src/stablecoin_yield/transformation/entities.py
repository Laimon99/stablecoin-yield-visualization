from __future__ import annotations

import re
from hashlib import sha1
from typing import Any

import pandas as pd

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9.]{1,20}")

LENDING_PROJECTS = {
    "aave",
    "compound",
    "morpho",
    "maple",
    "sky-lending",
    "spark",
    "kamino-lend",
    "silo",
    "fluid-lending",
    "euler",
}

LP_PROJECT_HINTS = {
    "curve",
    "uniswap",
    "pancakeswap",
    "balancer",
    "aerodrome",
    "velodrome",
    "sushiswap",
    "trader-joe",
    "orca",
    "raydium",
    "thena",
    "camelot",
}

AGGREGATOR_HINTS = {
    "yearn",
    "beefy",
    "convex",
    "pendle",
    "stake-dao",
    "idle",
    "sommelier",
    "enzyme",
}

LEVERAGED_HINTS = {
    "gearbox",
    "loop",
    "recursive",
    "multiply",
    "leveraged",
    "delta-neutral",
}

YIELD_BEARING_SYMBOL_HINTS = {
    "SDAI",
    "SUSDE",
    "USDE",
    "SUSDS",
    "USDS",
    "USDY",
    "AUSDC",
    "AUSDT",
    "CUSDC",
    "SFRAX",
    "FRXUSD",
}

PREFERRED_SYMBOL_STABLE_IDS = {
    "USDC": "usd_coin",
    "USDT": "tether",
    "DAI": "dai",
    "FRAX": "frax",
    "FRXUSD": "frax_usd",
    "USDE": "ethena_usde",
    "SUSDE": "ethena_usde",
    "USDS": "usds",
    "SUSDS": "usds",
    "SDAI": "dai",
    "USD0": "usual_usd",
    "BUSD0": "usual_usd",
    "FXUSD": "f_x_protocol_fxusd",
    "MSUSD": "main_street_usd",
    "PMUSD": "precious_metals_usd",
    "CRVUSD": "crvusd",
    "EURC": "euro_coin",
}


def stable_id(symbol: str, gecko_id: str | None = None) -> str:
    token = gecko_id or symbol.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", token.lower()).strip("_")
    return cleaned or "unknown"


def canonical_pool_id(source_pool_id: str, chain: str, project: str) -> str:
    key = f"{source_pool_id}|{chain}|{project}"
    return "pool_" + sha1(key.encode("utf-8")).hexdigest()[:16]


def parse_symbol_assets(symbol: str | None) -> list[str]:
    if not symbol:
        return []
    upper = symbol.upper().replace("(", "-").replace(")", "-")
    tokens = [match.group(0).upper() for match in TOKEN_RE.finditer(upper)]
    noise = {"POOL", "VAULT", "LP", "V2", "V3"}
    return [token for token in tokens if token not in noise]


def classify_pool_type(row: pd.Series) -> tuple[str, float, str]:
    project = str(row.get("project") or "").lower()
    symbol = str(row.get("symbol") or "").upper()
    reward_tokens = row.get("rewardTokens")
    apy_reward = row.get("apyReward")
    exposure = str(row.get("exposure") or "").lower()

    if isinstance(reward_tokens, list) and reward_tokens:
        return "incentive_driven", 0.8, "rewardTokens present"
    if pd.notna(apy_reward) and float(apy_reward or 0) > 0:
        return "incentive_driven", 0.75, "apyReward positive"
    if any(hint in project for hint in LEVERAGED_HINTS):
        return "leveraged_recursive", 0.7, "project name leverage hint"
    if any(hint in project for hint in AGGREGATOR_HINTS):
        return "vault_aggregator", 0.7, "project name aggregator hint"
    if any(token in symbol for token in YIELD_BEARING_SYMBOL_HINTS):
        return "yield_bearing_stablecoin", 0.7, "symbol yield-bearing hint"
    if project in LENDING_PROJECTS or any(hint in project for hint in LENDING_PROJECTS):
        return "single_stable_lending", 0.7, "project lending hint"
    if any(hint in project for hint in LP_PROJECT_HINTS):
        return "stable_stable_lp", 0.7, "project LP hint"
    if exposure == "single":
        return "single_stable_lending", 0.45, "single exposure fallback"
    return "stable_stable_lp", 0.35, "stablecoin pool fallback"


def stablecoin_table(stablecoin_payload: dict[str, Any]) -> pd.DataFrame:
    rows = stablecoin_payload.get("peggedAssets", [])
    records: list[dict[str, Any]] = []
    for asset in rows:
        symbol = str(asset.get("symbol") or "").upper()
        gecko_id = asset.get("gecko_id")
        records.append(
            {
                "stablecoin_id": stable_id(symbol, gecko_id),
                "source_stablecoin_id": str(asset.get("id")),
                "name": asset.get("name"),
                "symbol": symbol,
                "gecko_id": gecko_id,
                "peg_currency": str(asset.get("pegType") or "").replace("pegged", "") or None,
                "design_type": normalize_design_type(asset.get("pegMechanism")),
                "peg_mechanism_raw": asset.get("pegMechanism"),
                "issuer": None,
                "collateral_type": asset.get("pegMechanism"),
                "is_yield_bearing": symbol in YIELD_BEARING_SYMBOL_HINTS
                or "yield" in str(asset.get("name") or "").lower(),
                "chains": "|".join(asset.get("chains") or []),
                "price": asset.get("price"),
            }
        )
    frame = pd.DataFrame.from_records(records)
    return frame.drop_duplicates(subset=["stablecoin_id"]).reset_index(drop=True)


def normalize_design_type(value: Any) -> str:
    text = str(value or "").lower()
    if "fiat" in text:
        return "fiat_backed"
    if "crypto" in text:
        return "crypto_collateralized"
    if "algorithm" in text:
        return "algorithmic_synthetic"
    if "rwa" in text or "real-world" in text:
        return "rwa_backed"
    if "yield" in text:
        return "yield_bearing"
    return "other_or_unknown"


def build_pools_table(pools_payload: dict[str, Any], stablecoins: pd.DataFrame) -> pd.DataFrame:
    rows = pools_payload.get("data", [])
    raw = pd.DataFrame(rows)
    if raw.empty:
        return pd.DataFrame()
    stable_symbol_to_id = preferred_symbol_mapping(stablecoins)
    records: list[dict[str, Any]] = []
    for _, row in raw.iterrows():
        source_pool_id = str(row.get("pool"))
        assets = parse_symbol_assets(row.get("symbol"))
        mapped_assets = [stable_symbol_to_id[a] for a in assets if a in stable_symbol_to_id]
        override_assets = [a for a in assets if a in PREFERRED_SYMBOL_STABLE_IDS]
        pool_type, confidence, evidence = classify_pool_type(row)
        records.append(
            {
                "pool_id": canonical_pool_id(
                    source_pool_id, str(row.get("chain") or ""), str(row.get("project") or "")
                ),
                "source_pool_id": source_pool_id,
                "protocol_id": str(row.get("project") or "").lower(),
                "protocol_name": row.get("project"),
                "chain": row.get("chain"),
                "symbol_raw": row.get("symbol"),
                "pool_type": pool_type,
                "pool_type_confidence": confidence,
                "pool_type_evidence": evidence,
                "stablecoin_ids": "|".join(mapped_assets),
                "reward_token_ids": "|".join(row.get("rewardTokens") or []),
                "underlying_assets": "|".join(assets),
                "is_single_asset": len(assets) <= 1,
                "is_stable_only": bool(row.get("stablecoin")),
                "current_tvl_usd": row.get("tvlUsd"),
                "current_apy": row.get("apy"),
                "current_apy_base": row.get("apyBase"),
                "current_apy_reward": row.get("apyReward"),
                "history_count": row.get("count"),
                "exposure": row.get("exposure"),
                "il_risk": row.get("ilRisk"),
                "source_outlier": row.get("outlier"),
                "first_seen_at": None,
                "last_seen_at": None,
                "status": "observed",
                "entity_resolution_confidence": 0.95
                if override_assets
                else (0.85 if mapped_assets or bool(row.get("stablecoin")) else 0.4),
                "manual_review_required": confidence < 0.7 or not mapped_assets,
                "entity_resolution_note": "manual_symbol_override"
                if override_assets
                else ("stablecoin_symbol_mapping" if mapped_assets else "source_stablecoin_flag_only"),
            }
        )
    return pd.DataFrame.from_records(records)


def preferred_symbol_mapping(stablecoins: pd.DataFrame) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in stablecoins.itertuples(index=False):
        symbol = str(row.symbol).upper()
        candidate = str(row.stablecoin_id)
        if symbol not in mapping:
            mapping[symbol] = candidate
        preferred = PREFERRED_SYMBOL_STABLE_IDS.get(symbol)
        if preferred == candidate:
            mapping[symbol] = candidate
    for symbol, stablecoin_id in PREFERRED_SYMBOL_STABLE_IDS.items():
        mapping[symbol] = stablecoin_id
    return mapping

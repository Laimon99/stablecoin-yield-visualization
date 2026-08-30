from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stablecoin_yield.config import get_paths
from stablecoin_yield.ingestion.coingecko import CoinGeckoClient
from stablecoin_yield.ingestion.defillama import DefiLlamaStablecoinsClient, DefiLlamaYieldsClient
from stablecoin_yield.raw import RawEnvelope, write_raw_envelope


@dataclass(frozen=True)
class VerificationResult:
    source: str
    endpoint: str
    status_code: int
    raw_file: str
    summary: dict[str, Any]


def _write(envelope: RawEnvelope, root: Path) -> Path:
    return write_raw_envelope(envelope, get_paths(root).raw_dir)


def _public_path(path: Path, root: Path) -> str:
    """Return a portable reference without exposing the local workstation path."""
    return path.relative_to(root).as_posix()


def verify_sources(root: Path | None = None) -> list[VerificationResult]:
    paths = get_paths(root)
    results: list[VerificationResult] = []

    yields = DefiLlamaYieldsClient()
    stablecoins = DefiLlamaStablecoinsClient()
    coingecko = CoinGeckoClient()
    try:
        pools_env = yields.pools()
        pools_file = _write(pools_env, paths.root)
        pools_payload = pools_env.payload
        pool_rows = pools_payload.get("data", []) if isinstance(pools_payload, dict) else []
        stable_candidates = [
            p
            for p in pool_rows
            if p.get("stablecoin") and (p.get("tvlUsd") or 0) > 1_000_000 and (p.get("count") or 0) >= 180
        ]
        results.append(
            VerificationResult(
                "defillama_yields",
                "/pools",
                pools_env.status_code,
                _public_path(pools_file, paths.root),
                {
                    "row_count": len(pool_rows),
                    "stable_candidates_tvl_gt_1m_history_gt_180": len(stable_candidates),
                    "first_keys": list(pool_rows[0].keys()) if pool_rows else [],
                },
            )
        )

        if stable_candidates:
            selected = sorted(stable_candidates, key=lambda p: p.get("tvlUsd") or 0, reverse=True)[0]
            chart_env = yields.chart(str(selected["pool"]))
            chart_file = _write(chart_env, paths.root)
            chart_payload = chart_env.payload
            chart_rows = chart_payload.get("data", []) if isinstance(chart_payload, dict) else []
            results.append(
                VerificationResult(
                    "defillama_yields",
                    "/chart/{pool}",
                    chart_env.status_code,
                    _public_path(chart_file, paths.root),
                    {
                        "pool": selected["pool"],
                        "project": selected.get("project"),
                        "symbol": selected.get("symbol"),
                        "row_count": len(chart_rows),
                        "first_keys": list(chart_rows[0].keys()) if chart_rows else [],
                    },
                )
            )

        stables_env = stablecoins.stablecoins(include_prices=True)
        stables_file = _write(stables_env, paths.root)
        stables_payload = stables_env.payload
        assets = stables_payload.get("peggedAssets", []) if isinstance(stables_payload, dict) else []
        results.append(
            VerificationResult(
                "defillama_stablecoins",
                "/stablecoins",
                stables_env.status_code,
                _public_path(stables_file, paths.root),
                {
                    "stablecoin_count": len(assets),
                    "first_keys": list(assets[0].keys()) if assets else [],
                },
            )
        )

        prices_env = stablecoins.stablecoin_prices()
        prices_file = _write(prices_env, paths.root)
        prices_payload = prices_env.payload
        results.append(
            VerificationResult(
                "defillama_stablecoins",
                "/stablecoinprices",
                prices_env.status_code,
                _public_path(prices_file, paths.root),
                {
                    "row_count": len(prices_payload) if isinstance(prices_payload, list) else None,
                    "first_keys": list(prices_payload[0].keys())
                    if isinstance(prices_payload, list) and prices_payload
                    else [],
                },
            )
        )

        cg_env = coingecko.coins_markets(["tether", "usd-coin", "dai"])
        cg_file = _write(cg_env, paths.root)
        cg_payload = cg_env.payload
        results.append(
            VerificationResult(
                "coingecko",
                "/coins/markets",
                cg_env.status_code,
                _public_path(cg_file, paths.root),
                {
                    "row_count": len(cg_payload) if isinstance(cg_payload, list) else None,
                    "first_keys": list(cg_payload[0].keys()) if isinstance(cg_payload, list) and cg_payload else [],
                },
            )
        )
    finally:
        yields.close()
        stablecoins.close()
        coingecko.close()

    results_path = paths.quality_dir / "source_verification_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8") as handle:
        json.dump([r.__dict__ for r in results], handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return results

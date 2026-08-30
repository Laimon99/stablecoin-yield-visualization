from __future__ import annotations

from pathlib import Path

import pytest

from stablecoin_yield.config import get_paths
from stablecoin_yield.raw import latest_raw_file, read_envelope

ROOT = Path(__file__).resolve().parents[2]
RAW = get_paths(ROOT).raw_dir


def require_latest(source: str, endpoint: str) -> Path:
    path = latest_raw_file(RAW, source, endpoint)
    if path is None:
        pytest.skip(f"No raw sample for {source} {endpoint}. Run scripts/verify_sources.py.")
    return path


def test_defillama_yields_pools_contract() -> None:
    envelope = read_envelope(require_latest("defillama_yields", "/pools"))
    assert envelope.status_code == 200
    assert envelope.source == "defillama_yields"
    assert isinstance(envelope.payload, dict)
    rows = envelope.payload.get("data")
    assert isinstance(rows, list)
    assert rows
    required = {
        "chain",
        "project",
        "symbol",
        "tvlUsd",
        "apyBase",
        "apyReward",
        "apy",
        "pool",
        "stablecoin",
        "count",
    }
    assert required.issubset(rows[0].keys())


def test_defillama_yields_chart_contract() -> None:
    paths = sorted((RAW / "defillama_yields").glob("**/chart_*.json"))
    if not paths:
        pytest.skip("No chart raw sample. Run scripts/verify_sources.py.")
    envelope = read_envelope(paths[-1])
    assert envelope.status_code == 200
    assert isinstance(envelope.payload, dict)
    rows = envelope.payload.get("data")
    assert isinstance(rows, list)
    assert rows
    assert {"timestamp", "tvlUsd", "apy", "apyBase", "apyReward"}.issubset(rows[0].keys())


def test_defillama_stablecoins_contract() -> None:
    envelope = read_envelope(require_latest("defillama_stablecoins", "/stablecoins"))
    assert envelope.status_code == 200
    rows = envelope.payload.get("peggedAssets")
    assert isinstance(rows, list)
    assert rows
    assert {"id", "name", "symbol", "gecko_id", "pegType", "pegMechanism"}.issubset(
        rows[0].keys()
    )


def test_defillama_stablecoinprices_contract() -> None:
    envelope = read_envelope(require_latest("defillama_stablecoins", "/stablecoinprices"))
    assert envelope.status_code == 200
    assert isinstance(envelope.payload, list)
    assert envelope.payload
    assert {"date", "prices"}.issubset(envelope.payload[0].keys())
    assert isinstance(envelope.payload[0]["prices"], dict)


def test_coingecko_markets_contract() -> None:
    envelope = read_envelope(require_latest("coingecko", "/coins/markets"))
    assert envelope.status_code == 200
    assert isinstance(envelope.payload, list)
    assert envelope.payload
    assert {"id", "symbol", "name", "current_price", "market_cap", "last_updated"}.issubset(
        envelope.payload[0].keys()
    )


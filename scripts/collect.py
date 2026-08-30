from __future__ import annotations

import argparse
from pathlib import Path

from stablecoin_yield.config import get_paths, load_config
from stablecoin_yield.ingestion.coingecko import CoinGeckoClient
from stablecoin_yield.ingestion.defillama import DefiLlamaStablecoinsClient, DefiLlamaYieldsClient
from stablecoin_yield.raw import latest_raw_file, read_envelope, write_raw_envelope
from stablecoin_yield.transformation.build import select_candidate_pools


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    paths = get_paths(root)
    config = load_config(root)
    limit = (
        config["project"]["reproducibility"]["sample_mode_pool_limit"]
        if args.mode == "sample"
        else config["project"]["reproducibility"]["full_mode_pool_limit"]
    )
    min_tvl = float(config["metrics"]["pool_filters"]["min_tvl_usd"])
    min_history = int(config["metrics"]["pool_filters"]["min_history_days"])

    yields = DefiLlamaYieldsClient()
    stables = DefiLlamaStablecoinsClient()
    cg = CoinGeckoClient()
    try:
        if args.refresh or latest_raw_file(paths.raw_dir, "defillama_yields", "/pools") is None:
            write_raw_envelope(yields.pools(), paths.raw_dir)
        if args.refresh or latest_raw_file(paths.raw_dir, "defillama_stablecoins", "/stablecoins") is None:
            write_raw_envelope(stables.stablecoins(include_prices=True), paths.raw_dir)
        if args.refresh or latest_raw_file(paths.raw_dir, "defillama_stablecoins", "/stablecoinprices") is None:
            write_raw_envelope(stables.stablecoin_prices(), paths.raw_dir)
        if args.refresh or latest_raw_file(paths.raw_dir, "coingecko", "/coins/markets") is None:
            write_raw_envelope(cg.coins_markets(["tether", "usd-coin", "dai", "frax", "ethena-usde"]), paths.raw_dir)

        pools_path = latest_raw_file(paths.raw_dir, "defillama_yields", "/pools")
        pools_payload = read_envelope(pools_path).payload
        selected = select_candidate_pools(
            pools_payload, min_tvl=min_tvl, min_history=min_history, limit=int(limit)
        )
        existing_charts = {p.name.removeprefix("chart_").split("_", 1)[0] for p in (paths.raw_dir / "defillama_yields").glob("**/chart_*.json")}
        fetched = 0
        for row in selected.itertuples(index=False):
            pool_id = str(row.pool)
            if not args.refresh and pool_id in existing_charts:
                continue
            envelope = yields.chart(pool_id)
            write_raw_envelope(envelope, paths.raw_dir)
            fetched += 1
        print(f"selected_pools={len(selected)} fetched_charts={fetched} mode={args.mode}")
    finally:
        yields.close()
        stables.close()
        cg.close()


if __name__ == "__main__":
    main()


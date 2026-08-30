from __future__ import annotations

import argparse
from pathlib import Path

from stablecoin_yield.visualization.figures import render_all_figures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    registry = render_all_figures(root, mode=args.mode)
    print(registry[["id", "title", "sample_size"]].to_string(index=False))


if __name__ == "__main__":
    main()


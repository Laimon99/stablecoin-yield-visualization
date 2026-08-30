from __future__ import annotations

import argparse
from pathlib import Path

from stablecoin_yield.analysis.pipeline import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    outputs = run_analysis(root, mode=args.mode)
    for name, frame in outputs.items():
        print(f"{name}: {len(frame)} rows")


if __name__ == "__main__":
    main()


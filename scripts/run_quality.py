from __future__ import annotations

import argparse
from pathlib import Path

from stablecoin_yield.validation.quality import quality_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = quality_report(root, mode=args.mode)
    print(report[["check_id", "status", "failed_rows"]].to_string(index=False))


if __name__ == "__main__":
    main()


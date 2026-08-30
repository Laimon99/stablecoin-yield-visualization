from __future__ import annotations

import argparse
from pathlib import Path

from stablecoin_yield.reporting import build_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    outputs = build_report(root, mode=args.mode)
    print(f"markdown={outputs.markdown.relative_to(root)}")
    print(f"pdf={outputs.pdf.relative_to(root)}")
    print(f"summary={outputs.summary_json.relative_to(root)}")


if __name__ == "__main__":
    main()

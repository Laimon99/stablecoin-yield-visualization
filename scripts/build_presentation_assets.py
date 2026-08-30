from __future__ import annotations

import argparse
from pathlib import Path

from stablecoin_yield.presentation_assets import build_presentation_assets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    outputs = build_presentation_assets(root, mode=args.mode)
    print(f"outline={outputs.outline_markdown.relative_to(root)}")
    print(f"slides={outputs.slides_json.relative_to(root)}")
    print(f"speaker_notes={outputs.speaker_notes.relative_to(root)}")


if __name__ == "__main__":
    main()

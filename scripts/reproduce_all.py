from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from stablecoin_yield.reproducibility import build_release_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument(
        "--with-presentation",
        action="store_true",
        help="Also rebuild the optional PowerPoint artifact with @oai/artifact-tool.",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    steps = [
        ["scripts/collect.py", "--mode", args.mode],
        ["scripts/build_dataset.py", "--mode", args.mode],
        ["scripts/run_quality.py", "--mode", args.mode],
        ["scripts/run_analysis.py", "--mode", args.mode],
        ["scripts/render_figures.py", "--mode", args.mode],
        ["scripts/build_report.py", "--mode", args.mode],
        ["scripts/render_report_preview.py"],
    ]
    if args.refresh:
        steps[0].append("--refresh")
    for step in steps:
        command = [sys.executable, *step]
        print(f"running: {' '.join(step)}", flush=True)
        subprocess.run(command, cwd=root, check=True)
    if args.with_presentation:
        presentation_steps = [
            [sys.executable, "scripts/build_presentation_assets.py", "--mode", args.mode],
            ["node", "scripts/build_presentation_deck.mjs", "--mode", args.mode],
            [sys.executable, "scripts/build_presentation_contact_sheet.py"],
        ]
        for command in presentation_steps:
            print(f"running: {' '.join(command[1:])}", flush=True)
            subprocess.run(command, cwd=root, check=True)
    else:
        print(
            "presentation rebuild skipped; pass --with-presentation when "
            "@oai/artifact-tool is available",
            flush=True,
        )
    manifest = build_release_manifest(root, args.mode)
    print(f"manifest={manifest.path.relative_to(root)} files={manifest.file_count}")


if __name__ == "__main__":
    main()

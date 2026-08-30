from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preview-dir",
        default="outputs/presentation/rendered_preview",
        help="Directory containing slide-*.png previews.",
    )
    parser.add_argument(
        "--output",
        default="outputs/presentation/stablecoin_yield_presentation_contact_sheet.png",
        help="Output contact sheet path.",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    preview_dir = root / args.preview_dir
    output = root / args.output
    files = sorted(preview_dir.glob("slide-*.png"))
    if not files:
        raise FileNotFoundError(f"No slide previews found in {preview_dir}")
    cols = 2
    rows = math.ceil(len(files) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(9, rows * 2.8))
    axes_list = list(axes.flat) if hasattr(axes, "flat") else [axes]
    for ax in axes_list:
        ax.axis("off")
    for ax, path in zip(axes_list, files, strict=False):
        ax.imshow(mpimg.imread(path))
        ax.set_title(path.stem, loc="left", fontsize=8)
    fig.tight_layout(pad=1.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"contact_sheet={output.relative_to(root)}")


if __name__ == "__main__":
    main()

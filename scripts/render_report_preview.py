from __future__ import annotations

import argparse
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default="outputs/report/stablecoin_yield_report.pdf")
    parser.add_argument("--output-dir", default="outputs/report/rendered_preview")
    parser.add_argument("--contact-sheet", default="outputs/report/stablecoin_yield_report_contact_sheet.png")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    pdf = root / args.pdf
    output_dir = root / args.output_dir
    contact_sheet = root / args.contact_sheet
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("page-*.png"):
        old.unlink()
    doc = fitz.open(pdf)
    page_images = []
    for index, page in enumerate(doc):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        path = output_dir / f"page-{index + 1:02d}.png"
        pixmap.save(path)
        page_images.append(path)
    write_contact_sheet(page_images, contact_sheet)
    print(f"pages={doc.page_count}")
    print(f"preview={output_dir.relative_to(root)}")
    print(f"contact_sheet={contact_sheet.relative_to(root)}")


def write_contact_sheet(page_images: list[Path], output: Path) -> None:
    thumb_width, thumb_height = 320, 452
    margin = 18
    cols = 2
    rows = math.ceil(len(page_images) / cols)
    sheet = Image.new(
        "RGB",
        (cols * thumb_width + (cols + 1) * margin, rows * (thumb_height + 34) + (rows + 1) * margin),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(page_images):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height))
        x = margin + (index % cols) * (thumb_width + margin)
        y = margin + (index // cols) * (thumb_height + 34 + margin)
        sheet.paste(image, (x, y))
        draw.text((x, y + thumb_height + 6), path.stem, fill=(0, 0, 0))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


if __name__ == "__main__":
    main()

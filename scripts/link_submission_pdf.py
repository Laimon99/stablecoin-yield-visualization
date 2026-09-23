"""Preserve the PowerPoint export and embed actual PDF URI annotations."""
import argparse
from pathlib import Path

import fitz


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite {args.output}")
    document = fitz.open(args.input)
    targets = {
        "github.com/Laimon99/stablecoin-yield-visualization": "https://github.com/Laimon99/stablecoin-yield-visualization",
        "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
        "s.ragusini@campus.unimib.it": "mailto:s.ragusini@campus.unimib.it",
    }
    count = 0
    for page in document:
        for label, uri in targets.items():
            for rect in page.search_for(label):
                page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": uri})
                count += 1
    if count < 4:
        raise ValueError("Expected visible repository, licence and author links")
    metadata = document.metadata
    metadata.update({"title": "Stablecoin Yield - Simone Ragusini 945119", "author": "Simone Ragusini", "subject": "Refined Data Visualization submission, September 2026"})
    document.set_metadata(metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document.save(args.output, garbage=4, deflate=True)
    with fitz.open(args.output) as check:
        assert len(check) == 17
        assert any(link.get("uri") == targets["github.com/Laimon99/stablecoin-yield-visualization"] for page in check for link in page.get_links())
    print(f"Saved {args.output} with {count} embedded links")


if __name__ == "__main__":
    main()

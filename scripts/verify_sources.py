from __future__ import annotations

from pathlib import Path

from stablecoin_yield.source_verification import verify_sources


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    for result in verify_sources(root):
        row_count = result.summary.get("row_count", result.summary.get("stablecoin_count"))
        print(f"{result.source} {result.endpoint} status={result.status_code} rows={row_count}")
        print(f"  raw={result.raw_file}")
        print(f"  summary={result.summary}")


if __name__ == "__main__":
    main()


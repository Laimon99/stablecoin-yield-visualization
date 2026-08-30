from __future__ import annotations

import shutil
from pathlib import Path

from stablecoin_yield.config import get_paths


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = get_paths(root)
    targets = [
        paths.outputs_dir,
        paths.staging_dir,
        paths.processed_dir,
        paths.analytical_dir,
    ]
    for target in targets:
        resolved = target.resolve()
        if root.resolve() not in resolved.parents:
            raise RuntimeError(f"Refusing to delete path outside project root: {resolved}")
        if resolved.exists():
            shutil.rmtree(resolved)
            print(f"removed={target.relative_to(root)}")


if __name__ == "__main__":
    main()

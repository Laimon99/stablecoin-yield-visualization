"""Package public code and curated outputs, excluding raw data and secrets."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from stablecoin_yield.reproducibility import build_release_manifest, iter_release_files


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = build_release_manifest(root, "full")
    files = [*iter_release_files(root), manifest.path]
    output = root / "outputs/delivery/Simone_Ragusini_945119_Stablecoin_Yield.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(set(files)):
            relative = path.relative_to(root).as_posix()
            if relative.startswith(("data/", ".git/", ".venv/", "tmp/")) or relative == ".env":
                raise ValueError(f"Non-public file selected for packaging: {relative}")
            archive.write(path, f"stablecoin-yield/{relative}")
    print(f"Submission archive: {output}, {len(set(files))} files")


if __name__ == "__main__":
    main()

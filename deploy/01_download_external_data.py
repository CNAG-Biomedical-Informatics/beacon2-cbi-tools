#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import gdown


FILES = {
    "data.tar.gz.md5": "1g7bUAdOj5HWos03_dWsH0Y2V9EHx54Qe",
    "data.tar.gz.part-00": "1GOy9yUS71UP3pYhV1KZORbxA7rPDxH3a",
    "data.tar.gz.part-01": "19vTasSHcX47qSh_VvUkfnr-UHEvfjyR6",
    "data.tar.gz.part-02": "1HeURlpWk1CcjqckE0g7Vp_G2-rBz-Dej",
    "data.tar.gz.part-03": "1lwx3yeeal3otHMGyEJEsl5qqvhXUw32q",
    "data.tar.gz.part-04": "1zp9-Tl4EyXFXbyUq7MAr7g5NdmpgMt8F",
    "data.tar.gz.part-05": "1dUTRxjKheNZ5OoSutvdxPJ8NkYbKohbc",
    "data.tar.gz.part-06": "1-wZPfReNAmKkY9ZWNrFmqb0pwQxvhN1w",
}


def download_bundle(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, file_id in FILES.items():
        destination = output_dir / filename
        if destination.is_file():
            print(f"Found {destination}; skipping")
            continue
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        print(f"Downloading {filename}")
        result = gdown.download(url, str(destination), quiet=False, fuzzy=True)
        if result is None or not destination.is_file():
            raise RuntimeError(f"Download failed: {filename}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download the external bff-tools annotation-data bundle"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("."),
        help="directory for archive parts (default: current directory)",
    )
    args = parser.parse_args()
    download_bundle(args.out_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

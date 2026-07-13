#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from bff_tools.parity import compare_bff_files


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON_CONVERTER = ROOT / "src" / "bff_tools" / "vcf2bff.py"
DEFAULT_FIXTURE = ROOT / "testdata" / "vcf" / "cineca_annotated" / "fully_annotated.vcf.gz"


def converter_arguments(input_path: Path, output_dir: Path) -> list[str]:
    return [
        "--input",
        str(input_path),
        "--genome",
        "hg19",
        "--dataset-id",
        "CINECA_synthetic_cohort_EUROPE_UK1",
        "--project-dir",
        "cineca_annotated_fixture",
        "--out-dir",
        str(output_dir),
        "--threads",
        "1",
    ]


def python_command(path: Path) -> list[str]:
    return [sys.executable, str(path)] if path.suffix == ".py" else [str(path)]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Python and Perl VCF converters and compare BFF output"
    )
    parser.add_argument("--python-converter", type=Path, default=DEFAULT_PYTHON_CONVERTER)
    parser.add_argument(
        "--perl-converter",
        type=Path,
        required=True,
        help="legacy vcf2bff.pl from a separate checkout",
    )
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()

    python_converter = args.python_converter.resolve()
    perl_converter = args.perl_converter.resolve()
    fixture = args.fixture.resolve()
    if not python_converter.is_file():
        parser.error(f"Python converter does not exist: {python_converter}")
    if not perl_converter.is_file():
        parser.error(f"Perl converter does not exist: {perl_converter}")
    if not fixture.is_file():
        parser.error(f"VCF fixture does not exist: {fixture}")

    with tempfile.TemporaryDirectory() as tmpdir:
        temp = Path(tmpdir)
        perl_output = temp / "perl"
        python_output = temp / "python"
        perl_output.mkdir()
        python_output.mkdir()

        started = time.perf_counter()
        print("Running Perl converter...", flush=True)
        subprocess.run(
            ["perl", str(perl_converter), *converter_arguments(fixture, perl_output)],
            cwd=ROOT,
            check=True,
        )
        perl_seconds = time.perf_counter() - started
        print(f"Perl converter: {perl_seconds:.1f}s", flush=True)

        started = time.perf_counter()
        print("Running Python converter...", flush=True)
        subprocess.run(
            [*python_command(python_converter), *converter_arguments(fixture, python_output)],
            cwd=ROOT,
            check=True,
        )
        python_seconds = time.perf_counter() - started
        print(f"Python converter: {python_seconds:.1f}s", flush=True)

        result = compare_bff_files(
            perl_output / "genomicVariationsVcf.json.gz",
            python_output / "genomicVariationsVcf.json.gz",
        )
    if not result.equal:
        print(f"First semantic difference: record {result.first_difference}")
        print(f"JSON path: {result.path}")
        print(f"Perl: {json.dumps(result.expected, ensure_ascii=False)[:1000]}")
        print(f"Python: {json.dumps(result.actual, ensure_ascii=False)[:1000]}")
        return 1
    print(f"Python/Perl parity passed for {result.records} BFF record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

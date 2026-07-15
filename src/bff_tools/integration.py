from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

from .config import DATA_ROOT_ENV
from .parity import ParityError, compare_bff_files
from .resource_installer import resolve_data_directory


ASSET_DIR = Path(__file__).with_name("integration_assets")
INPUT_VCF = ASSET_DIR / "test_1000G.vcf.gz"
PARAMETERS = ASSET_DIR / "param.yaml"
EXPECTED_BFF = ASSET_DIR / "genomicVariationsVcf.json.gz"
ANNOTATED_VCF = ASSET_DIR / "test_1000G.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz"
REQUIRED_ASSETS = (INPUT_VCF, PARAMETERS, EXPECTED_BFF, ANNOTATED_VCF)


class IntegrationTestError(RuntimeError):
    pass


def _check_assets() -> None:
    missing = [str(path) for path in REQUIRED_ASSETS if not path.is_file()]
    if missing:
        raise IntegrationTestError(
            "The installed integration fixture is incomplete: " + ", ".join(missing)
        )


def _run_command(
    command: list[str],
    *,
    env: dict[str, str],
    run: Callable[..., subprocess.CompletedProcess[object]],
) -> None:
    result = run(command, env=env, check=False)
    if result.returncode != 0:
        raise IntegrationTestError(
            f"Integration command failed with exit code {result.returncode}: "
            + " ".join(command)
        )


def _format_difference(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)[:1000]


def _run_in_project(
    project_dir: Path,
    *,
    data_dir: Path,
    threads: int,
    verbose: bool,
    run: Callable[..., subprocess.CompletedProcess[object]],
) -> None:
    env = os.environ.copy()
    env[DATA_ROOT_ENV] = str(data_dir)
    executable = [sys.executable, "-m", "bff_tools"]
    conversion = executable + [
        "vcf",
        "--input",
        str(INPUT_VCF),
        "--param",
        str(PARAMETERS),
        "--annotate",
        "--no-browser",
        "--project-dir",
        str(project_dir),
        "--threads",
        str(threads),
        "--no-emoji",
        "--no-color",
    ]
    if verbose:
        conversion.append("--verbose")

    print("Running normalization, SnpEff, dbNSFP, ClinVar, and COSMIC integration")
    _run_command(conversion, env=env, run=run)

    actual = project_dir / "vcf" / "genomicVariationsVcf.json.gz"
    validation = executable + [
        "validate",
        "--input",
        str(actual),
        "--gv-vcf",
        "--no-emoji",
        "--no-color",
    ]
    _run_command(validation, env=env, run=run)

    try:
        result = compare_bff_files(EXPECTED_BFF, actual)
    except ParityError as exc:
        raise IntegrationTestError(f"Cannot compare integration output: {exc}") from exc
    if not result.equal:
        raise IntegrationTestError(
            f"Semantic difference at record {result.first_difference}, "
            f"JSON path {result.path}: expected {_format_difference(result.expected)}, "
            f"observed {_format_difference(result.actual)}"
        )
    print(f"Semantic parity passed for {result.records} record(s)")
    print("Full annotation integration passed")


def run_annotation_integration(
    *,
    data_dir: str | None = None,
    output_dir: str | None = None,
    threads: int = 1,
    verbose: bool = False,
    run: Callable[..., subprocess.CompletedProcess[object]] = subprocess.run,
) -> Path | None:
    if threads <= 0:
        raise IntegrationTestError("--threads requires a positive integer")
    _check_assets()
    resolved_data = resolve_data_directory(data_dir)
    if not resolved_data.is_dir():
        raise IntegrationTestError(
            f"External annotation directory does not exist: {resolved_data}"
        )

    if output_dir:
        project_dir = Path(output_dir).expanduser().resolve()
        if project_dir.exists():
            raise IntegrationTestError(
                f"Integration output already exists: {project_dir}"
            )
        project_dir.parent.mkdir(parents=True, exist_ok=True)
        _run_in_project(
            project_dir,
            data_dir=resolved_data,
            threads=threads,
            verbose=verbose,
            run=run,
        )
        print(f"Integration output retained in {project_dir}")
        return project_dir

    with tempfile.TemporaryDirectory(prefix="bff-tools-integration-") as tmpdir:
        _run_in_project(
            Path(tmpdir) / "annotation-integration",
            data_dir=resolved_data,
            threads=threads,
            verbose=verbose,
            run=run,
        )
    return None

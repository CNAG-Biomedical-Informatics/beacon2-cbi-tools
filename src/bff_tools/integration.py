from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

from . import console
from .config import DATA_ROOT_ENV
from .parity import ParityError, compare_bff_files
from .resource_installer import ResourceInstallError, resolve_data_directory
from .version import VERSION


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
    label: str,
    no_color: bool,
    env: dict[str, str],
    run: Callable[..., subprocess.CompletedProcess[object]],
) -> None:
    console.status_line("INFO", f"{label} started", no_color=no_color)
    result = run(command, env=env, check=False)
    if result.returncode != 0:
        console.status_line(
            "FAIL",
            f"{label} exited with status {result.returncode}",
            no_color=no_color,
        )
        raise IntegrationTestError(
            f"Integration command failed with exit code {result.returncode}: "
            + " ".join(command)
        )
    console.status_line("PASS", f"{label} completed", no_color=no_color)


def _format_difference(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)[:1000]


def _run_in_project(
    project_dir: Path,
    *,
    data_dir: Path,
    threads: int,
    verbose: bool,
    no_color: bool,
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

    _run_command(
        conversion,
        label="Annotation and VCF-to-BFF pipeline",
        no_color=no_color,
        env=env,
        run=run,
    )

    actual = project_dir / "vcf" / "genomicVariationsVcf.json.gz"
    validation = executable + [
        "validate",
        "--input",
        str(actual),
        "--gv-vcf",
        "--no-emoji",
        "--no-color",
    ]
    _run_command(
        validation,
        label="BFF schema validation",
        no_color=no_color,
        env=env,
        run=run,
    )

    console.status_line("INFO", "Semantic BFF comparison started", no_color=no_color)
    try:
        result = compare_bff_files(EXPECTED_BFF, actual)
    except ParityError as exc:
        console.status_line("FAIL", "Semantic BFF comparison failed", no_color=no_color)
        raise IntegrationTestError(f"Cannot compare integration output: {exc}") from exc
    if not result.equal:
        console.status_line("FAIL", "Semantic BFF comparison failed", no_color=no_color)
        raise IntegrationTestError(
            f"Semantic difference at record {result.first_difference}, "
            f"JSON path {result.path}: expected {_format_difference(result.expected)}, "
            f"observed {_format_difference(result.actual)}"
        )
    console.status_line(
        "PASS",
        f"Semantic parity passed for {result.records} record(s)",
        no_color=no_color,
    )


def run_annotation_integration(
    *,
    data_dir: str | None = None,
    output_dir: str | None = None,
    threads: int = 1,
    verbose: bool = False,
    no_color: bool = False,
    run: Callable[..., subprocess.CompletedProcess[object]] = subprocess.run,
) -> Path | None:
    console.section(
        f"Beacon v2 CBI Tools {VERSION} test",
        console.CYAN,
        no_color=no_color,
    )
    print("=" * 48)
    if threads <= 0:
        console.status_line("FAIL", "Thread count must be positive", no_color=no_color)
        raise IntegrationTestError("--threads requires a positive integer")
    try:
        _check_assets()
    except IntegrationTestError:
        console.status_line("FAIL", "Packaged integration fixtures are incomplete", no_color=no_color)
        raise
    console.status_line("PASS", "Packaged integration fixtures are available", no_color=no_color)

    try:
        resolved_data = resolve_data_directory(data_dir)
    except ResourceInstallError:
        console.status_line("FAIL", "Annotation resource root is not configured", no_color=no_color)
        raise
    if not resolved_data.is_dir():
        console.status_line(
            "FAIL",
            f"Annotation resource root does not exist: {resolved_data}",
            no_color=no_color,
        )
        raise IntegrationTestError(
            f"External annotation directory does not exist: {resolved_data}"
        )
    console.status_line(
        "PASS",
        f"Annotation resource root: {resolved_data}",
        no_color=no_color,
    )

    if output_dir:
        project_dir = Path(output_dir).expanduser().resolve()
        if project_dir.exists():
            console.status_line(
                "FAIL",
                f"Integration output already exists: {project_dir}",
                no_color=no_color,
            )
            raise IntegrationTestError(
                f"Integration output already exists: {project_dir}"
            )
        project_dir.parent.mkdir(parents=True, exist_ok=True)
        _run_in_project(
            project_dir,
            data_dir=resolved_data,
            threads=threads,
            verbose=verbose,
            no_color=no_color,
            run=run,
        )
        console.status_line(
            "INFO",
            f"Integration output retained in {project_dir}",
            no_color=no_color,
        )
        console.section("Summary", console.WHITE, no_color=no_color)
        console.status_line(
            "PASS",
            "Packaged compact annotation integration passed",
            no_color=no_color,
        )
        return project_dir

    with tempfile.TemporaryDirectory(prefix="bff-tools-integration-") as tmpdir:
        _run_in_project(
            Path(tmpdir) / "annotation-integration",
            data_dir=resolved_data,
            threads=threads,
            verbose=verbose,
            no_color=no_color,
            run=run,
        )
    console.section("Summary", console.WHITE, no_color=no_color)
    console.status_line(
        "PASS",
        "Packaged compact annotation integration passed",
        no_color=no_color,
    )
    return None

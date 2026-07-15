from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .browser import BrowserError, generate_browser_report
from .integration import ANNOTATED_VCF
from .validator import ValidatorError, validate_inputs
from .vcf2bff import ConversionError, convert_vcf


PANEL_DIR = Path(__file__).with_name("panels")
DEMO_DATASET_ID = "bff-tools-demo"


class DemoError(RuntimeError):
    pass


@dataclass(frozen=True)
class DemoResult:
    output_dir: Path
    bff_path: Path
    browser_path: Path | None
    records: int


def _write_readme(result: DemoResult) -> None:
    browser_line = (
        f"- browser/{result.browser_path.name}: standalone variant browser\n"
        if result.browser_path
        else "- Browser generation was disabled for this run.\n"
    )
    (result.output_dir / "README.txt").write_text(
        "BFF Tools demo\n"
        "==============\n\n"
        "This directory was generated from the fully annotated VCF fixture "
        "packaged with Beacon v2 CBI Tools. No external annotation databases "
        "were used during this demo run.\n\n"
        "Outputs\n"
        "-------\n"
        f"- vcf/{result.bff_path.name}: {result.records} Beacon Friendly Format records\n"
        f"{browser_line}\n"
        "Open the HTML file directly in a modern browser. For raw VCF input, "
        "install the external annotation bundle and use `bff-tools vcf`.\n",
        encoding="utf-8",
    )


def run_demo(output_dir: Path, *, browser: bool = True) -> DemoResult:
    destination = output_dir.expanduser().resolve()
    if destination.exists():
        raise DemoError(f"Demo output already exists: {destination}")
    if not ANNOTATED_VCF.is_file():
        raise DemoError(f"Packaged demo fixture is missing: {ANNOTATED_VCF}")

    try:
        vcf_dir = destination / "vcf"
        vcf_dir.mkdir(parents=True)
        bff_path, records = convert_vcf(
            ANNOTATED_VCF,
            vcf_dir,
            genome="hs37",
            dataset_id=DEMO_DATASET_ID,
            project_dir=str(destination),
            threads=1,
        )
        report = validate_inputs([bff_path], streamed_genomic=True)
        if not report.ok:
            first = report.issues[0]
            raise DemoError(
                f"Generated demo BFF failed validation at record {first.row}: "
                f"{first.message}"
            )

        browser_path: Path | None = None
        if browser:
            browser_path = destination / "browser" / "bff-tools-demo.html"
            generate_browser_report(
                bff_path,
                PANEL_DIR,
                browser_path,
                project_id=DEMO_DATASET_ID,
                job_id="packaged-demo",
            )
        result = DemoResult(destination, bff_path, browser_path, records)
        _write_readme(result)
    except DemoError:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    except (
        BrowserError,
        ConversionError,
        KeyError,
        OSError,
        ValidatorError,
        ValueError,
    ) as exc:
        shutil.rmtree(destination, ignore_errors=True)
        raise DemoError(f"Cannot generate demo: {exc}") from exc

    return result

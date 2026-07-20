from __future__ import annotations

import os
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from . import console
from .browser import TABULATOR_CSS, TABULATOR_JS, TEMPLATE_FILE
from .config import (
    CONFIG_PATH_ENV,
    DATA_ROOT_ENV,
    DEFAULT_DATA_ROOT,
    PACKAGED_CONFIG_PATH,
    ConfigError,
    default_config_path,
    load_yaml_file,
    read_config_file,
)
from .integration import REQUIRED_ASSETS
from .resource_installer import (
    BUNDLE_REVISION,
    EXPECTED_DIRECTORIES,
    INSTALL_MARKER,
)
from .validator import ValidatorError, current_schema_version, template_path, validate_schemas
from .version import VERSION


PACKAGE_DIR = Path(__file__).resolve().parent
PANEL_DIR = PACKAGE_DIR / "panels"
RUNTIME_ASSETS = (
    PACKAGED_CONFIG_PATH,
    PACKAGE_DIR / "vcf2bff.py",
    PACKAGE_DIR / "pipeline" / "partial" / "run_vcf2bff.sh",
    PACKAGE_DIR / "pipeline" / "partial" / "run_tsv2vcf.sh",
)
BROWSER_ASSETS = (
    TEMPLATE_FILE,
    TABULATOR_CSS,
    TABULATOR_JS,
    PANEL_DIR / "Invitae_Multi_Cancer.lst",
    PANEL_DIR / "cardiopathy.lst",
    PANEL_DIR / "exome.lst",
    PANEL_DIR / "protein-coding_gene.txt",
)


@dataclass(frozen=True)
class DoctorCheck:
    status: str
    label: str
    detail: str
    required: bool = True
    fix: str | None = None


def _check_files(label: str, paths: tuple[Path, ...]) -> DoctorCheck:
    missing: list[str] = []
    for path in paths:
        try:
            if not path.is_file() or path.stat().st_size == 0:
                missing.append(str(path))
        except OSError:
            missing.append(str(path))
    if missing:
        return DoctorCheck(
            "FAIL",
            label,
            "missing " + ", ".join(missing),
            fix="Reinstall beacon2-cbi-tools from the selected distribution.",
        )
    return DoctorCheck("PASS", label, f"{len(paths)} required file(s) available")


def _command_check(label: str, *commands: str) -> DoctorCheck:
    available = [(command, shutil.which(command)) for command in commands]
    for command, path in available:
        if path:
            return DoctorCheck("PASS", label, f"{command} at {path}")
    return DoctorCheck(
        "FAIL",
        label,
        "not found: " + " or ".join(commands),
        fix=f"Install {' or '.join(commands)} and ensure it is available on PATH.",
    )


def _commands_check(label: str, *commands: str) -> DoctorCheck:
    resolved = {command: shutil.which(command) for command in commands}
    missing = [command for command, path in resolved.items() if not path]
    if missing:
        return DoctorCheck(
            "FAIL",
            label,
            "not found: " + ", ".join(missing),
            fix=f"Install {', '.join(missing)} and ensure it is available on PATH.",
        )
    detail = ", ".join(f"{command} at {resolved[command]}" for command in commands)
    return DoctorCheck("PASS", label, detail)


def _compressor_check() -> DoctorCheck:
    candidates = (Path("/usr/bin/pigz"), Path("/bin/gzip"))
    for path in candidates:
        if path.is_file() and os.access(path, os.X_OK):
            return DoctorCheck("PASS", "Compression", str(path))
    return DoctorCheck(
        "FAIL",
        "Compression",
        "neither /usr/bin/pigz nor /bin/gzip is executable",
        fix="Install gzip, or pigz at /usr/bin/pigz for threaded compression.",
    )


def _schema_check() -> DoctorCheck:
    try:
        version = current_schema_version()
        checked = validate_schemas(announce=False)
    except (OSError, ValidatorError) as exc:
        return DoctorCheck(
            "FAIL",
            "Beacon schemas",
            str(exc),
            fix="Reinstall beacon2-cbi-tools or select a valid packaged schema snapshot.",
        )
    return DoctorCheck(
        "PASS",
        "Beacon schemas",
        f"{version} ({len(checked)} schemas valid)",
    )


def _capability(label: str, checks: tuple[DoctorCheck, ...]) -> DoctorCheck:
    failed = [check.label for check in checks if check.status == "FAIL"]
    if failed:
        return DoctorCheck("FAIL", label, "blocked by " + ", ".join(failed))
    return DoctorCheck("PASS", label, "ready")


def _config_selection(config_file: str | None) -> tuple[Path, str, bool]:
    if config_file:
        return Path(config_file).expanduser().resolve(), "--config", True
    configured = os.environ.get(CONFIG_PATH_ENV)
    if configured:
        return Path(configured).expanduser().resolve(), CONFIG_PATH_ENV, True
    path = default_config_path()
    source = "packaged default" if path == PACKAGED_CONFIG_PATH else "repository default"
    return path, source, False


def _data_root_from_config(config: dict[str, object]) -> tuple[Path, str, bool]:
    uses_data_root = any(
        isinstance(value, str) and "{base}" in value for value in config.values()
    )
    configured = os.environ.get(DATA_ROOT_ENV)
    if configured:
        return Path(configured).expanduser().resolve(), DATA_ROOT_ENV, uses_data_root
    if config.get("base"):
        return Path(str(config["base"])).expanduser().resolve(), "config base", uses_data_root
    return DEFAULT_DATA_ROOT.resolve(), "packaged default", uses_data_root


def _bundle_check(data_root: Path) -> DoctorCheck:
    missing = [name for name in EXPECTED_DIRECTORIES if not (data_root / name).is_dir()]
    marker = data_root / INSTALL_MARKER
    if not marker.is_file():
        return DoctorCheck(
            "FAIL",
            "Bundle revision",
            f"missing {marker.name}",
            required=False,
            fix=f"Install bundle {BUNDLE_REVISION} into a clean directory.",
        )
    try:
        revision = marker.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return DoctorCheck(
            "FAIL",
            "Bundle revision",
            str(exc),
            required=False,
            fix=f"Reinstall bundle {BUNDLE_REVISION}.",
        )
    if revision != BUNDLE_REVISION:
        return DoctorCheck(
            "FAIL",
            "Bundle revision",
            f"expected {BUNDLE_REVISION}, found {revision or '(empty)'}",
            required=False,
            fix=f"Install bundle {BUNDLE_REVISION} into a clean directory.",
        )
    if missing:
        return DoctorCheck(
            "FAIL",
            "Bundle revision",
            "missing " + ", ".join(missing),
            required=False,
            fix=f"Reinstall bundle {BUNDLE_REVISION} into a clean directory.",
        )
    return DoctorCheck(
        "PASS",
        "Bundle revision",
        f"{BUNDLE_REVISION} marker and layout verified",
        required=False,
    )


def _annotation_checks(
    config_file: str | None,
    genome: str,
) -> tuple[list[DoctorCheck], DoctorCheck]:
    resources: list[DoctorCheck] = []
    try:
        config_path, config_source, custom_config = _config_selection(config_file)
    except ConfigError as exc:
        failure = DoctorCheck(
            "FAIL",
            "Raw VCF annotation",
            str(exc),
            fix=f"Correct {CONFIG_PATH_ENV} or remove it to use the packaged layout.",
        )
        resources.append(DoctorCheck("FAIL", "Configuration", str(exc), required=False))
        return resources, failure

    if not config_path.is_file():
        detail = f"{config_path} ({config_source}) does not exist"
        resources.append(DoctorCheck("FAIL", "Configuration", detail, required=False))
        return resources, DoctorCheck(
            "FAIL",
            "Raw VCF annotation",
            detail,
            fix="Select an existing YAML configuration file.",
        )

    try:
        raw_config = load_yaml_file(config_path)
    except ConfigError as exc:
        resources.append(DoctorCheck("FAIL", "Configuration", str(exc), required=False))
        return resources, DoctorCheck(
            "FAIL",
            "Raw VCF annotation",
            str(exc),
            fix="Correct the annotation YAML configuration.",
        )

    resources.append(
        DoctorCheck(
            "PASS",
            "Configuration",
            f"{config_path} ({config_source})",
            required=False,
        )
    )
    data_root, data_source, uses_data_root = _data_root_from_config(raw_config)
    resources.append(
        DoctorCheck(
            "INFO",
            "Data root",
            (
                f"{data_root} ({data_source})"
                if uses_data_root
                else f"not used by custom absolute paths ({data_source}: {data_root})"
            ),
            required=False,
        )
    )

    bundle_ok = True
    if not custom_config and uses_data_root:
        if not data_root.is_dir():
            explicitly_selected = DATA_ROOT_ENV in os.environ
            status = "FAIL" if explicitly_selected else "WARN"
            resources[-1] = DoctorCheck(
                status,
                "Data root",
                f"{data_root} ({data_source}) does not exist",
                required=False,
                fix=(
                    f"Set {DATA_ROOT_ENV} to an installed bundle or run "
                    "bff-tools install-resources."
                ),
            )
            resources.append(
                DoctorCheck(
                    "SKIP",
                    "Bundle revision",
                    "not checked because the data root is unavailable",
                    required=False,
                )
            )
            return resources, DoctorCheck(
                status,
                "Raw VCF annotation",
                f"{DATA_ROOT_ENV} is not configured"
                if status == "WARN"
                else f"configured data root does not exist: {data_root}",
                required=status == "FAIL",
                fix=(
                    f"Set {DATA_ROOT_ENV} to an installed bundle or run "
                    "bff-tools install-resources."
                ),
            )
        resources[-1] = DoctorCheck(
            "PASS",
            "Data root",
            f"{data_root} ({data_source})",
            required=False,
        )
        bundle = _bundle_check(data_root)
        resources.append(bundle)
        bundle_ok = bundle.status == "PASS"
    elif custom_config:
        resources.append(
            DoctorCheck(
                "INFO",
                "Bundle revision",
                "not required for a custom resource layout",
                required=False,
            )
        )

    try:
        resolved_config = read_config_file(
            str(config_path),
            mode="vcf",
            annotate=True,
            genome=genome,
            browser=False,
        )
        tmpdir = resolved_config.get("tmpdir")
        if tmpdir and not os.access(str(tmpdir), os.W_OK):
            raise ConfigError(f"Configured tmpdir is not writable: {tmpdir}")
    except ConfigError as exc:
        resources.append(
            DoctorCheck(
                "FAIL",
                "Annotation profile",
                str(exc),
                required=False,
                fix=f"Correct the {genome} paths in {config_path}.",
            )
        )
        return resources, DoctorCheck(
            "FAIL",
            "Raw VCF annotation",
            f"{genome} profile is incomplete",
            fix=f"Correct the reported {genome} resource or executable path.",
        )

    resources.append(
        DoctorCheck(
            "PASS",
            "Annotation profile",
            f"{genome} executables and resources available",
            required=False,
        )
    )
    if not bundle_ok:
        return resources, DoctorCheck(
            "FAIL",
            "Raw VCF annotation",
            f"standard bundle {BUNDLE_REVISION} is not verified",
            fix=f"Install bundle {BUNDLE_REVISION} into a clean directory.",
        )
    return resources, DoctorCheck("PASS", "Raw VCF annotation", f"{genome} profile ready")


def _print_check(check: DoctorCheck, *, no_color: bool) -> None:
    tag = console.status_tag(check.status, no_color=no_color)
    print(f"{tag} {check.label:<28} {check.detail}")
    if check.fix:
        print(f"       Fix: {check.fix}")


def _print_section(title: str, checks: list[DoctorCheck], *, no_color: bool) -> None:
    console.section(title, console.BLUE, no_color=no_color)
    for check in checks:
        _print_check(check, no_color=no_color)


def run_doctor(
    *,
    config_file: str | None = None,
    genome: str = "hg19",
    no_color: bool = False,
) -> int:
    """Report installation readiness without executing a data pipeline."""
    selected_genome = "hs37" if genome == "b37" else genome
    python_ok = sys.version_info >= (3, 10)
    application = DoctorCheck("PASS", "Application", VERSION)
    python = DoctorCheck(
        "PASS" if python_ok else "FAIL",
        "Python runtime",
        f"{platform.python_version()} at {sys.executable}",
        fix=None if python_ok else "Use Python 3.10 or newer.",
    )
    runtime = _check_files("Runtime assets", RUNTIME_ASSETS)
    metadata = _check_files("Metadata template", (template_path(),))
    browser = _check_files("Browser assets", BROWSER_ASSETS)
    fixtures = _check_files("Integration fixtures", tuple(REQUIRED_ASSETS))
    schemas = _schema_check()
    bash = _command_check("Bash", "bash")
    compression = _compressor_check()
    filters = _commands_check("Browser filters", "grep", "zgrep")

    core = [
        application,
        python,
        DoctorCheck(
            "INFO",
            "Host platform",
            f"{platform.system()} {platform.machine()}",
            required=False,
        ),
        runtime,
        metadata,
        browser,
        fixtures,
        schemas,
        bash,
        compression,
        filters,
    ]
    resources, annotation = _annotation_checks(config_file, selected_genome)
    capabilities = [
        _capability("Metadata validation", (metadata, schemas)),
        _capability("Annotated VCF conversion", (runtime, bash, compression)),
        _capability("Standalone browser", (browser, filters)),
        annotation,
    ]
    integration = _capability("Packaged integration test", (fixtures, annotation))
    if annotation.status == "WARN" and fixtures.status == "PASS":
        integration = DoctorCheck(
            "WARN",
            "Packaged integration test",
            "fixture ready; external annotation bundle not configured",
            required=False,
        )
    capabilities.append(integration)

    console.section(
        f"Beacon v2 CBI Tools {VERSION} doctor",
        console.CYAN,
        no_color=no_color,
    )
    print("=" * 48)
    _print_section("Core", core, no_color=no_color)
    print()
    _print_section("Capabilities", capabilities, no_color=no_color)
    print()
    _print_section("Annotation Resources", resources, no_color=no_color)

    gate_checks = [*core, annotation]
    failures = [
        check
        for check in gate_checks
        if check.required and check.status == "FAIL"
    ]
    print()
    console.section("Summary", console.WHITE, no_color=no_color)
    if failures:
        _print_check(
            DoctorCheck(
                "FAIL",
                "Status",
                f"NOT READY ({len(failures)} failed check(s))",
            ),
            no_color=no_color,
        )
        return 1

    detail = "READY" if annotation.status == "PASS" else "CORE READY (annotation not configured)"
    _print_check(DoctorCheck("PASS", "Status", detail), no_color=no_color)
    return 0

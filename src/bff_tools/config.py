from __future__ import annotations

import os
import platform
import shutil
import socket
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
PACKAGE_DIR = Path(__file__).resolve().parent


class ConfigError(RuntimeError):
    pass


def load_yaml_file(path: Path, allowed_keys: Iterable[str] | None = None) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except OSError as exc:
        raise ConfigError(f"Cannot read YAML file <{path}>: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Cannot parse YAML file <{path}>: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Expected a mapping in {path}")
    if allowed_keys is not None:
        allowed = set(allowed_keys)
        for key in data.keys():
            if key not in allowed:
                raise ConfigError(f"Invalid parameter '{key}' in {path}")
    return data


def default_config_path() -> Path:
    user = os.environ.get("LOGNAME") or os.environ.get("USER") or ""
    host = socket.gethostname()
    if user == "mrueda" and host in {"mrueda-ws1", "mrueda-ws5"}:
        return ROOT_DIR / "bin" / "mrueda_ws1_config.yaml"
    return ROOT_DIR / "bin" / "config.yaml"


def _require_config_value(config: dict[str, Any], key: str, context: str) -> str:
    value = config.get(key)
    if value in {None, ""}:
        raise ConfigError(f"Configuration key '{key}' is required for {context}")
    return str(value)


def _require_file(config: dict[str, Any], key: str, context: str) -> None:
    value = _require_config_value(config, key, context)
    if not Path(value).is_file():
        raise ConfigError(f"Configured {key} file does not exist: {value}")


def _require_directory(config: dict[str, Any], key: str, context: str) -> None:
    value = _require_config_value(config, key, context)
    if not Path(value).is_dir():
        raise ConfigError(f"Configured {key} directory does not exist: {value}")


def _require_executable(config: dict[str, Any], key: str, context: str) -> None:
    value = _require_config_value(config, key, context)
    candidate = Path(value)
    if candidate.parent != Path("."):
        available = candidate.is_file() and os.access(candidate, os.X_OK)
    else:
        available = shutil.which(value) is not None
    if not available:
        raise ConfigError(f"Configured {key} executable is not available: {value}")


def read_config_file(
    config_file: str | None,
    *,
    mode: str = "vcf",
    annotate: bool = False,
    genome: str = "hg19",
    browser: bool = False,
) -> dict[str, Any]:
    config_path = Path(config_file).resolve() if config_file else default_config_path()
    config = load_yaml_file(config_path) if config_path.is_file() else {}

    arch = platform.machine()
    if arch == "x86_64":
        arch = "x86_64"
    elif arch == "aarch64":
        arch = "arm64"
    config["arch"] = arch

    base = config.get("base", "")

    for key, value in list(config.items()):
        if isinstance(value, str):
            config[key] = value.replace("{arch}", arch).replace("{base}", str(base))

    for suffix in ("cosmic", "dbnsfp", "clinvar"):
        hg19_key = f"hg19{suffix}"
        if hg19_key in config:
            config.setdefault(f"hs37{suffix}", config[hg19_key])
    config.setdefault("tmpdir", "/tmp")
    config.setdefault("mem", "8G")
    config.setdefault("dbnsfpset", "all")
    config.setdefault("pythonbin", sys.executable)

    pipeline_dir = PACKAGE_DIR / "pipeline"
    partial_dir = pipeline_dir / "partial"
    config["bash4bff"] = str(partial_dir / "run_vcf2bff.sh")
    config["bash4tsv"] = str(partial_dir / "run_tsv2vcf.sh")
    config["vcf_converter"] = str(PACKAGE_DIR / "vcf_converter.py")
    config.setdefault("paneldir", str(PACKAGE_DIR / "panels"))

    _require_file(config, "bash4bff", "VCF conversion")
    _require_file(config, "vcf_converter", "VCF conversion")
    _require_executable(config, "pythonbin", "VCF conversion")

    if mode == "tsv":
        _require_file(config, "bash4tsv", "TSV conversion")
        _require_executable(config, "bcftools", "TSV conversion")
        _require_file(config, f"{genome}fasta", "TSV conversion")
        _require_directory(config, "tmpdir", "TSV conversion")

    if annotate:
        context = "the annotation profile"
        _require_executable(config, "bcftools", context)
        _require_executable(config, "javabin", context)
        for key in (
            "snpeff",
            "snpsift",
            f"{genome}fasta",
            f"{genome}clinvar",
            f"{genome}cosmic",
            f"{genome}dbnsfp",
        ):
            _require_file(config, key, context)
        _require_directory(config, "tmpdir", context)

    if browser:
        _require_directory(config, "paneldir", "browser report generation")

    if config["dbnsfpset"] not in {"all", "cnag"}:
        raise ConfigError("Only [cnag|all] values are accepted for 'dbnsfpset'")

    return config


def read_param_file(arg: dict[str, Any]) -> dict[str, Any]:
    param: dict[str, Any] = {
        "annotate": True,
        "center": "CNAG",
        "datasetid": "default_beacon_1",
        "genome": "hg19",
        "organism": "Homo sapiens",
        "projectdir": "beacon",
        "bff2html": False,
        "pipeline": {
            "vcf2bff": 0,
            "bff2html": 0,
            "tsv2vcf": 0,
        },
        "sampleid": "23andme_1",
        "technology": "Illumina HiSeq 2000",
    }

    if arg.get("paramfile"):
        loaded = load_yaml_file(Path(arg["paramfile"]).resolve(), allowed_keys=param.keys())
        param.update(loaded)

    cli_overrides = {
        "annotate": arg.get("annotate"),
        "bff2html": arg.get("browser"),
        "datasetid": arg.get("datasetid"),
        "genome": arg.get("genome"),
        "sampleid": arg.get("sampleid"),
    }
    for key, value in cli_overrides.items():
        if value is not None:
            param[key] = value

    if arg["mode"] == "tsv" and not bool(param["annotate"]):
        raise ConfigError("'annotate' must be enabled when using tsv mode")

    threads_host = os.cpu_count() or 1
    requested_threads = int(arg.get("threads") or max(1, threads_host - 1))
    jobid = f"{int(time.time())}{os.getpid():05d}"[-15:]
    param["jobid"] = jobid
    param["date"] = time.ctime()

    projectdir_override = arg.get("projectdir_override")
    if projectdir_override:
        projectdir = projectdir_override
        if Path(projectdir).is_dir():
            raise ConfigError(f"Sorry but the dir <{projectdir}> exists")
        param["projectdir"] = projectdir
    else:
        base_projectdir = str(param["projectdir"]).replace(" ", "_")
        param["projectdir"] = f"{base_projectdir}_{jobid}"

    param["log"] = str(Path(param["projectdir"]) / "log.json")
    param["hostname"] = socket.gethostname()
    param["user"] = os.environ.get("LOGNAME") or os.environ.get("USER") or "unknown"
    param["threadshost"] = int(threads_host)
    param["threads"] = requested_threads
    param["threadsless"] = requested_threads
    param["zip"] = "/usr/bin/pigz" if os.access("/usr/bin/pigz", os.X_OK) else "/bin/gzip"
    if str(param.get("organism", "")).lower() == "human":
        param["organism"] = "Homo sapiens"
    param["gvvcfjson"] = str(Path(param["projectdir"]) / "vcf" / "genomicVariationsVcf.json.gz")
    param["sampleid"] = str(param["sampleid"]).replace(" ", "_")

    if param["genome"] == "b37":
        param["genome"] = "hs37"
    if param["genome"] not in {"hg19", "hg38", "hs37"}:
        raise ConfigError("Please select a valid reference genome. The options are [hg19 hg38 hs37]")

    modes = {
        "vcf": {
            "vcf2bff": 1,
            "bff2html": int(bool(param.get("bff2html"))),
            "tsv2vcf": 0,
        },
        "tsv": {
            "vcf2bff": 1,
            "bff2html": int(bool(param.get("bff2html"))),
            "tsv2vcf": 1,
        },
    }
    if arg["mode"] not in modes:
        raise ConfigError(f"Invalid mode: {arg['mode']}")
    param["pipeline"].update(modes[arg["mode"]])

    return param

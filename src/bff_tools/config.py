from __future__ import annotations

import os
import platform
import socket
import time
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]

REQUIRED_CONFIG_KEYS = {
    "hs37fasta",
    "hg19fasta",
    "hg38fasta",
    "hg19clinvar",
    "hg38clinvar",
    "hg19cosmic",
    "hg38cosmic",
    "hg19dbnsfp",
    "hg38dbnsfp",
    "javabin",
    "snpeff",
    "snpsift",
    "bcftools",
    "mem",
    "tmpdir",
    "mongoimport",
    "mongostat",
    "mongodburi",
    "mongosh",
    "dbnsfpset",
}


class ConfigError(RuntimeError):
    pass


def load_yaml_file(path: Path, allowed_keys: Iterable[str] | None = None) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
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


def read_config_file(config_file: str | None) -> dict[str, Any]:
    config_path = Path(config_file).resolve() if config_file else default_config_path()
    config = load_yaml_file(config_path)

    missing = REQUIRED_CONFIG_KEYS.difference(config.keys())
    if missing:
        raise ConfigError(
            f"Missing required parameter(s) in configuration file: {', '.join(sorted(missing))}"
        )

    arch = platform.machine()
    if arch == "x86_64":
        arch = "x86_64"
    elif arch == "aarch64":
        arch = "arm64"
    config["arch"] = arch

    base = config.get("base")
    if not base:
        raise ConfigError("Missing 'base' in configuration")

    for key, value in list(config.items()):
        if isinstance(value, str):
            config[key] = value.replace("{arch}", arch).replace("{base}", str(base))

    config["hs37cosmic"] = config["hg19cosmic"]
    config["hs37dbnsfp"] = config["hg19dbnsfp"]
    config["hs37clinvar"] = config["hg19clinvar"]
    config.setdefault("tmpdir", "/tmp")
    config.setdefault("mem", "8G")
    config.setdefault("dbnsfpset", "all")

    for key, value in config.items():
        if key in {"mem", "dbnsfpset", "mongodburi", "arch"}:
            continue
        if not Path(str(value)).exists():
            raise ConfigError(
                f"We could not find <{value}> files\nPlease check for typos? in your <{config_path}> file"
            )

    internal_dir = ROOT_DIR / "pipeline" / "internal"
    complete_dir = internal_dir / "complete"
    partial_dir = internal_dir / "partial"
    javabin = config["javabin"]
    config["snpeff"] = f"{javabin} -Xmx{config['mem']} -jar {config['snpeff']}"
    config["snpsift"] = f"{javabin} -Xmx{config['mem']} -jar {config['snpsift']}"
    config["bash4bff"] = str(partial_dir / "run_vcf2bff.sh")
    config["bash4html"] = str(partial_dir / "run_bff2html.sh")
    config["bash4mongodb"] = str(partial_dir / "run_bff2mongodb.sh")
    config["bash4tsv"] = str(partial_dir / "run_tsv2vcf.sh")
    config["vcf2bff"] = str(complete_dir / "vcf2bff.pl")
    config["bff2json"] = str(complete_dir / "bff2json.pl")
    config["json2html"] = str(complete_dir / "bff2html.pl")
    config["browserdir"] = str(ROOT_DIR / "browser")
    config["assetsdir"] = str(ROOT_DIR / "utils" / "bff_browser" / "static" / "assets")
    config.setdefault("paneldir", str(Path(config["browserdir"]) / "data"))

    for key in ("bash4bff", "bash4html", "bash4mongodb", "bash4tsv", "vcf2bff", "bff2json", "json2html"):
        if not os.access(config[key], os.X_OK):
            raise ConfigError(f"You don't have +x permission for script <{config[key]}>")

    if config["dbnsfpset"] not in {"all", "cnag"}:
        raise ConfigError("Sorry only [cnag|all] values are accepted for <dbnsfpset>")

    return config


def read_param_file(arg: dict[str, Any]) -> dict[str, Any]:
    param: dict[str, Any] = {
        "annotate": True,
        "bff": {},
        "center": "CNAG",
        "datasetid": "default_beacon_1",
        "genome": "hg19",
        "organism": "Homo sapiens",
        "projectdir": "beacon",
        "bff2html": False,
        "pipeline": {
            "vcf2bff": 0,
            "bff2html": 0,
            "bff2mongodb": 0,
            "tsv2vcf": 0,
        },
        "sampleid": "23andme_1",
        "technology": "Illumina HiSeq 2000",
    }

    if arg.get("paramfile"):
        loaded = load_yaml_file(Path(arg["paramfile"]).resolve(), allowed_keys=param.keys())
        param.update(loaded)

    threads_host = os.cpu_count() or 1
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
    param["threadsless"] = threads_host - 1 if threads_host > 1 else 1
    param["zip"] = f"/usr/bin/pigz -p {param['threadsless']}" if os.access("/usr/bin/pigz", os.X_OK) else "/bin/gzip"
    if str(param.get("organism", "")).lower() == "human":
        param["organism"] = "Homo sapiens"
    param["gvvcfjson"] = str(Path(param["projectdir"]) / "vcf" / "genomicVariationsVcf.json.gz")
    param["sampleid"] = str(param["sampleid"]).replace(" ", "_")

    if arg["mode"] == "tsv" and not bool(param["annotate"]):
        raise ConfigError("'annotate' must be set to true when using tsv mode")

    if param["genome"] == "b37":
        param["genome"] = "hs37"
    if param["genome"] not in {"hg19", "hg38", "hs37"}:
        raise ConfigError("Please select a valid reference genome. The options are [hg19 hg38 hs37]")

    modes = {
        "full": {
            "vcf2bff": 1,
            "bff2html": int(bool(param.get("bff2html"))),
            "tsv2vcf": int(bool(param.get("tsv2vcf"))),
            "bff2mongodb": 1,
        },
        "vcf": {
            "vcf2bff": 1,
            "bff2html": int(bool(param.get("bff2html"))),
            "tsv2vcf": 0,
            "bff2mongodb": 0,
        },
        "tsv": {
            "vcf2bff": 1,
            "bff2html": int(bool(param.get("bff2html"))),
            "tsv2vcf": 1,
            "bff2mongodb": 0,
        },
        "load": {"vcf2bff": 0, "bff2html": 0, "bff2mongodb": 1, "tsv2vcf": 0},
    }
    if arg["mode"] not in modes:
        raise ConfigError(f"Invalid mode: {arg['mode']}")
    param["pipeline"].update(modes[arg["mode"]])

    if arg["mode"] in {"load", "full"}:
        collections = {"runs", "cohorts", "biosamples", "individuals", "genomicVariations", "analyses", "datasets"}
        if arg["mode"] == "load":
            collections.add("genomicVariationsVcf")
        user_collections = sorted(k for k in param.get("bff", {}).keys() if k != "metadatadir")
        metadata_dir = Path(param.get("bff", {}).get("metadatadir", ""))
        for collection in user_collections:
            if collection not in collections:
                raise ConfigError(
                    f"Collection: <{collection}> is not a valid value for bff:\nAllowed values are <{' '.join(sorted(collections))}>"
                )
            if collection == "genomicVariationsVcf":
                candidate = Path(param["bff"][collection])
            else:
                candidate = metadata_dir / param["bff"][collection]
            if not candidate.is_file():
                raise ConfigError(f"Collection: <{collection}> does not have a valid file <{candidate}>")
            param["bff"][collection] = str(candidate)

    if arg["mode"] == "full":
        param.setdefault("bff", {})["genomicVariationsVcf"] = param["gvvcfjson"]

    return param

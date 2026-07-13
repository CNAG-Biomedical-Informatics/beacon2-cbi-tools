from __future__ import annotations

import gzip
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .browser import BrowserError, generate_browser_report
from .redaction import redact_mapping


class ExecutionError(RuntimeError):
    pass


def write_json_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=3, sort_keys=True) + "\n", encoding="utf-8")


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def submit_cmd(command: Sequence[str], job: Path, log: Path, *, cwd: Path | None = None) -> None:
    try:
        with log.open("w", encoding="utf-8") as log_handle:
            subprocess.run(
                list(command),
                cwd=cwd,
                check=True,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ExecutionError(f"Failed to execute: {job}\nPlease check this file:\n{log}\n") from exc


def shell_value(value: Any) -> str:
    return shlex.quote(str(value))


def write_browser_readme(
    path: Path,
    *,
    report_name: str,
    variants: int,
    panels: int,
    warning: str | None = None,
) -> None:
    warning_note = f"\nWARNING\n-------\n{warning}\n" if warning else ""
    path.write_text(
        "BFF TOOLS BROWSER\n"
        "=================\n\n"
        f"Report: {report_name}\n"
        f"Panel-matched variants: {variants}\n"
        f"Gene panels with hits: {panels}\n\n"
        "HOW TO OPEN\n"
        "-----------\n"
        f"Open {report_name} directly in a modern web browser. No web server "
        "is required and the table library and data are embedded in the HTML.\n\n"
        "If local-file access is restricted by browser policy, run this command "
        "from this directory:\n\n"
        "    python3 -m http.server 8000\n\n"
        f"Then open http://localhost:8000/{report_name}\n\n"
        "NOTES\n"
        "-----\n"
        "- Search, filters, sorting, pagination, column settings, printing, and "
        "CSV export run locally in the browser.\n"
        "- Select a row or its arrow to inspect the complete variant summary.\n"
        "- External database links require internet access; the report itself "
        "does not.\n"
        "- Display loci are 1-based. The BFF start value shown in variant details "
        "is 0-based.\n"
        "- The report contains HIGH and MODERATE impact variants matching a "
        "configured gene panel; it is not an exhaustive copy of the input.\n"
        "- This research-use report is not a medical device and is not sufficient "
        "for clinical decisions.\n"
        f"{warning_note}",
        encoding="utf-8",
    )


def create_dbnsfp4_fields(selection: str, file_path: str) -> str:
    if selection == "cnag":
        fields = [
            "aaref", "aaalt", "rs_dbSNP151", "aapos", "genename", "Ensembl_geneid",
            "Ensembl_transcriptid", "Ensembl_proteinid", "Uniprot_acc", "Uniprot_entry",
            "HGVSc_snpEff", "HGVSp_snpEff", "SIFT_score", "SIFT_converted_rankscore",
            "SIFT_pred", "Polyphen2_HDIV_score", "Polyphen2_HDIV_pred", "Polyphen2_HVAR_score",
            "Polyphen2_HVAR_pred", "MutPred_score", "MVP_score", "DEOGEN2_score",
            "ClinPred_score", "ClinPred_pred", "phastCons100way_vertebrate",
            "phastCons30way_mammalian", "clinvar_id", "clinvar_clnsig", "clinvar_trait",
            "clinvar_review", "clinvar_hgvs", "clinvar_var_source", "clinvar_MedGen_id",
            "clinvar_OMIM_id", "clinvar_Orphanet_id", "Interpro_domain",
        ]
        return ",".join(sorted(fields))

    with gzip.open(file_path, "rt", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().lstrip("#").strip()
    cols = []
    for field in header.split():
        cols.append(f"'{field}'" if "(" in field or ")" in field else field)
    return ",".join(sorted(cols))


class PipelineRunner:
    def __init__(self, *, arg: dict[str, Any], config: dict[str, Any], param: dict[str, Any]):
        self.arg = arg
        self.config = config
        self.param = param
        self.projectdir = Path(param["projectdir"])
        self.notices: list[str] = []

    def make_log_payload(self) -> dict[str, Any]:
        return {
            "arg": redact_mapping(self.arg),
            "config": redact_mapping(self.config),
            "param": redact_mapping(self.param),
        }

    def prepare(self) -> None:
        self.projectdir.mkdir(parents=False, exist_ok=False)
        write_json_log(Path(self.param["log"]), self.make_log_payload())

    def run_tsv2vcf(self) -> None:
        target_dir = self.projectdir / "tsv"
        target_dir.mkdir()
        template = Path(self.config["bash4tsv"])
        content = template.read_text(encoding="utf-8")
        replacements = "\n".join([
            f"export TMPDIR={shell_value(self.config['tmpdir'])}",
            f"ZIP={shell_value(self.param['zip'])}",
            f"BCFTOOLS={shell_value(self.config['bcftools'])}",
            f"THREADS={shell_value(self.param['threads'])}",
            f"SAMPLE_ID={shell_value(self.param['sampleid'])}",
            f"GENOME={shell_value('hg19' if self.param['genome'] == 'hs37' else self.param['genome'])}",
            f"REF={shell_value(self.config[self.param['genome'] + 'fasta'])}",
            f"DATASETID={shell_value(self.param['datasetid'])}",
            f"PROJECTDIR={shell_value(self.param['projectdir'])}",
        ])
        content = content.replace("#____WRAPPER_VARIABLES____#", replacements)
        script_path = target_dir / template.name
        log_path = target_dir / template.name.replace(".sh", ".log")
        write_executable(script_path, content)
        submit_cmd(
            ["bash", script_path.name, str(Path(self.arg["inputfile"]).resolve())],
            script_path,
            log_path,
            cwd=target_dir,
        )
        self.arg["inputfile"] = str((target_dir / f"{self.param['sampleid']}.filtered.vcf.gz").resolve())

    def run_vcf2bff(self) -> None:
        target_dir = self.projectdir / "vcf"
        target_dir.mkdir()
        template = Path(self.config["bash4bff"])
        content = template.read_text(encoding="utf-8")
        genome = "hg19" if self.param["genome"] == "hs37" else self.param["genome"]
        replacements = [
            f"export TMPDIR={shell_value(self.config['tmpdir'])}",
            f"ZIP={shell_value(self.param['zip'])}",
            f"PYTHON={shell_value(self.config['pythonbin'])}",
            f"VCF2BFF={shell_value(self.config['vcf2bff'])}",
            f"THREADS={shell_value(self.param['threads'])}",
            f"GENOME={shell_value(genome)}",
            f"DATASETID={shell_value(self.param['datasetid'])}",
            f"PROJECTDIR={shell_value(self.param['projectdir'])}",
            f"PROGRESS_EVERY={shell_value(self.param.get('progress_every', 10_000))}",
            f"JSONL={shell_value('true' if self.param.get('jsonl') else 'false')}",
        ]
        fields = ""
        if self.param.get("annotate"):
            replacements.extend([
                f"JAVA={shell_value(self.config['javabin'])}",
                f"MEM={shell_value(self.config['mem'])}",
                f"SNPEFF={shell_value(self.config['snpeff'])}",
                f"SNPSIFT={shell_value(self.config['snpsift'])}",
                f"BCFTOOLS={shell_value(self.config['bcftools'])}",
                f"REF={shell_value(self.config[self.param['genome'] + 'fasta'])}",
                f"COSMIC={shell_value(self.config[self.param['genome'] + 'cosmic'])}",
                f"DBNSFP={shell_value(self.config[self.param['genome'] + 'dbnsfp'])}",
                f"CLINVAR={shell_value(self.config[self.param['genome'] + 'clinvar'])}",
            ])
            fields = create_dbnsfp4_fields(
                self.config["dbnsfpset"],
                self.config[self.param["genome"] + "dbnsfp"],
            )
        content = content.replace("#____WRAPPER_VARIABLES____#", "\n".join(replacements))
        content = content.replace("#____WRAPPER_FIELDS____#", fields)
        script_path = target_dir / template.name
        log_path = target_dir / template.name.replace(".sh", ".log")
        write_executable(script_path, content)
        annotate = "true" if self.param.get("annotate") else "false"
        inputfile = Path(self.arg["inputfile"]).resolve()
        submit_cmd(
            ["bash", script_path.name, str(inputfile), annotate],
            script_path,
            log_path,
            cwd=target_dir,
        )

    def run_bff2html(self) -> None:
        target_dir = self.projectdir / "browser"
        target_dir.mkdir()
        gvvcfjson = Path(self.param["gvvcfjson"]).resolve()
        output_path = target_dir / f"{self.param['jobid']}.html"
        log_path = target_dir / "run_bff2html.log"
        try:
            summary = generate_browser_report(
                gvvcfjson,
                Path(self.config["paneldir"]),
                output_path,
                project_id=self.projectdir.name,
                job_id=str(self.param["jobid"]),
            )
        except BrowserError as exc:
            log_path.write_text(str(exc) + "\n", encoding="utf-8")
            raise ExecutionError(
                f"Failed to generate BFF Tools Browser report\nPlease check this file:\n{log_path}\n"
            ) from exc
        warning = summary.get("warning")
        warning_line = f"Warning: {warning}\n" if warning else ""
        log_path.write_text(
            "Generated standalone BFF Tools Browser report\n"
            f"Output: {output_path}\n"
            f"Selected variants: {summary['variants']}\n"
            f"Panels with hits: {summary['panels']}\n"
            f"{warning_line}",
            encoding="utf-8",
        )
        if warning:
            self.notices.append(str(warning))
        write_browser_readme(
            target_dir / "README.txt",
            report_name=output_path.name,
            variants=summary["variants"],
            panels=summary["panels"],
            warning=str(warning) if warning else None,
        )

    def run_named(self, pipeline_name: str) -> None:
        if pipeline_name == "tsv2vcf":
            self.run_tsv2vcf()
            return
        if pipeline_name == "vcf2bff":
            self.run_vcf2bff()
            return
        if pipeline_name == "bff2html":
            self.run_bff2html()
            return
        raise ExecutionError(f"Unknown pipeline: {pipeline_name}")

    def run(self) -> None:
        self.prepare()
        for pipeline_name in ("tsv2vcf", "vcf2bff", "bff2html"):
            if self.param["pipeline"].get(pipeline_name):
                self.run_named(pipeline_name)

from __future__ import annotations

import gzip
import json
import re
import shlex
import shutil
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
        replacements = "\n".join([
            f"export TMPDIR={shell_value(self.config['tmpdir'])}",
            f"ZIP={shell_value(self.param['zip'])}",
            f"JAVA={shell_value(self.config['javabin'])}",
            f"MEM={shell_value(self.config['mem'])}",
            f"SNPEFF={shell_value(self.config['snpeff'])}",
            f"SNPSIFT={shell_value(self.config['snpsift'])}",
            f"BCFTOOLS={shell_value(self.config['bcftools'])}",
            f"THREADS={shell_value(self.param['threads'])}",
            f"VCF2BFF={shell_value(self.config['vcf2bff'])}",
            f"GENOME={shell_value(genome)}",
            f"REF={shell_value(self.config[self.param['genome'] + 'fasta'])}",
            f"COSMIC={shell_value(self.config[self.param['genome'] + 'cosmic'])}",
            f"DBNSFP={shell_value(self.config[self.param['genome'] + 'dbnsfp'])}",
            f"DATASETID={shell_value(self.param['datasetid'])}",
            f"PROJECTDIR={shell_value(self.param['projectdir'])}",
            f"CLINVAR={shell_value(self.config[self.param['genome'] + 'clinvar'])}",
        ])
        fields = create_dbnsfp4_fields(self.config["dbnsfpset"], self.config[self.param["genome"] + "dbnsfp"])
        content = content.replace("#____WRAPPER_VARIABLES____#", replacements)
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
                f"Failed to generate BFF browser report\nPlease check this file:\n{log_path}\n"
            ) from exc
        log_path.write_text(
            "Generated standalone BFF browser report\n"
            f"Output: {output_path}\n"
            f"Selected variants: {summary['variants']}\n"
            f"Panels with hits: {summary['panels']}\n",
            encoding="utf-8",
        )

    def run_bff2mongodb(self) -> None:
        target_dir = self.projectdir / "mongodb"
        target_dir.mkdir()
        log_path = target_dir / "run_bff2mongodb.log"
        mongoimport = str(self.config["mongoimport"])
        mongosh = str(self.config["mongosh"])
        mongodb_uri = str(self.config["mongodburi"])

        collections = {
            collection: Path(value).resolve()
            for collection, value in self.param.get("bff", {}).items()
            if collection not in {"metadatadir", "genomicVariationsVcf"}
        }
        gv_path = self.param.get("bff", {}).get("genomicVariationsVcf")
        if gv_path:
            collections["genomicVariations"] = Path(gv_path).resolve()
        if not collections:
            raise ExecutionError("No BFF collections were configured for MongoDB loading")

        try:
            with log_path.open("w", encoding="utf-8") as log_handle:
                for collection, source_path in sorted(collections.items()):
                    log_handle.write(f"Loading collection: {collection} from {source_path}\n")
                    log_handle.flush()
                    command = [
                        mongoimport,
                        "--jsonArray",
                        "--uri",
                        mongodb_uri,
                        "--collection",
                        collection,
                    ]
                    if source_path.suffix == ".gz":
                        self._run_streamed_import(command, source_path, log_handle)
                    else:
                        subprocess.run(
                            [*command, "--file", str(source_path)],
                            check=True,
                            stdout=log_handle,
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                    self._create_mongodb_indexes(
                        mongosh=mongosh,
                        mongodb_uri=mongodb_uri,
                        collection=collection,
                        log_handle=log_handle,
                    )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ExecutionError(
                f"MongoDB loading failed\nPlease check this file:\n{log_path}\n"
            ) from exc

    @staticmethod
    def _run_streamed_import(command: list[str], source_path: Path, log_handle: Any) -> None:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
        )
        assert process.stdin is not None
        try:
            with gzip.open(source_path, "rb") as source:
                shutil.copyfileobj(source, process.stdin, length=1024 * 1024)
        except BrokenPipeError:
            pass
        finally:
            process.stdin.close()
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)

    @staticmethod
    def _create_mongodb_indexes(
        *,
        mongosh: str,
        mongodb_uri: str,
        collection: str,
        log_handle: Any,
    ) -> None:
        collection_json = json.dumps(collection)
        index_suffix = re.sub(r"[^A-Za-z0-9_]", "_", collection)
        script = (
            "disableTelemetry();\n"
            f"const collection = db.getCollection({collection_json});\n"
            f'collection.createIndex({{"$**": 1}}, {{name: "single_field_{index_suffix}"}});\n'
            f'collection.createIndex({{"$**": "text"}}, {{name: "text_{index_suffix}"}});\n'
            "quit();\n"
        )
        subprocess.run(
            [mongosh, mongodb_uri],
            input=script,
            check=True,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
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
        if pipeline_name == "bff2mongodb":
            self.run_bff2mongodb()
            return
        raise ExecutionError(f"Unknown pipeline: {pipeline_name}")

    def run(self) -> None:
        self.prepare()
        for pipeline_name in ("tsv2vcf", "vcf2bff", "bff2html", "bff2mongodb"):
            if self.param["pipeline"].get(pipeline_name):
                self.run_named(pipeline_name)

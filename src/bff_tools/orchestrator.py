from __future__ import annotations

import gzip
import json
import subprocess
from pathlib import Path
from typing import Any


class ExecutionError(RuntimeError):
    pass


def write_json_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=3, sort_keys=True) + "\n", encoding="utf-8")


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def submit_cmd(cmd: str, job: Path, log: Path) -> None:
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise ExecutionError(f"Failed to execute: {job}\nPlease check this file:\n{log}\n") from exc


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
        return {"arg": self.arg, "config": self.config, "param": self.param}

    def prepare(self) -> None:
        self.projectdir.mkdir(parents=False, exist_ok=False)
        write_json_log(Path(self.param["log"]), self.make_log_payload())

    def run_tsv2vcf(self) -> None:
        target_dir = self.projectdir / "tsv"
        target_dir.mkdir()
        template = Path(self.config["bash4tsv"])
        content = template.read_text(encoding="utf-8")
        replacements = "\n".join([
            f"export TMPDIR={self.config['tmpdir']}",
            f"ZIP='{self.param['zip']}'",
            f"BCFTOOLS={self.config['bcftools']}",
            f"SAMPLE_ID={self.param['sampleid']}",
            f"GENOME='{('hg19' if self.param['genome'] == 'hs37' else self.param['genome'])}'",
            f"REF={self.config[self.param['genome'] + 'fasta']}",
            f"DATASETID={self.param['datasetid']}",
            f"PROJECTDIR={self.param['projectdir']}",
        ])
        content = content.replace("#____WRAPPER_VARIABLES____#", replacements)
        script_path = target_dir / template.name
        log_path = target_dir / template.name.replace(".sh", ".log")
        write_executable(script_path, content)
        cmd = f"cd {target_dir} && bash {script_path.name} {Path(self.arg['inputfile']).resolve()} > {log_path.name} 2>&1"
        submit_cmd(cmd, script_path, log_path)
        self.arg["inputfile"] = str((target_dir / f"{self.param['sampleid']}.filtered.vcf.gz").resolve())

    def run_vcf2bff(self) -> None:
        target_dir = self.projectdir / "vcf"
        target_dir.mkdir()
        template = Path(self.config["bash4bff"])
        content = template.read_text(encoding="utf-8")
        genome = "hg19" if self.param["genome"] == "hs37" else self.param["genome"]
        replacements = "\n".join([
            f"export TMPDIR={self.config['tmpdir']}",
            f"ZIP='{self.param['zip']}'",
            f"SNPEFF='{self.config['snpeff']}'",
            f"SNPSIFT='{self.config['snpsift']}'",
            f"BCFTOOLS={self.config['bcftools']}",
            f"VCF2BFF={self.config['vcf2bff']}",
            f"GENOME='{genome}'",
            f"REF={self.config[self.param['genome'] + 'fasta']}",
            f"COSMIC={self.config[self.param['genome'] + 'cosmic']}",
            f"DBNSFP={self.config[self.param['genome'] + 'dbnsfp']}",
            f"DATASETID={self.param['datasetid']}",
            f"PROJECTDIR={self.param['projectdir']}",
            f"CLINVAR={self.config[self.param['genome'] + 'clinvar']}",
        ])
        fields = create_dbnsfp4_fields(self.config["dbnsfpset"], self.config[self.param["genome"] + "dbnsfp"])
        content = content.replace("#____WRAPPER_VARIABLES____#", replacements)
        content = content.replace("#____WRAPPER_FIELDS____#", fields)
        script_path = target_dir / template.name
        log_path = target_dir / template.name.replace(".sh", ".log")
        write_executable(script_path, content)
        annotate = "true" if self.param.get("annotate") else "false"
        inputfile = Path(self.arg["inputfile"]).resolve()
        cmd = f"cd {target_dir} && bash {script_path.name} {inputfile} {annotate} > {log_path.name} 2>&1"
        submit_cmd(cmd, script_path, log_path)

    def run_bff2html(self) -> None:
        target_dir = self.projectdir / "browser"
        target_dir.mkdir()
        template = Path(self.config["bash4html"])
        content = template.read_text(encoding="utf-8")
        replacements = "\n".join([
            f"export TMPDIR={self.config['tmpdir']}",
            f"BFF2JSON={self.config['bff2json']}",
            f"JSON2HTML={self.config['json2html']}",
            f"ASSETSDIR={self.config['assetsdir']}",
            f"PANELDIR={self.config['paneldir']}",
        ])
        content = content.replace("#____WRAPPER_VARIABLES____#", replacements)
        script_path = target_dir / template.name
        log_path = target_dir / template.name.replace(".sh", ".log")
        write_executable(script_path, content)
        gvvcfjson = Path(self.param["gvvcfjson"]).resolve()
        cmd = f"cd {target_dir} && bash {script_path.name} {gvvcfjson} {self.projectdir} {self.param['jobid']} > {log_path.name} 2>&1"
        submit_cmd(cmd, script_path, log_path)

    def run_bff2mongodb(self) -> None:
        target_dir = self.projectdir / "mongodb"
        target_dir.mkdir()
        template = Path(self.config["bash4mongodb"])
        content = template.read_text(encoding="utf-8")
        replacements = [
            f"export TMPDIR={self.config['tmpdir']}",
            f"ZIP='{self.param['zip']}'",
            f"MONGOIMPORT={self.config['mongoimport']}",
            f"MONGODBURI={self.config['mongodburi']}",
            f"MONGOSH={self.config['mongosh']}",
        ]
        collections = []
        for collection, value in self.param.get("bff", {}).items():
            if collection in {"metadatadir", "genomicVariationsVcf"}:
                continue
            collections.append(f'["{collection}"]="{Path(value).resolve()}"')
        replacements.append("declare -A collections=(" + " ".join(collections) + ")")
        content = content.replace("#____WRAPPER_VARIABLES____#", "\n".join(replacements))

        gv_path = self.param.get("bff", {}).get("genomicVariationsVcf")
        gv_block = ""
        if gv_path:
            gv_resolved = Path(gv_path).resolve()
            gv_block = (
                "\n"
                'echo "Loading collection...genomicVariations[Vcf]"\n'
                f'$ZIP -dc {gv_resolved} | $MONGOIMPORT --jsonArray --uri "$MONGODBURI" --collection genomicVariations || echo "Could not load <{gv_resolved}> for <genomicVariations>"\n'
                'echo "Indexing collection...genomicVariations[Vcf]"\n'
                '$MONGOSH "$MONGODBURI"<<EOF\n'
                'disableTelemetry()\n'
                '/* Single field indexes */\n'
                'db.genomicVariations.createIndex( {"\\$**": 1}, {name: "single_field_genomicVariations"} )\n'
                '/* Text indexes */\n'
                'db.genomicVariations.createIndex( {"\\$**": "text"}, {name: "text_genomicVariations"} )\n'
                'quit()\n'
                'EOF'
            )
        content = content.replace("\n#__WRAPPER_GENOMIC_VARIATIONS_VARIABLES__#", gv_block)
        script_path = target_dir / template.name
        log_path = target_dir / template.name.replace(".sh", ".log")
        write_executable(script_path, content)
        cmd = f"cd {target_dir} && bash {script_path.name} > {log_path.name} 2>&1"
        submit_cmd(cmd, script_path, log_path)
        text = log_path.read_text(encoding="utf-8", errors="replace")
        if "document(s) failed to import" in text:
            raise ExecutionError(f"There was an error with <mongoimport>. Please check <{log_path}>")

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

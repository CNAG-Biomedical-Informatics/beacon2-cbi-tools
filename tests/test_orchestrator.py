from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools.orchestrator import (  # noqa: E402
    ExecutionError,
    PipelineRunner,
    create_dbnsfp4_fields,
    submit_cmd,
    write_executable,
    write_json_log,
)


class OrchestratorTests(unittest.TestCase):
    def test_create_dbnsfp4_fields_cnag(self) -> None:
        expected_fields = [
            "aaref",
            "aaalt",
            "rs_dbSNP151",
            "aapos",
            "genename",
            "Ensembl_geneid",
            "Ensembl_transcriptid",
            "Ensembl_proteinid",
            "Uniprot_acc",
            "Uniprot_entry",
            "HGVSc_snpEff",
            "HGVSp_snpEff",
            "SIFT_score",
            "SIFT_converted_rankscore",
            "SIFT_pred",
            "Polyphen2_HDIV_score",
            "Polyphen2_HDIV_pred",
            "Polyphen2_HVAR_score",
            "Polyphen2_HVAR_pred",
            "MutPred_score",
            "MVP_score",
            "DEOGEN2_score",
            "ClinPred_score",
            "ClinPred_pred",
            "phastCons100way_vertebrate",
            "phastCons30way_mammalian",
            "clinvar_id",
            "clinvar_clnsig",
            "clinvar_trait",
            "clinvar_review",
            "clinvar_hgvs",
            "clinvar_var_source",
            "clinvar_MedGen_id",
            "clinvar_OMIM_id",
            "clinvar_Orphanet_id",
            "Interpro_domain",
        ]
        expected = ",".join(sorted(expected_fields))
        self.assertEqual(create_dbnsfp4_fields("cnag", ""), expected)

    def test_write_executable_creates_file_and_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "test_script.sh"
            write_executable(target, "echo Hello World\n")
            self.assertTrue(target.exists())
            mode = target.stat().st_mode & 0o7777
            self.assertEqual(mode, 0o755)

    def test_write_json_log_writes_sorted_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "log.json"
            payload = {"b": 2, "a": 1}
            write_json_log(target, payload)
            self.assertTrue(target.exists())
            loaded = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(loaded, payload)

    def test_submit_cmd_raises_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            job = Path(tmpdir) / "job.sh"
            log = Path(tmpdir) / "job.log"
            with self.assertRaises(ExecutionError):
                submit_cmd("false", job, log)

    def test_prepare_writes_log_json_with_arg_config_and_param(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projectdir = Path(tmpdir) / "beacon_job"
            arg = {"mode": "vcf", "inputfile": "input.vcf.gz"}
            config = {"version": "2.0.11_1"}
            param = {"projectdir": str(projectdir), "log": str(projectdir / "log.json")}
            runner = PipelineRunner(arg=arg, config=config, param=param)
            runner.prepare()
            payload = json.loads((projectdir / "log.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["arg"], arg)
            self.assertEqual(payload["config"], config)
            self.assertEqual(payload["param"], param)

    def test_run_tsv2vcf_generates_script_and_updates_inputfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            template = tmp / "run_tsv2vcf.sh"
            template.write_text("#____WRAPPER_VARIABLES____#\n", encoding="utf-8")
            inputfile = tmp / "input.txt.gz"
            inputfile.write_text("dummy", encoding="utf-8")
            runner = PipelineRunner(
                arg={"inputfile": str(inputfile)},
                config={
                    "bash4tsv": str(template),
                    "tmpdir": "/tmp",
                    "bcftools": "/usr/bin/bcftools",
                    "hs37fasta": "/ref/hs37.fa.gz",
                },
                param={
                    "projectdir": str(tmp / "job"),
                    "zip": "/bin/gzip",
                    "sampleid": "sample_1",
                    "genome": "hs37",
                    "datasetid": "ds1",
                },
            )
            runner.projectdir.mkdir()
            with mock.patch("bff_tools.orchestrator.submit_cmd") as submit_mock:
                runner.run_tsv2vcf()
            script_path = runner.projectdir / "tsv" / "run_tsv2vcf.sh"
            content = script_path.read_text(encoding="utf-8")
            self.assertIn("SAMPLE_ID=sample_1", content)
            self.assertIn("GENOME='hg19'", content)
            submit_mock.assert_called_once()
            self.assertTrue(runner.arg["inputfile"].endswith("sample_1.filtered.vcf.gz"))

    def test_run_vcf2bff_generates_script_with_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            template = tmp / "run_vcf2bff.sh"
            template.write_text("#____WRAPPER_VARIABLES____#\n#____WRAPPER_FIELDS____#\n", encoding="utf-8")
            inputfile = tmp / "input.vcf.gz"
            inputfile.write_text("dummy", encoding="utf-8")
            runner = PipelineRunner(
                arg={"inputfile": str(inputfile)},
                config={
                    "bash4bff": str(template),
                    "tmpdir": "/tmp",
                    "bcftools": "/usr/bin/bcftools",
                    "snpeff": "snpeff",
                    "snpsift": "snpsift",
                    "vcf2bff": "vcf2bff.pl",
                    "dbnsfpset": "cnag",
                    "hs37fasta": "/ref/hs37.fa.gz",
                    "hs37cosmic": "/ref/cosmic.vcf.gz",
                    "hs37dbnsfp": "/ref/dbnsfp.gz",
                    "hs37clinvar": "/ref/clinvar.vcf.gz",
                },
                param={
                    "projectdir": str(tmp / "job"),
                    "zip": "/bin/gzip",
                    "genome": "hs37",
                    "datasetid": "ds1",
                    "annotate": True,
                },
            )
            runner.projectdir.mkdir()
            with mock.patch("bff_tools.orchestrator.submit_cmd") as submit_mock:
                with mock.patch("bff_tools.orchestrator.create_dbnsfp4_fields", return_value="FIELD1,FIELD2"):
                    runner.run_vcf2bff()
            script_path = runner.projectdir / "vcf" / "run_vcf2bff.sh"
            content = script_path.read_text(encoding="utf-8")
            self.assertIn("VCF2BFF=vcf2bff.pl", content)
            self.assertIn("FIELD1,FIELD2", content)
            submit_mock.assert_called_once()

    def test_run_executes_pipelines_in_order(self) -> None:
        runner = PipelineRunner(
            arg={},
            config={},
            param={
                "projectdir": "/tmp/ignored",
                "pipeline": {
                    "tsv2vcf": 1,
                    "vcf2bff": 1,
                    "bff2html": 0,
                    "bff2mongodb": 1,
                },
            },
        )
        calls: list[str] = []
        with mock.patch.object(runner, "prepare", side_effect=lambda: calls.append("prepare")):
            with mock.patch.object(runner, "run_named", side_effect=lambda name: calls.append(name)):
                runner.run()
        self.assertEqual(calls, ["prepare", "tsv2vcf", "vcf2bff", "bff2mongodb"])


if __name__ == "__main__":
    unittest.main()

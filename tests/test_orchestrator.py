from __future__ import annotations

import gzip
import json
import subprocess
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
from bff_tools.browser import BrowserError  # noqa: E402


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

    def test_create_dbnsfp4_fields_reads_and_quotes_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            header = Path(tmpdir) / "dbnsfp.gz"
            with gzip.open(header, "wt", encoding="utf-8") as handle:
                handle.write("#plain field(one) field_two\n")
            fields = create_dbnsfp4_fields("all", str(header))
        self.assertEqual(fields, "'field(one)',field_two,plain")

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
                submit_cmd(["false"], job, log)

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

    def test_prepare_redacts_credentials_from_log_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projectdir = Path(tmpdir) / "beacon_job"
            runner = PipelineRunner(
                arg={"mode": "vcf"},
                config={"service_uri": "https://root:secret@example.org/api"},
                param={"projectdir": str(projectdir), "log": str(projectdir / "log.json")},
            )
            runner.prepare()
            text = (projectdir / "log.json").read_text(encoding="utf-8")
            self.assertNotIn("root", text)
            self.assertNotIn("secret", text)
            self.assertIn("<redacted>", text)

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
                    "threads": 3,
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
            self.assertIn("THREADS=3", content)
            self.assertIn("GENOME=hg19", content)
            submit_mock.assert_called_once()
            self.assertNotIn("shell", submit_mock.call_args.kwargs)
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
                    "javabin": "/usr/bin/java",
                    "mem": "8G",
                    "snpeff": "/opt/snpEff.jar",
                    "snpsift": "/opt/SnpSift.jar",
                    "pythonbin": "/usr/bin/python3",
                    "vcf2bff": "/opt/bff_tools/vcf2bff.py",
                    "dbnsfpset": "cnag",
                    "hs37fasta": "/ref/hs37.fa.gz",
                    "hs37cosmic": "/ref/cosmic.vcf.gz",
                    "hs37dbnsfp": "/ref/dbnsfp.gz",
                    "hs37clinvar": "/ref/clinvar.vcf.gz",
                },
                param={
                    "projectdir": str(tmp / "job"),
                    "zip": "/bin/gzip",
                    "threads": 5,
                    "genome": "hs37",
                    "datasetid": "ds1",
                    "annotate": True,
                    "jsonl": True,
                },
            )
            runner.projectdir.mkdir()
            with mock.patch("bff_tools.orchestrator.submit_cmd") as submit_mock:
                with mock.patch("bff_tools.orchestrator.create_dbnsfp4_fields", return_value="FIELD1,FIELD2"):
                    runner.run_vcf2bff()
            script_path = runner.projectdir / "vcf" / "run_vcf2bff.sh"
            content = script_path.read_text(encoding="utf-8")
            self.assertIn("PYTHON=/usr/bin/python3", content)
            self.assertIn("VCF2BFF=/opt/bff_tools/vcf2bff.py", content)
            self.assertIn("PROGRESS_EVERY=10000", content)
            self.assertIn("JSONL=true", content)
            self.assertIn("THREADS=5", content)
            self.assertIn("JAVA=/usr/bin/java", content)
            self.assertIn("SNPEFF=/opt/snpEff.jar", content)
            self.assertIn("FIELD1,FIELD2", content)
            submit_mock.assert_called_once()
            self.assertNotIn("shell", submit_mock.call_args.kwargs)

    def test_run_vcf2bff_without_annotation_needs_no_reference_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            template = tmp / "run_vcf2bff.sh"
            template.write_text(
                "#____WRAPPER_VARIABLES____#\n#____WRAPPER_FIELDS____#\n",
                encoding="utf-8",
            )
            inputfile = tmp / "input.vcf.gz"
            inputfile.write_text("dummy", encoding="utf-8")
            runner = PipelineRunner(
                arg={"inputfile": str(inputfile)},
                config={
                    "bash4bff": str(template),
                    "tmpdir": "/tmp",
                    "pythonbin": "/usr/bin/python3",
                    "vcf2bff": "/opt/bff_tools/vcf2bff.py",
                },
                param={
                    "projectdir": str(tmp / "job"),
                    "zip": "/bin/gzip",
                    "threads": 2,
                    "genome": "hg19",
                    "datasetid": "ds1",
                    "annotate": False,
                },
            )
            runner.projectdir.mkdir()
            with mock.patch("bff_tools.orchestrator.submit_cmd") as submit_mock:
                with mock.patch("bff_tools.orchestrator.create_dbnsfp4_fields") as fields_mock:
                    runner.run_vcf2bff()
            fields_mock.assert_not_called()
            submit_mock.assert_called_once()
            content = (runner.projectdir / "vcf" / "run_vcf2bff.sh").read_text(encoding="utf-8")
            self.assertNotIn("SNPEFF=", content)

    def test_run_bff2html_generates_standalone_report_and_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            projectdir = tmp / "job"
            projectdir.mkdir()
            gv_path = projectdir / "vcf" / "genomicVariationsVcf.json.gz"
            gv_path.parent.mkdir()
            gv_path.write_text("dummy", encoding="utf-8")
            panel_dir = tmp / "panels"
            panel_dir.mkdir()
            runner = PipelineRunner(
                arg={},
                config={"paneldir": str(panel_dir)},
                param={
                    "projectdir": str(projectdir),
                    "gvvcfjson": str(gv_path),
                    "jobid": "12345",
                },
            )
            warning = "Large standalone report"
            summary = {
                "variants": 3,
                "panels": 2,
                "pathogenic": 1,
                "homAlt": 1,
                "warning": warning,
            }
            with mock.patch(
                "bff_tools.orchestrator.generate_browser_report",
                return_value=summary,
            ) as generate_mock:
                runner.run_bff2html()

            output_path = projectdir / "browser" / "12345.html"
            generate_mock.assert_called_once_with(
                gv_path.resolve(),
                panel_dir,
                output_path,
                project_id="job",
                job_id="12345",
            )
            log = (projectdir / "browser" / "run_bff2html.log").read_text(encoding="utf-8")
            self.assertIn("Selected variants: 3", log)
            self.assertIn(f"Warning: {warning}", log)
            self.assertEqual(runner.notices, [warning])
            readme = (projectdir / "browser" / "README.txt").read_text(encoding="utf-8")
            self.assertIn("Report: 12345.html", readme)
            self.assertIn("No web server is required", readme)
            self.assertIn("External database links require internet access", readme)
            self.assertIn("not a medical device", readme)
            self.assertIn(warning, readme)

    def test_run_bff2html_wraps_browser_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projectdir = Path(tmpdir) / "job"
            projectdir.mkdir()
            runner = PipelineRunner(
                arg={},
                config={"paneldir": str(Path(tmpdir) / "panels")},
                param={
                    "projectdir": str(projectdir),
                    "gvvcfjson": str(projectdir / "variants.json.gz"),
                    "jobid": "42",
                },
            )
            with mock.patch(
                "bff_tools.orchestrator.generate_browser_report",
                side_effect=BrowserError("bad BFF"),
            ), self.assertRaisesRegex(ExecutionError, "Failed to generate"):
                runner.run_bff2html()
            self.assertEqual(
                (projectdir / "browser" / "run_bff2html.log").read_text(
                    encoding="utf-8"
                ),
                "bad BFF\n",
            )

    def test_run_named_dispatches_and_rejects_unknown_pipeline(self) -> None:
        runner = PipelineRunner(
            arg={}, config={}, param={"projectdir": "/tmp/unused"}
        )
        for name, method_name in (
            ("tsv2vcf", "run_tsv2vcf"),
            ("vcf2bff", "run_vcf2bff"),
            ("bff2html", "run_bff2html"),
        ):
            with self.subTest(name=name), mock.patch.object(
                runner, method_name
            ) as method:
                runner.run_named(name)
                method.assert_called_once()
        with self.assertRaisesRegex(ExecutionError, "Unknown pipeline"):
            runner.run_named("unknown")

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
                },
            },
        )
        calls: list[str] = []
        with mock.patch.object(runner, "prepare", side_effect=lambda: calls.append("prepare")):
            with mock.patch.object(runner, "run_named", side_effect=lambda name: calls.append(name)):
                runner.run()
        self.assertEqual(calls, ["prepare", "tsv2vcf", "vcf2bff"])


if __name__ == "__main__":
    unittest.main()

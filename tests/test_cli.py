from __future__ import annotations

import contextlib
import io
import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools import cli  # noqa: E402
from bff_tools.integration import ANNOTATED_VCF, EXPECTED_BFF  # noqa: E402
from bff_tools.parity import compare_bff_files  # noqa: E402


class CliTests(unittest.TestCase):
    def test_vcf_help_names_external_data_environment(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit) as ctx:
            cli.build_parser().parse_args(["vcf", "--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("BFF_TOOLS_DATA", stdout.getvalue())

    def test_version_option_exits_cleanly(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cli.main(["-V"])
        self.assertEqual(ctx.exception.code, 0)

    def test_missing_config_file_raises_config_error(self) -> None:
        with self.assertRaises(cli.ConfigError):
            cli._validate_args(
                {
                    "mode": "vcf",
                    "inputfile": "foo.vcf",
                    "configfile": "missing.yaml",
                    "paramfile": None,
                    "threads": None,
                }
            )

    def test_argument_validation_rejects_missing_inputs_and_bad_values(self) -> None:
        cases = [
            ({"mode": "vcf", "inputfile": None}, "require an input file"),
            (
                {"mode": "vcf", "inputfile": "input.vcf", "paramfile": "missing.yaml"},
                "requires a param file",
            ),
            (
                {"mode": "vcf", "inputfile": "input.vcf", "threads": 0},
                "positive integer",
            ),
            (
                {"mode": "vcf", "inputfile": "input.vcf", "progress_every": 0},
                "progress-every",
            ),
            (
                {"mode": "vcf", "inputfile": "input.txt"},
                "valid input extension",
            ),
        ]
        for arguments, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(
                cli.ConfigError, message
            ):
                cli._validate_args(arguments)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / "config.yaml"
            param = Path(tmpdir) / "param.yaml"
            config.write_text("{}\n", encoding="utf-8")
            param.write_text("{}\n", encoding="utf-8")
            cli._validate_args(
                {
                    "mode": "tsv",
                    "inputfile": "input.tsv.gz",
                    "configfile": str(config),
                    "paramfile": str(param),
                    "threads": 1,
                }
            )

    def test_main_reports_config_error_without_traceback(self) -> None:
        stderr = io.StringIO()
        with mock.patch("bff_tools.cli.read_config_file", side_effect=cli.ConfigError("bad config")):
            with contextlib.redirect_stderr(stderr):
                result = cli.main(["tsv", "-i", "input.tsv"])
        self.assertEqual(result, 1)
        self.assertEqual(stderr.getvalue().strip(), "Error: bad config")

    def test_validate_template_and_validation_result_paths(self) -> None:
        stdout = io.StringIO()
        with mock.patch(
            "bff_tools.cli.export_template", return_value=Path("template.xlsx")
        ), contextlib.redirect_stdout(stdout):
            result = cli.handle_validate({"template_out": "template.xlsx"})
        self.assertEqual(result, 0)
        self.assertIn("Wrote template.xlsx", stdout.getvalue())

        report = SimpleNamespace(ok=False)
        arguments = {
            "input_files": ["individuals.json"],
            "schema_dir": "schemas",
            "out_dir": "output",
            "gv": True,
            "gv_vcf": False,
            "ignore_validation": False,
            "verbose": True,
            "debug": 0,
            "no_color": True,
            "no_emoji": True,
        }
        with mock.patch(
            "bff_tools.cli.validate_inputs", return_value=report
        ) as validate_mock, mock.patch("bff_tools.cli.print_report") as print_mock:
            self.assertEqual(cli.handle_validate(arguments), 1)
        self.assertEqual(validate_mock.call_args.kwargs["schema_dir"], Path("schemas"))
        print_mock.assert_called_once_with(
            report,
            ignore_validation=False,
            no_color=True,
            no_emoji=True,
        )

        arguments["ignore_validation"] = True
        with mock.patch(
            "bff_tools.cli.validate_inputs", return_value=report
        ), mock.patch("bff_tools.cli.print_report"):
            self.assertEqual(cli.handle_validate(arguments), 0)

    def test_main_reports_validator_error(self) -> None:
        stderr = io.StringIO()
        with mock.patch(
            "bff_tools.cli.handle_validate",
            side_effect=cli.ValidatorError("invalid workbook"),
        ), contextlib.redirect_stderr(stderr):
            result = cli.main(["validate", "--template-out", "template.xlsx"])
        self.assertEqual(result, 1)
        self.assertIn("invalid workbook", stderr.getvalue())

    def test_spinner_and_pipeline_execution_modes(self) -> None:
        class OneIterationEvent:
            def __init__(self) -> None:
                self.finished = False

            def is_set(self) -> bool:
                return self.finished

            def wait(self, _seconds: float) -> None:
                self.finished = True

        stdout = io.StringIO()
        with mock.patch(
            "bff_tools.cli.time.time", side_effect=[10.0, 11.0]
        ), contextlib.redirect_stdout(stdout):
            cli._spinner_worker(stop_event=OneIterationEvent(), no_emoji=False)
        self.assertIn("Working", stdout.getvalue())
        self.assertIn("elapsed: 1s", stdout.getvalue())

        runner = mock.Mock()
        with mock.patch("bff_tools.cli.sys.stdout.isatty", return_value=False):
            cli._run_pipeline(
                runner, "vcf2bff", debug=0, verbose=False, no_emoji=True
            )
        runner.run_named.assert_called_once_with("vcf2bff")

        runner.reset_mock()
        thread = mock.Mock()
        with mock.patch(
            "bff_tools.cli.sys.stdout.isatty", return_value=True
        ), mock.patch("bff_tools.cli.threading.Thread", return_value=thread) as factory:
            cli._run_pipeline(
                runner, "bff2html", debug=0, verbose=False, no_emoji=True
            )
        factory.assert_called_once()
        thread.start.assert_called_once()
        thread.join.assert_called_once()
        runner.run_named.assert_called_once_with("bff2html")

    def test_main_runs_selected_pipelines_and_prints_finish_banner(self) -> None:
        param = {
            "annotate": False,
            "bff2html": True,
            "genome": "hg19",
            "projectdir": "output",
            "pipeline": {"tsv2vcf": 0, "vcf2bff": 1, "bff2html": 1},
        }
        runner = mock.Mock()
        runner.notices = []
        with mock.patch(
            "bff_tools.cli.read_param_file", return_value=param
        ), mock.patch("bff_tools.cli.read_config_file", return_value={}) as config_mock, mock.patch(
            "bff_tools.cli.PipelineRunner", return_value=runner
        ), mock.patch("bff_tools.cli.print_run_summary"), mock.patch(
            "bff_tools.cli.print_start_banner"
        ), mock.patch("bff_tools.cli.print_pipeline_status") as status_mock, mock.patch(
            "bff_tools.cli._run_pipeline"
        ) as run_mock, mock.patch("bff_tools.cli.print_finish_banner") as finish_mock, mock.patch(
            "bff_tools.cli.random.choice", return_value="Bye"
        ):
            result = cli.main(
                [
                    "vcf",
                    "-i",
                    "input.vcf",
                    "--no-annotate",
                    "--browser",
                    "--verbose",
                ]
            )

        self.assertEqual(result, 0)
        self.assertTrue(config_mock.call_args.kwargs["browser"])
        runner.prepare.assert_called_once()
        self.assertEqual(
            [call.args[1] for call in run_mock.call_args_list],
            ["vcf2bff", "bff2html"],
        )
        self.assertEqual(status_mock.call_count, 2)
        finish_mock.assert_called_once()

    def test_main_reports_pipeline_execution_error(self) -> None:
        param = {
            "annotate": False,
            "bff2html": False,
            "genome": "hg19",
            "projectdir": "output",
            "pipeline": {},
        }
        runner = mock.Mock()
        runner.prepare.side_effect = cli.ExecutionError("pipeline failed")
        stderr = io.StringIO()
        with mock.patch(
            "bff_tools.cli.read_param_file", return_value=param
        ), mock.patch("bff_tools.cli.read_config_file", return_value={}), mock.patch(
            "bff_tools.cli.PipelineRunner", return_value=runner
        ), mock.patch("bff_tools.cli.print_run_summary"), mock.patch(
            "bff_tools.cli.print_start_banner"
        ), contextlib.redirect_stderr(stderr):
            result = cli.main(["vcf", "-i", "input.vcf"])
        self.assertEqual(result, 1)
        self.assertIn("pipeline failed", stderr.getvalue())

    def test_package_entry_points_delegate_to_cli(self) -> None:
        import bff_tools

        with mock.patch("bff_tools.cli.main", return_value=7) as main_mock:
            self.assertEqual(bff_tools.main(["--version"]), 7)
        main_mock.assert_called_once_with(["--version"])

        with mock.patch.object(
            sys, "argv", ["bff-tools", "--version"]
        ), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as context:
                runpy.run_module("bff_tools.__main__", run_name="__main__")
        self.assertEqual(context.exception.code, 0)

    def test_retired_modes_are_not_available(self) -> None:
        parser = cli.build_parser()
        for mode in ("load", "full"):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    parser.parse_args([mode])
            self.assertEqual(ctx.exception.code, 2)

    def test_goodbye_list_is_not_empty(self) -> None:
        self.assertTrue(cli.GOODBYES)

    def test_bin_bff_tools_help_runs(self) -> None:
        result = subprocess.run(
            [str(ROOT / "bin" / "bff-tools"), "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("usage: bff-tools", result.stdout)
        self.assertIn("validate", result.stdout)

    def test_bin_bff_tools_beaconizes_annotated_vcf_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "beaconized"
            result = subprocess.run(
                [
                    str(ROOT / "bin" / "bff-tools"),
                    "vcf",
                    "--input",
                    str(ANNOTATED_VCF),
                    "--no-annotate",
                    "--browser",
                    "--genome",
                    "hg19",
                    "--dataset-id",
                    "default_beacon_1",
                    "--project-dir",
                    str(project_dir),
                    "--no-color",
                    "--no-emoji",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )

            actual_path = project_dir / "vcf" / "genomicVariationsVcf.json.gz"
            browser_path = project_dir / "browser"
            self.assertTrue(actual_path.is_file())
            self.assertTrue((project_dir / "log.json").is_file())
            self.assertEqual(len(list(browser_path.glob("*.html"))), 1)

            comparison = compare_bff_files(EXPECTED_BFF, actual_path)
            self.assertTrue(
                comparison.equal,
                msg=(
                    f"difference at record {comparison.first_difference} "
                    f"path {comparison.path}: "
                    f"{comparison.expected!r} != {comparison.actual!r}"
                ),
            )


if __name__ == "__main__":
    unittest.main()

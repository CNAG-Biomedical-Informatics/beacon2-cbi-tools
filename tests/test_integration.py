from __future__ import annotations

import contextlib
import io
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

from bff_tools import cli, integration  # noqa: E402
from bff_tools.config import DATA_ROOT_ENV  # noqa: E402
from bff_tools.parity import ParityError, ParityResult  # noqa: E402


class IntegrationTests(unittest.TestCase):
    def test_packaged_assets_are_complete(self) -> None:
        integration._check_assets()
        self.assertTrue(all(path.stat().st_size > 0 for path in integration.REQUIRED_ASSETS))

        with mock.patch.object(
            integration,
            "REQUIRED_ASSETS",
            (Path("/missing/integration-fixture"),),
        ):
            with self.assertRaisesRegex(
                integration.IntegrationTestError, "fixture is incomplete"
            ):
                integration._check_assets()

    def test_run_uses_installed_cli_and_retains_requested_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "data"
            data_dir.mkdir()
            output_dir = root / "result"
            commands: list[tuple[list[str], dict[str, str]]] = []

            def run(command, *, env, check):
                self.assertFalse(check)
                commands.append((command, env))
                if "vcf" in command:
                    actual = output_dir / "vcf" / "genomicVariationsVcf.json.gz"
                    actual.parent.mkdir(parents=True)
                    actual.write_bytes(integration.EXPECTED_BFF.read_bytes())
                return subprocess.CompletedProcess(command, 0)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = integration.run_annotation_integration(
                    data_dir=str(data_dir),
                    output_dir=str(output_dir),
                    threads=3,
                    verbose=True,
                    run=run,
                )

        self.assertEqual(result, output_dir)
        self.assertEqual(len(commands), 2)
        conversion, conversion_env = commands[0]
        validation, validation_env = commands[1]
        self.assertEqual(conversion[:3], [sys.executable, "-m", "bff_tools"])
        self.assertIn(str(integration.INPUT_VCF), conversion)
        self.assertIn("--verbose", conversion)
        self.assertEqual(conversion[conversion.index("--threads") + 1], "3")
        self.assertIn("validate", validation)
        self.assertEqual(conversion_env[DATA_ROOT_ENV], str(data_dir.resolve()))
        self.assertEqual(validation_env[DATA_ROOT_ENV], str(data_dir.resolve()))
        self.assertIn("Semantic parity passed for 1044 record(s)", stdout.getvalue())
        self.assertIn(f"Integration output retained in {output_dir}", stdout.getvalue())

    def test_temporary_output_is_removed_after_success(self) -> None:
        generated_project: Path | None = None

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)

            def run(command, *, env, check):
                nonlocal generated_project
                if "vcf" in command:
                    generated_project = Path(command[command.index("--project-dir") + 1])
                    actual = generated_project / "vcf" / "genomicVariationsVcf.json.gz"
                    actual.parent.mkdir(parents=True)
                    actual.write_bytes(integration.EXPECTED_BFF.read_bytes())
                return subprocess.CompletedProcess(command, 0)

            with contextlib.redirect_stdout(io.StringIO()):
                result = integration.run_annotation_integration(
                    data_dir=str(data_dir),
                    run=run,
                )

        self.assertIsNone(result)
        self.assertIsNotNone(generated_project)
        self.assertFalse(generated_project.exists())

    def test_preflight_and_command_failures_are_actionable(self) -> None:
        with self.assertRaisesRegex(integration.IntegrationTestError, "positive"):
            integration.run_annotation_integration(data_dir="/tmp", threads=0)

        with self.assertRaisesRegex(integration.IntegrationTestError, "does not exist"):
            integration.run_annotation_integration(
                data_dir="/definitely/missing/bff-tools-data"
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir) / "existing"
            existing.mkdir()
            with self.assertRaisesRegex(
                integration.IntegrationTestError, "output already exists"
            ):
                integration.run_annotation_integration(
                    data_dir=tmpdir,
                    output_dir=str(existing),
                )

            failed = lambda command, **_kwargs: subprocess.CompletedProcess(command, 2)
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(
                    integration.IntegrationTestError, "exit code 2"
                ):
                    integration.run_annotation_integration(
                        data_dir=tmpdir,
                        run=failed,
                    )

    def test_parity_failures_report_record_and_json_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"

            def run(command, **_kwargs):
                if "vcf" in command:
                    actual = project / "vcf" / "genomicVariationsVcf.json.gz"
                    actual.parent.mkdir(parents=True)
                    actual.write_bytes(b"[]\n")
                return subprocess.CompletedProcess(command, 0)

            difference = ParityResult(
                records=0,
                first_difference=1,
                path="/variation/alternateBases",
                expected="A",
                actual="T",
            )
            with mock.patch.object(
                integration, "compare_bff_files", return_value=difference
            ), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(
                    integration.IntegrationTestError,
                    "record 1, JSON path /variation/alternateBases",
                ):
                    integration.run_annotation_integration(
                        data_dir=tmpdir,
                        output_dir=str(project),
                        run=run,
                    )

        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"

            def run_with_output(command, **_kwargs):
                if "vcf" in command:
                    actual = project / "vcf" / "genomicVariationsVcf.json.gz"
                    actual.parent.mkdir(parents=True)
                    actual.write_bytes(b"[]\n")
                return subprocess.CompletedProcess(command, 0)

            with mock.patch.object(
                integration,
                "compare_bff_files",
                side_effect=ParityError("invalid JSON"),
            ), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(
                    integration.IntegrationTestError, "Cannot compare.*invalid JSON"
                ):
                    integration.run_annotation_integration(
                        data_dir=tmpdir,
                        output_dir=str(project),
                        run=run_with_output,
                    )

    def test_cli_dispatches_test_and_reports_errors(self) -> None:
        with mock.patch("bff_tools.cli.run_annotation_integration") as run_mock:
            self.assertEqual(
                cli.main(
                    [
                        "test",
                        "--data-dir",
                        "/data",
                        "--output-dir",
                        "/output",
                        "--threads",
                        "4",
                        "--verbose",
                    ]
                ),
                0,
            )
        run_mock.assert_called_once_with(
            data_dir="/data",
            output_dir="/output",
            threads=4,
            verbose=True,
        )

        stderr = io.StringIO()
        with mock.patch(
            "bff_tools.cli.run_annotation_integration",
            side_effect=integration.IntegrationTestError("test failed"),
        ), contextlib.redirect_stderr(stderr):
            self.assertEqual(cli.main(["test", "--data-dir", "/data"]), 1)
        self.assertIn("Error: test failed", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

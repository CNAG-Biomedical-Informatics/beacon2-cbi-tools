from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools import cli, doctor
from bff_tools.config import CONFIG_PATH_ENV, DATA_ROOT_ENV, ConfigError
from bff_tools.resource_installer import BUNDLE_REVISION, EXPECTED_DIRECTORIES, INSTALL_MARKER
from bff_tools.validator import ValidatorError


class DoctorTests(unittest.TestCase):
    @staticmethod
    def _root_config(root: Path) -> dict[str, object]:
        return {
            "base": str(root),
            "hg19fasta": "{base}/databases/genomes/hg19.fa.gz",
        }

    @staticmethod
    def _standard_bundle(root: Path, *, revision: str = BUNDLE_REVISION) -> None:
        for name in EXPECTED_DIRECTORIES:
            (root / name).mkdir(parents=True, exist_ok=True)
        (root / INSTALL_MARKER).write_text(f"{revision}\n", encoding="utf-8")

    def test_unconfigured_bundle_is_a_warning_and_core_remains_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing"
            output = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                doctor, "load_yaml_file", return_value=self._root_config(missing)
            ), contextlib.redirect_stdout(output):
                result = doctor.run_doctor(no_color=True)

        self.assertEqual(result, 0)
        rendered = output.getvalue()
        self.assertIn("[WARN] Raw VCF annotation", rendered)
        self.assertIn("CORE READY (annotation not configured)", rendered)
        self.assertIn("bff-tools install-resources", rendered)
        self.assertNotIn("\033[", rendered)

    def test_valid_standard_bundle_and_profile_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            self._standard_bundle(root)
            output = io.StringIO()
            with mock.patch.dict(
                os.environ, {DATA_ROOT_ENV: str(root)}, clear=True
            ), mock.patch.object(
                doctor, "load_yaml_file", return_value=self._root_config(root)
            ), mock.patch.object(
                doctor, "read_config_file", return_value={"base": str(root)}
            ) as config, contextlib.redirect_stdout(output):
                result = doctor.run_doctor(genome="hg38", no_color=True)

        self.assertEqual(result, 0)
        self.assertIn("[PASS] Raw VCF annotation", output.getvalue())
        self.assertIn("[PASS] Status", output.getvalue())
        self.assertIn("READY", output.getvalue())
        self.assertEqual(config.call_args.kwargs["genome"], "hg38")

    def test_explicit_missing_data_root_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "missing"
            output = io.StringIO()
            with mock.patch.dict(
                os.environ, {DATA_ROOT_ENV: str(root)}, clear=True
            ), mock.patch.object(
                doctor, "load_yaml_file", return_value=self._root_config(root)
            ), contextlib.redirect_stdout(output):
                result = doctor.run_doctor(no_color=True)

        self.assertEqual(result, 1)
        self.assertIn("configured data root does not exist", output.getvalue())
        self.assertIn("NOT READY", output.getvalue())

    def test_incomplete_or_wrong_standard_bundle_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            self._standard_bundle(root, revision="r2")
            output = io.StringIO()
            with mock.patch.dict(
                os.environ, {DATA_ROOT_ENV: str(root)}, clear=True
            ), mock.patch.object(
                doctor, "load_yaml_file", return_value=self._root_config(root)
            ), mock.patch.object(
                doctor, "read_config_file", return_value={}
            ), contextlib.redirect_stdout(output):
                result = doctor.run_doctor(no_color=True)

        self.assertEqual(result, 1)
        self.assertIn("expected r3, found r2", output.getvalue())
        self.assertIn("standard bundle r3 is not verified", output.getvalue())

    def test_custom_absolute_layout_does_not_require_bundle_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "site.yaml"
            config_path.write_text("javabin: /usr/bin/java\n", encoding="utf-8")
            output = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                doctor, "read_config_file", return_value={"javabin": "/usr/bin/java"}
            ), contextlib.redirect_stdout(output):
                result = doctor.run_doctor(
                    config_file=str(config_path),
                    genome="hs37",
                    no_color=True,
                )

        self.assertEqual(result, 0)
        self.assertIn("not required for a custom resource layout", output.getvalue())
        self.assertIn("hs37 profile ready", output.getvalue())

    def test_invalid_custom_configuration_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "site.yaml"
            config_path.write_text("base: /site/data\n", encoding="utf-8")
            output = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                doctor,
                "read_config_file",
                side_effect=ConfigError("Configured hg19clinvar file does not exist"),
            ), contextlib.redirect_stdout(output):
                result = doctor.run_doctor(
                    config_file=str(config_path),
                    no_color=True,
                )

        self.assertEqual(result, 1)
        self.assertIn("Configured hg19clinvar", output.getvalue())
        self.assertIn("Correct the reported hg19", output.getvalue())

    def test_missing_environment_configuration_fails_without_traceback(self) -> None:
        missing = "/definitely/missing/bff-tools-doctor.yaml"
        output = io.StringIO()
        with mock.patch.dict(
            os.environ, {CONFIG_PATH_ENV: missing}, clear=True
        ), contextlib.redirect_stdout(output):
            result = doctor.run_doctor(no_color=True)

        self.assertEqual(result, 1)
        self.assertIn(missing, output.getvalue())
        self.assertIn("Select an existing YAML", output.getvalue())

    def test_b37_alias_and_cli_dispatch_use_selected_options(self) -> None:
        annotation = doctor.DoctorCheck("PASS", "Raw VCF annotation", "ready")
        with mock.patch.object(
            doctor, "_annotation_checks", return_value=([], annotation)
        ) as inspect, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(doctor.run_doctor(genome="b37", no_color=True), 0)
        inspect.assert_called_once_with(None, "hs37")

        with mock.patch("bff_tools.cli.run_doctor", return_value=0) as run:
            self.assertEqual(
                cli.main(
                    [
                        "doctor",
                        "--config",
                        "site.yaml",
                        "--genome",
                        "hg38",
                        "--no-color",
                    ]
                ),
                0,
            )
        run.assert_called_once_with(
            config_file="site.yaml",
            genome="hg38",
            no_color=True,
        )

    def test_schema_and_asset_helpers_report_failures(self) -> None:
        with mock.patch.object(
            doctor, "validate_schemas", side_effect=ValidatorError("schema broken")
        ):
            result = doctor._schema_check()
        self.assertEqual(result.status, "FAIL")
        self.assertIn("schema broken", result.detail)

        missing = doctor._check_files("Assets", (Path("/missing/asset"),))
        self.assertEqual(missing.status, "FAIL")
        self.assertIn("Reinstall", missing.fix or "")

    def test_command_and_bundle_helpers_cover_failure_modes(self) -> None:
        with mock.patch("bff_tools.doctor.shutil.which", return_value=None):
            self.assertEqual(doctor._command_check("Bash", "bash").status, "FAIL")
            self.assertEqual(
                doctor._commands_check("Filters", "grep", "zgrep").status,
                "FAIL",
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            missing = doctor._bundle_check(root)
            self.assertEqual(missing.status, "FAIL")
            self.assertIn(INSTALL_MARKER, missing.detail)

            self._standard_bundle(root)
            self.assertEqual(doctor._bundle_check(root).status, "PASS")

    def test_invalid_yaml_and_default_config_errors_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "broken.yaml"
            config_path.write_text("broken: [\n", encoding="utf-8")
            output = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(
                output
            ):
                self.assertEqual(
                    doctor.run_doctor(config_file=str(config_path), no_color=True),
                    1,
                )
        self.assertIn("Cannot parse YAML", output.getvalue())

        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            doctor, "default_config_path", side_effect=ConfigError("default broken")
        ), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(doctor.run_doctor(no_color=True), 1)
        self.assertIn("default broken", output.getvalue())


if __name__ == "__main__":
    unittest.main()

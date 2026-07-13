from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools.config import (  # noqa: E402
    CONFIG_PATH_ENV,
    ConfigError,
    default_config_path,
    load_yaml_file,
    read_config_file,
    read_param_file,
)


class ConfigTests(unittest.TestCase):
    def test_load_yaml_file_reads_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yaml"
            path.write_text("key1: value1\nkey2: 2\n", encoding="utf-8")
            data = load_yaml_file(path)
            self.assertEqual(data["key1"], "value1")
            self.assertEqual(data["key2"], 2)

    def test_load_yaml_file_rejects_invalid_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yaml"
            path.write_text("badkey: value\n", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_yaml_file(path, allowed_keys=["goodkey"])

    def test_read_param_file_returns_expected_keys(self) -> None:
        params = read_param_file({"mode": "vcf"})
        self.assertIn("jobid", params)
        self.assertIn("log", params)
        self.assertIn("threads", params)
        self.assertTrue(params["annotate"])
        self.assertIsInstance(params, dict)

    def test_cli_values_override_parameter_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "params.yaml"
            path.write_text("annotate: true\ngenome: hg19\ndatasetid: from-yaml\n", encoding="utf-8")
            params = read_param_file(
                {
                    "mode": "vcf",
                    "paramfile": str(path),
                    "annotate": False,
                    "genome": "hg38",
                    "datasetid": "from-cli",
                }
            )
        self.assertFalse(params["annotate"])
        self.assertEqual(params["genome"], "hg38")
        self.assertEqual(params["datasetid"], "from-cli")

    def test_basic_vcf_config_needs_no_external_reference_bundle(self) -> None:
        with mock.patch("bff_tools.config.default_config_path", return_value=Path("/missing/config.yaml")):
            config = read_config_file(None, mode="vcf", annotate=False)
        self.assertTrue(Path(config["bash4bff"]).is_file())
        self.assertTrue(Path(config["vcf_converter"]).is_file())
        self.assertTrue(Path(config["pythonbin"]).is_file())
        self.assertNotIn("hg19fasta", config)

    def test_annotation_profile_reports_missing_configuration(self) -> None:
        with mock.patch("bff_tools.config.default_config_path", return_value=Path("/missing/config.yaml")):
            with self.assertRaisesRegex(ConfigError, "Annotation requires --config"):
                read_config_file(None, mode="vcf", annotate=True)

    def test_requested_threads_control_runtime_parameters(self) -> None:
        params = read_param_file({"mode": "vcf", "threads": 4})
        self.assertEqual(params["threads"], 4)
        self.assertEqual(params["threadsless"], 4)
        if "pigz" in params["zip"]:
            self.assertEqual(params["zip"], "/usr/bin/pigz")

    def test_tsv_mode_routes_input_through_tsv2vcf(self) -> None:
        params = read_param_file({"mode": "tsv", "inputfile": "cohort.tsv.gz"})
        self.assertEqual(params["pipeline"]["tsv2vcf"], 1)
        self.assertEqual(params["pipeline"]["vcf2bff"], 1)

    def test_tsv_mode_requires_annotation(self) -> None:
        with self.assertRaisesRegex(ConfigError, "annotate.*enabled"):
            read_param_file(
                {
                    "mode": "tsv",
                    "inputfile": "cohort.tsv.gz",
                    "annotate": False,
                }
            )

    def test_default_config_path_uses_repository_default(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            path = default_config_path()
        self.assertEqual(path, ROOT / "bin" / "config.yaml")

    def test_default_config_path_uses_environment_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "annotation.yaml"
            config_path.write_text("base: /data\n", encoding="utf-8")
            with mock.patch.dict(
                "os.environ",
                {CONFIG_PATH_ENV: str(config_path)},
                clear=False,
            ):
                path = default_config_path()
        self.assertEqual(path, config_path)

    def test_default_config_path_rejects_missing_environment_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "missing.yaml"
            with mock.patch.dict(
                "os.environ",
                {CONFIG_PATH_ENV: str(config_path)},
                clear=False,
            ):
                with self.assertRaisesRegex(ConfigError, CONFIG_PATH_ENV):
                    default_config_path()


if __name__ == "__main__":
    unittest.main()

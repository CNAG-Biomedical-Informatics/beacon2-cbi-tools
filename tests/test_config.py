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

from bff_tools.config import ConfigError, default_config_path, load_yaml_file, read_param_file  # noqa: E402


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
        self.assertIsInstance(params, dict)

    def test_default_config_path_uses_host_override(self) -> None:
        with mock.patch("bff_tools.config.socket.gethostname", return_value="mrueda-ws5"):
            with mock.patch.dict("os.environ", {"USER": "mrueda"}, clear=False):
                path = default_config_path()
        self.assertEqual(path.name, "mrueda_ws1_config.yaml")


if __name__ == "__main__":
    unittest.main()

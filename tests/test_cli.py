from __future__ import annotations

import contextlib
import io
import subprocess
import unittest
from pathlib import Path
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools import cli  # noqa: E402


class CliTests(unittest.TestCase):
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

    def test_goodbye_list_is_not_empty(self) -> None:
        self.assertTrue(cli.GOODBYES)

    def test_handle_validate_delegates_to_validator(self) -> None:
        with mock.patch("bff_tools.cli.subprocess.run") as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(args=["validator"], returncode=7)
            result = cli.handle_validate(["-i", "input.xlsx"])
        self.assertEqual(result, 7)
        run_mock.assert_called_once()

    def test_bin_bff_tools_help_runs(self) -> None:
        result = subprocess.run(
            [str(ROOT / "bin" / "bff-tools"), "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("usage: bff-tools", result.stdout)
        self.assertIn("validate", result.stdout)


if __name__ == "__main__":
    unittest.main()

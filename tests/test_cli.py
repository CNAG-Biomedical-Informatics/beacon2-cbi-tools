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

    def test_main_reports_config_error_without_traceback(self) -> None:
        stderr = io.StringIO()
        with mock.patch("bff_tools.cli.read_config_file", side_effect=cli.ConfigError("bad config")):
            with contextlib.redirect_stderr(stderr):
                result = cli.main(["tsv", "-i", "input.tsv"])
        self.assertEqual(result, 1)
        self.assertEqual(stderr.getvalue().strip(), "Error: bad config")

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


if __name__ == "__main__":
    unittest.main()

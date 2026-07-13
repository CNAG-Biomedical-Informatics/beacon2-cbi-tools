from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools import output  # noqa: E402


class OutputTests(unittest.TestCase):
    def test_plain_and_duration_formatting_cover_boundaries(self) -> None:
        self.assertEqual(output._plain(None), "(undef)")
        self.assertEqual(output._plain(""), "(undef)")
        self.assertEqual(output._plain(0), "0")
        self.assertEqual(output.format_duration(-2), "0s")
        self.assertEqual(output.format_duration(61), "1m 1s")
        self.assertEqual(output.format_duration(3661), "1h 1m 1s")

    def test_short_path_handles_empty_home_long_and_resolution_failures(self) -> None:
        self.assertEqual(output.short_path(None), "(undef)")
        self.assertEqual(output.short_path(""), "(undef)")
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            nested = home / "one" / "two" / "three" / "four"
            with mock.patch("pathlib.Path.home", return_value=home):
                self.assertEqual(output.short_path(nested), "~/one/two/three/four")
        with mock.patch("pathlib.Path.resolve", side_effect=OSError("no resolve")):
            self.assertEqual(output.short_path("relative/path"), "relative/path")
        self.assertEqual(
            output.short_path("/one/two/three/four/five"), ".../three/four/five"
        )

    def test_mapping_and_run_summary_render_redacted_structured_output(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            output._print_mapping("Empty", {}, output.BLUE, use_color=False)
            output.print_run_summary(
                arg={
                    "mode": "vcf",
                    "inputfile": "/tmp/input.vcf",
                    "configfile": "config.yaml",
                    "threads": 2,
                    "debug": 1,
                    "verbose": True,
                    "nocolor": True,
                    "noemoji": True,
                    "projectdir_override": "output",
                },
                config={
                    "mongodburi": "mongodb://root:secret@host:27017/db"
                },
                param={
                    "projectdir": "/tmp/output",
                    "jobid": "42",
                    "genome": "hg19",
                    "threads": 2,
                    "log": "/tmp/output/log.json",
                    "pipeline": {"vcf2bff": 1},
                },
                version="2.0.13-dev",
                executable=Path("/tmp/bff-tools"),
                no_color=True,
                no_emoji=True,
            )
        rendered = stream.getvalue()
        self.assertIn("BFF-Tools 2.0.13-dev", rendered)
        self.assertIn("--debug", rendered)
        self.assertIn("<redacted>@host:27017", rendered)
        self.assertNotIn("secret", rendered)
        self.assertIn("See /tmp/output/log.json", rendered)

    def test_banners_status_and_color_controls(self) -> None:
        stream = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(
            stream
        ):
            output.print_start_banner()
            output.print_pipeline_status("vcf2bff")
            output.print_pipeline_status("custom", no_emoji=True)
            output.print_finish_banner(runtime=65, goodbye="Adios")
        rendered = stream.getvalue()
        self.assertIn("\033[", rendered)
        self.assertIn("🧬 VCF2BFF", rendered)
        self.assertIn("CUSTOM", rendered)
        self.assertIn("1m 5s", rendered)
        self.assertIn("👋 Adios", rendered)

        plain = io.StringIO()
        with mock.patch.dict(
            os.environ, {"ANSI_COLORS_DISABLED": "1"}
        ), contextlib.redirect_stdout(plain):
            output.print_start_banner(no_emoji=True)
            output.print_finish_banner(runtime=1, goodbye="Bye", no_emoji=True)
        self.assertNotIn("\033[", plain.getvalue())
        self.assertIn("Bye", plain.getvalue())


if __name__ == "__main__":
    unittest.main()

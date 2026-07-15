from __future__ import annotations

import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools.demo import DemoError, run_demo  # noqa: E402


class DemoTests(unittest.TestCase):
    def test_demo_builds_valid_bff_browser_and_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "demo"
            result = run_demo(output)

            self.assertEqual(result.records, 1044)
            self.assertTrue(result.bff_path.is_file())
            self.assertIsNotNone(result.browser_path)
            self.assertTrue(result.browser_path and result.browser_path.is_file())
            self.assertIn(
                "No external annotation databases",
                (output / "README.txt").read_text(encoding="utf-8"),
            )
            with gzip.open(result.bff_path, "rt", encoding="utf-8") as handle:
                records = json.load(handle)
            self.assertEqual(len(records), 1044)

            with self.assertRaisesRegex(DemoError, "already exists"):
                run_demo(output)

    def test_demo_can_skip_browser(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_demo(Path(tmpdir) / "demo", browser=False)
            self.assertIsNone(result.browser_path)
            self.assertIn(
                "Browser generation was disabled",
                (result.output_dir / "README.txt").read_text(encoding="utf-8"),
            )

    def test_demo_removes_partial_output_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "demo"
            with mock.patch(
                "bff_tools.demo.convert_vcf",
                side_effect=OSError("simulated write failure"),
            ):
                with self.assertRaisesRegex(DemoError, "simulated write failure"):
                    run_demo(output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

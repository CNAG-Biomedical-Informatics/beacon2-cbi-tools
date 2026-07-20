from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools import VERSION, __version__  # noqa: E402
from bff_tools.cli import VERSION as CLI_VERSION  # noqa: E402
from bff_tools.vcf2bff import VERSION as CONVERTER_VERSION  # noqa: E402


class VersionTests(unittest.TestCase):
    def test_runtime_versions_use_the_canonical_python_version(self) -> None:
        self.assertEqual(__version__, VERSION)
        self.assertEqual(CLI_VERSION, VERSION)
        self.assertEqual(CONVERTER_VERSION, VERSION)

    def test_converter_remains_directly_executable(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SRC / "bff_tools" / "vcf2bff.py"), "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn(VERSION, result.stdout)


if __name__ == "__main__":
    unittest.main()

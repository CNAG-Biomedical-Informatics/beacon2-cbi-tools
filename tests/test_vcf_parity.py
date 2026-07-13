from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools.parity import compare_bff_files  # noqa: E402


class VcfParityTests(unittest.TestCase):
    def test_semantic_comparison_ignores_converter_provenance(self) -> None:
        expected = {
            "variantInternalId": "chr1_1_A_G",
            "variation": {"referenceBases": "A", "alternateBases": "G"},
            "_info": {"genome": "hg19", "vcf2bff": {"version": "perl"}},
        }
        actual = {
            "variation": {"alternateBases": "G", "referenceBases": "A"},
            "variantInternalId": "chr1_1_A_G",
            "_info": {"vcf2bff": {"version": "python"}, "genome": "hg19"},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            expected_path = Path(tmpdir) / "expected.json"
            actual_path = Path(tmpdir) / "actual.json"
            expected_path.write_text("[\n" + json.dumps(expected) + "\n]\n", encoding="utf-8")
            actual_path.write_text("[\n" + json.dumps(actual) + "\n]\n", encoding="utf-8")
            result = compare_bff_files(expected_path, actual_path)
        self.assertTrue(result.equal)
        self.assertEqual(result.records, 1)

    def test_semantic_comparison_reports_json_path_and_type_difference(self) -> None:
        expected = {"caseLevelData": [{"depth": "1"}]}
        actual = {"caseLevelData": [{"depth": 1}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            expected_path = Path(tmpdir) / "expected.json"
            actual_path = Path(tmpdir) / "actual.json"
            expected_path.write_text("[\n" + json.dumps(expected) + "\n]\n", encoding="utf-8")
            actual_path.write_text("[\n" + json.dumps(actual) + "\n]\n", encoding="utf-8")
            result = compare_bff_files(expected_path, actual_path)
        self.assertFalse(result.equal)
        self.assertEqual(result.path, "/caseLevelData/0/depth")
        self.assertEqual(result.expected, "1")
        self.assertEqual(result.actual, 1)

    def test_semantic_comparison_distinguishes_boolean_from_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            expected_path = Path(tmpdir) / "expected.json"
            actual_path = Path(tmpdir) / "actual.json"
            expected_path.write_text('[{"value": true}]\n', encoding="utf-8")
            actual_path.write_text('[{"value": 1}]\n', encoding="utf-8")
            result = compare_bff_files(expected_path, actual_path)
        self.assertFalse(result.equal)
        self.assertEqual(result.path, "/value")

    def test_semantic_comparison_accepts_equivalent_json_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            expected_path = Path(tmpdir) / "expected.json"
            actual_path = Path(tmpdir) / "actual.json"
            expected_path.write_text('[{"value": 1}]\n', encoding="utf-8")
            actual_path.write_text('[{"value": 1.0}]\n', encoding="utf-8")
            result = compare_bff_files(expected_path, actual_path)
        self.assertTrue(result.equal)

    @unittest.skipUnless(
        os.environ.get("BFF_CINECA_FIXTURE_DIR")
        and os.environ.get("BFF_PYTHON_SHADOW_OUTPUT"),
        "set BFF_CINECA_FIXTURE_DIR and BFF_PYTHON_SHADOW_OUTPUT for the full migration gate",
    )
    def test_external_cineca_fixture_matches_python_shadow_output(self) -> None:
        fixture_dir = Path(os.environ["BFF_CINECA_FIXTURE_DIR"])
        expected = fixture_dir / "genomicVariationsVcf.json.gz"
        actual = Path(os.environ["BFF_PYTHON_SHADOW_OUTPUT"])
        self.assertTrue(expected.is_file(), expected)
        self.assertTrue(actual.is_file(), actual)
        result = compare_bff_files(expected, actual)
        self.assertTrue(
            result.equal,
            f"first semantic difference at BFF record {result.first_difference}",
        )
        self.assertGreater(result.records, 0)


if __name__ == "__main__":
    unittest.main()

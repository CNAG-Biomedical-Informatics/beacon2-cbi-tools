from __future__ import annotations

import json
import tempfile
import unittest
import warnings
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools.validator import (  # noqa: E402
    ValidatorError,
    export_template,
    row_to_document,
    validate_inputs,
)


class ValidatorTests(unittest.TestCase):
    def test_row_to_document_preserves_workbook_mapping(self) -> None:
        headers = (
            "id",
            "sex.id",
            "active",
            "count",
            "tags",
            "measures_assayCode.id",
            "measures_assayCode.label",
        )
        values = (
            "person-1",
            "NCIT:C20197",
            "true",
            "4",
            '["alpha", "beta"]',
            "LOINC:1,LOINC:2",
            "First,Second",
        )
        self.assertEqual(
            row_to_document(headers, values),
            {
                "id": "person-1",
                "sex": {"id": "NCIT:C20197"},
                "active": True,
                "count": 4,
                "tags": ["alpha", "beta"],
                "measures": [
                    {"assayCode": {"id": "LOINC:1", "label": "First"}},
                    {"assayCode": {"id": "LOINC:2", "label": "Second"}},
                ],
            },
        )

    def test_row_to_document_rejects_malformed_json_cell(self) -> None:
        with self.assertRaisesRegex(ValidatorError, "Invalid JSON cell value"):
            row_to_document(("id", "values"), ("person-1", "[broken"))

    def test_json_validation_reports_schema_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "individuals.json"
            path.write_text('[{"id": "person-1"}]\n', encoding="utf-8")
            report = validate_inputs([path])
        self.assertFalse(report.ok)
        self.assertTrue(any("sex" in issue.message for issue in report.issues))

    def test_json_validation_accepts_valid_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "individuals.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "person-1",
                            "sex": {"id": "NCIT:C20197", "label": "male"},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            report = validate_inputs([path])
        self.assertTrue(report.ok)
        self.assertEqual(report.checked, 1)

    def test_mixed_xlsx_and_json_inputs_are_rejected(self) -> None:
        workbook = ROOT / "CINECA_synthetic_cohort_EUROPE_UK1" / "Beacon-v2-Models_CINECA_UK1.xlsx"
        individuals = ROOT / "CINECA_synthetic_cohort_EUROPE_UK1" / "bff" / "individuals.json"
        with self.assertRaisesRegex(ValidatorError, "cannot be mixed"):
            validate_inputs([workbook, individuals])

    def test_cineca_workbook_matches_perl_generated_bff_byte_for_byte(self) -> None:
        workbook = ROOT / "CINECA_synthetic_cohort_EUROPE_UK1" / "Beacon-v2-Models_CINECA_UK1.xlsx"
        expected_dir = ROOT / "CINECA_synthetic_cohort_EUROPE_UK1" / "bff"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Unknown extension is not supported")
                report = validate_inputs([workbook], output_dir=output_dir)
            self.assertTrue(report.ok)
            self.assertEqual(report.checked, 10018)
            for collection in (
                "analyses",
                "biosamples",
                "cohorts",
                "datasets",
                "individuals",
                "runs",
            ):
                actual = (output_dir / f"{collection}.json").read_bytes()
                expected = (expected_dir / f"{collection}.json").read_bytes()
                self.assertEqual(actual, expected, collection)

    def test_workbook_output_directory_is_created(self) -> None:
        workbook = ROOT / "CINECA_synthetic_cohort_EUROPE_UK1" / "Beacon-v2-Models_CINECA_UK1.xlsx"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "bff"
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Unknown extension is not supported")
                report = validate_inputs([workbook], output_dir=output_dir)
            self.assertTrue(report.ok)
            self.assertTrue((output_dir / "individuals.json").is_file())

    def test_template_export_writes_packaged_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "metadata.xlsx"
            export_template(destination)
            self.assertTrue(destination.is_file())
            self.assertGreater(destination.stat().st_size, 1000)
            with self.assertRaisesRegex(ValidatorError, "already exists"):
                export_template(destination)


if __name__ == "__main__":
    unittest.main()

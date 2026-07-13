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

from bff_tools.parity import compare_bff_files  # noqa: E402
import bff_tools.vcf_converter as vcf_converter  # noqa: E402
from bff_tools.vcf_converter import (  # noqa: E402
    ConversionError,
    convert_vcf,
    map_case_level_data,
)


class VcfConversionTests(unittest.TestCase):
    def test_unannotated_vcf_fails_with_actionable_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ConversionError, "SnpEff ANN header"):
                convert_vcf(
                    ROOT / "testdata" / "vcf" / "test_1000G.vcf.gz",
                    Path(tmpdir),
                    genome="hg19",
                    dataset_id="default_beacon_1",
                    project_dir="unannotated",
                    threads=1,
                )

    def test_gt_only_case_mapping_handles_variable_width_and_homozygous_calls(self) -> None:
        self.assertEqual(
            map_case_level_data(
                ("0", "10", "1/1", "0/1", "."),
                ("sample-0", "sample-1", "sample-2", "sample-3", "sample-4"),
                "GT",
            ),
            [
                {
                    "biosampleId": "sample-1",
                    "zygosity": {"id": "GENO:GENO:00000", "label": "10"},
                },
                {
                    "biosampleId": "sample-2",
                    "zygosity": {"id": "GENO:GENO_0000136", "label": "1/1"},
                },
                {
                    "biosampleId": "sample-3",
                    "zygosity": {"id": "GENO:GENO_0000458", "label": "0/1"},
                },
            ],
        )

    def test_case_level_data_preserves_depth_as_a_string(self) -> None:
        self.assertEqual(
            map_case_level_data(
                ("0/0:30", "0/1:12", "1/1:0", "./.:"),
                ("sample-0", "sample-1", "sample-2", "sample-3"),
                "GT:DP",
            ),
            [
                {
                    "biosampleId": "sample-1",
                    "zygosity": {
                        "id": "GENO:GENO_0000458",
                        "label": "0/1",
                    },
                    "depth": "12",
                },
                {
                    "biosampleId": "sample-2",
                    "zygosity": {
                        "id": "GENO:GENO_0000136",
                        "label": "1/1",
                    },
                    "depth": "0",
                },
            ],
        )

    def test_case_level_data_preserves_legacy_first_field_selection(self) -> None:
        self.assertEqual(
            map_case_level_data(
                ("10:0/0", "9:0/1"),
                ("selected", "not-selected"),
                "DP:GT",
            ),
            [
                {
                    "biosampleId": "selected",
                    "zygosity": {
                        "id": "GENO:GENO:00000",
                        "label": "0/0",
                    },
                    "depth": "10",
                }
            ],
        )

    def test_python_converter_matches_perl_generated_bff(self) -> None:
        fixture_dir = ROOT / "testdata" / "vcf" / "ref_beacon_166403275914916" / "vcf"
        source = fixture_dir / "test_1000G.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz"
        expected = fixture_dir / "genomicVariationsVcf.json.gz"
        with tempfile.TemporaryDirectory() as tmpdir:
            actual, records_written = convert_vcf(
                source,
                Path(tmpdir),
                genome="hg19",
                dataset_id="default_beacon_1",
                project_dir="beacon_166403275914916",
                threads=1,
            )
            result = compare_bff_files(expected, actual)
        self.assertEqual(records_written, 1044)
        self.assertTrue(
            result.equal,
            f"first semantic difference at BFF record {result.first_difference}",
        )

    def test_cineca_annotated_converter_matches_perl_generated_bff(self) -> None:
        fixture_dir = ROOT / "testdata" / "vcf" / "cineca_annotated"
        with tempfile.TemporaryDirectory() as tmpdir:
            actual, records_written = convert_vcf(
                fixture_dir / "fully_annotated.vcf.gz",
                Path(tmpdir),
                genome="hg19",
                dataset_id="CINECA_synthetic_cohort_EUROPE_UK1",
                project_dir="cineca_annotated_fixture",
                threads=1,
            )
            result = compare_bff_files(
                fixture_dir / "genomicVariationsVcf.json.gz",
                actual,
            )
        self.assertEqual(records_written, 4998)
        self.assertTrue(
            result.equal,
            f"first semantic difference at BFF record {result.first_difference}",
        )

    def test_standard_library_codec_fallback_matches_perl_output(self) -> None:
        fixture_dir = ROOT / "testdata" / "vcf" / "ref_beacon_166403275914916" / "vcf"
        source = fixture_dir / "test_1000G.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz"
        expected = fixture_dir / "genomicVariationsVcf.json.gz"
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                mock.patch.object(vcf_converter, "_igzip", None),
                mock.patch.object(vcf_converter, "_orjson", None),
            ):
                actual, records_written = vcf_converter.convert_vcf(
                    source,
                    Path(tmpdir),
                    genome="hg19",
                    dataset_id="default_beacon_1",
                    project_dir="beacon_166403275914916",
                    threads=1,
                )
            result = compare_bff_files(expected, actual)
        self.assertEqual(records_written, 1044)
        self.assertTrue(result.equal)


if __name__ == "__main__":
    unittest.main()

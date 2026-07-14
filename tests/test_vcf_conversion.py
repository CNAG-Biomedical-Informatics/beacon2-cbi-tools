from __future__ import annotations

import contextlib
import gzip
import io
import json
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
from bff_tools.validator import validate_inputs  # noqa: E402
import bff_tools.vcf2bff as vcf2bff  # noqa: E402
from bff_tools.vcf2bff import (  # noqa: E402
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

    def test_legacy_pathogenic_fixture_matches_perl_and_schema(self) -> None:
        fixture_dir = ROOT / "testdata" / "vcf" / "legacy_pathogenic"
        with tempfile.TemporaryDirectory() as tmpdir:
            actual, records_written = convert_vcf(
                fixture_dir / "test_pathogenic.vcf.gz",
                Path(tmpdir),
                genome="hg19",
                dataset_id="foo",
                project_dir="123456789",
                threads=1,
            )
            result = compare_bff_files(
                fixture_dir / "genomicVariationsVcf.json.gz",
                actual,
            )
            validation = validate_inputs([actual], streamed_genomic=True)
        self.assertEqual(records_written, 15)
        self.assertTrue(
            result.equal,
            f"first semantic difference at BFF record {result.first_difference}",
        )
        self.assertTrue(validation.ok, validation.issues)
        self.assertEqual(validation.checked, 15)
        self.assertEqual(
            [(collection.name, collection.checked) for collection in validation.collections],
            [("genomicVariations", 15)],
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
                mock.patch.object(vcf2bff, "_igzip", None),
                mock.patch.object(vcf2bff, "_orjson", None),
            ):
                actual, records_written = vcf2bff.convert_vcf(
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

    def test_jsonl_output_contains_one_complete_document_per_line(self) -> None:
        source = (
            ROOT
            / "testdata"
            / "vcf"
            / "ref_beacon_166403275914916"
            / "vcf"
            / "test_1000G.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path, records_written = convert_vcf(
                source,
                Path(tmpdir),
                genome="hg19",
                dataset_id="default_beacon_1",
                project_dir="jsonl-test",
                threads=1,
                jsonl=True,
            )
            with gzip.open(output_path, "rt", encoding="utf-8") as handle:
                documents = [json.loads(line) for line in handle if line.strip()]
            parity = compare_bff_files(
                source.parent / "genomicVariationsVcf.json.gz",
                output_path,
            )
        self.assertEqual(output_path.name, vcf2bff.JSONL_OUTPUT_NAME)
        self.assertEqual(records_written, 1044)
        self.assertEqual(len(documents), records_written)
        self.assertTrue(all(isinstance(document, dict) for document in documents))
        self.assertTrue(parity.equal)

    def test_converter_cli_supports_configurable_verbose_progress(self) -> None:
        source = (
            ROOT
            / "testdata"
            / "vcf"
            / "ref_beacon_166403275914916"
            / "vcf"
            / "test_1000G.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output), mock.patch(
                "builtins.print", wraps=print
            ) as print_mock:
                result = vcf2bff.main(
                    [
                        "-i",
                        str(source),
                        "--dataset-id",
                        "default_beacon_1",
                        "--project-dir",
                        "progress-test",
                        "--genome",
                        "hg19",
                        "--out-dir",
                        tmpdir,
                        "--threads",
                        "1",
                        "--verbose",
                        "--progress-every",
                        "500",
                    ]
                )
            self.assertEqual(result, 0)
            self.assertTrue((Path(tmpdir) / vcf2bff.OUTPUT_NAME).is_file())
        rendered = output.getvalue()
        self.assertIn("VCF records scanned = 500", rendered)
        self.assertIn("VCF records scanned = 1000", rendered)
        self.assertIn("Wrote 1044 variants", rendered)
        self.assertIn("vcf2bff finished OK", rendered)
        flushed = {
            call.args[0]
            for call in print_mock.call_args_list
            if call.kwargs.get("flush") is True
        }
        self.assertIn("Info: VCF records scanned = 500", flushed)
        self.assertIn("Info: VCF records scanned = 1000", flushed)
        self.assertIn("Info: vcf2bff finished OK", flushed)

    def test_converter_cli_rejects_invalid_runtime_arguments_and_errors(self) -> None:
        source = ROOT / "testdata" / "vcf" / "test_1000G.vcf.gz"
        common = [
            "-i",
            str(source),
            "--dataset-id",
            "dataset",
            "--project-dir",
            "project",
            "--genome",
            "hg19",
        ]
        for extra in (
            ["--out-dir", "/definitely/missing"],
            ["--threads", "0"],
            ["--progress-every", "0"],
        ):
            with self.subTest(extra=extra), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, "2"):
                    vcf2bff.main(common + extra)

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(
                vcf2bff, "convert_vcf", side_effect=ConversionError("bad record")
            ), contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaisesRegex(SystemExit, "1"):
                    vcf2bff.main(common + ["--out-dir", tmpdir])
            self.assertIn("bad record", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

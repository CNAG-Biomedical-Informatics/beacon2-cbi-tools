from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools.browser import (  # noqa: E402
    BrowserError,
    build_report_payload,
    generate_browser_report,
    load_bff_variants,
    variant_to_row,
)


def example_variant(*, gene: str = "BRCA1", impact: str = "HIGH") -> dict:
    return {
        "variantInternalId": "chr17_43071077_A_G",
        "identifiers": {
            "genomicHGVSId": "17:g.43071077A>G",
            "variantAlternativeIds": [
                {"id": "dbSNP:rs123"},
                {"id": "ClinVar:456"},
            ],
        },
        "_position": {"assemblyId": "hg38", "refseqId": "17", "startInteger": 43071076},
        "variantQuality": {"QUAL": 99, "FILTER": "PASS"},
        "variation": {
            "referenceBases": "A",
            "alternateBases": "G",
            "variantType": "SNP",
            "location": {"interval": {"start": {"value": 43071076}}},
        },
        "molecularAttributes": {
            "geneIds": [gene],
            "molecularEffects": [{"label": "missense"}],
            "aminoacidChanges": ["p.Lys1Arg"],
            "annotationImpact": [impact],
        },
        "variantLevelData": {
            "clinicalInterpretations": [
                {
                    "clinicalRelevance": "pathogenic",
                    "effect": {"label": "Hereditary breast cancer"},
                }
            ]
        },
        "caseLevelData": [
            {
                "biosampleId": "sample-1",
                "zygosity": {"label": "1|1"},
                "DP": 42,
            }
        ],
    }


class BrowserTests(unittest.TestCase):
    def test_variant_to_row_extracts_browser_fields_and_flags(self) -> None:
        row = variant_to_row(example_variant())
        self.assertEqual(row["geneIds"], "BRCA1")
        self.assertEqual(row["dbSNP"], "rs123")
        self.assertEqual(row["ClinVar"], "456")
        self.assertEqual(row["position"], 43071076)
        self.assertTrue(row["_pathogenic"])
        self.assertTrue(row["_homAlt"])

    def test_payload_keeps_only_selected_impacts_and_gene_panels(self) -> None:
        payload = build_report_payload(
            [
                example_variant(),
                example_variant(gene="TP53", impact="LOW"),
                example_variant(gene="NOT_IN_PANEL", impact="HIGH"),
            ],
            {"cancer": {"BRCA1", "TP53"}},
            project_id="project",
            job_id="job",
            source_name="input.json.gz",
        )
        self.assertEqual(payload["summary"]["variants"], 1)
        self.assertEqual(payload["summary"]["panels"], 1)
        self.assertEqual(payload["rows"][0]["_panels"], ["cancer"])

    def test_generate_browser_report_is_standalone_and_escapes_script_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / "variants.json.gz"
            panel_dir = tmp / "panels"
            output_path = tmp / "report.html"
            panel_dir.mkdir()
            (panel_dir / "cancer.lst").write_text("BRCA1\n", encoding="utf-8")
            variant = example_variant()
            variant["variantInternalId"] = "</script><script>alert(1)</script>"
            with gzip.open(input_path, "wt", encoding="utf-8") as handle:
                json.dump([variant], handle)

            summary = generate_browser_report(
                input_path,
                panel_dir,
                output_path,
                project_id="project <one>",
                job_id="job-1",
            )

            text = output_path.read_text(encoding="utf-8")
            self.assertEqual(summary["variants"], 1)
            self.assertIn("project &lt;one&gt;", text)
            self.assertIn("<\\/script><script>alert(1)<\\/script>", text)
            self.assertIn("new Tabulator", text)
            self.assertIn("pagination: true", text)
            self.assertIn("paginationSizeSelector: [25, 50, 100, 250]", text)
            self.assertIn("https://www.ncbi.nlm.nih.gov/snp/", text)
            self.assertIn("https://gnomad.broadinstitute.org/variant/", text)
            self.assertIn('"gnomad_r2_1"', text)
            self.assertIn('"gnomad_r4"', text)
            self.assertNotIn("flask", text.lower())
            self.assertNotIn("cdn.jsdelivr.net", text)

    def test_load_bff_variants_rejects_non_array_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.json"
            path.write_text('{"data": []}\n', encoding="utf-8")
            with self.assertRaises(BrowserError):
                load_bff_variants(path)


if __name__ == "__main__":
    unittest.main()

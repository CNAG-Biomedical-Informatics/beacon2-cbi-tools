from __future__ import annotations

import gzip
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

import bff_tools.browser as browser  # noqa: E402
from bff_tools.browser import (  # noqa: E402
    BrowserError,
    build_report_payload,
    generate_browser_report,
    iter_bff_variants,
    load_gene_panels,
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
        "variantQuality": {"QUAL": 99, "FILTER": "PASS", "DP": 120},
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
                "depth": "42",
            }
        ],
    }


def write_bff(path: Path, variants: list[object], *, jsonl: bool = False) -> None:
    opener = gzip.open if path.suffix == ".gz" else Path.open
    with opener(path, "wt", encoding="utf-8") as handle:
        if jsonl:
            for variant in variants:
                json.dump(variant, handle, separators=(",", ":"))
                handle.write("\n")
            return
        handle.write("[\n")
        for index, variant in enumerate(variants):
            if index:
                handle.write(",\n")
            json.dump(variant, handle, separators=(",", ":"))
        handle.write("\n]\n")


class BrowserTests(unittest.TestCase):
    def test_variant_to_row_extracts_browser_fields_and_flags(self) -> None:
        row = variant_to_row(example_variant())
        self.assertEqual(row["geneIds"], "BRCA1")
        self.assertEqual(row["dbSNP"], "rs123")
        self.assertEqual(row["ClinVar"], "456")
        self.assertEqual(row["position"], 43071076)
        self.assertNotIn("DP", row)
        self.assertEqual(row["biosampleId"], "sample-1 (1|1:42)")
        self.assertEqual(row["_conditionCount"], 1)
        self.assertEqual(row["_primaryCondition"], "Hereditary breast cancer")
        self.assertTrue(row["_pathogenic"])
        self.assertTrue(row["_homAlt"])

    def test_payload_keeps_only_selected_impacts_and_gene_panels(self) -> None:
        with mock.patch.object(browser, "variant_to_row", wraps=variant_to_row) as convert:
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
        self.assertEqual(payload["panelGenes"], {"cancer": 2})
        self.assertEqual(payload["rows"][0]["_panels"], ["cancer"])
        convert.assert_called_once()

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
            write_bff(input_path, [variant])

            summary = generate_browser_report(
                input_path,
                panel_dir,
                output_path,
                project_id="project <one>",
                job_id="job-1",
            )

            text = output_path.read_text(encoding="utf-8")
            self.assertEqual(summary["variants"], 1)
            self.assertIn("BFF Tools Browser", text)
            self.assertIn('id="detail-panel"', text)
            self.assertIn('id="panel-tabs"', text)
            self.assertIn("Panel results", text)
            self.assertIn("Panel-matched variants", text)
            self.assertIn('appendPanelTab("", "All panels"', text)
            self.assertIn('variantCount.toLocaleString() + " unique variants"', text)
            self.assertIn("Beacon v2 CBI Tools", text)
            self.assertNotIn('class="brand-mark"', text)
            self.assertIn('function effectFormatter(cell)', text)
            self.assertIn('.effect-chip.disruptive', text)
            self.assertNotIn("Variant landscape", text)
            self.assertIn("project &lt;one&gt;", text)
            self.assertIn("<\\/script><script>alert(1)<\\/script>", text)
            self.assertIn("new Tabulator", text)
            self.assertIn("pagination: true", text)
            self.assertIn("paginationSizeSelector: [25, 50, 100, 250]", text)
            self.assertIn('paginationElement: document.getElementById("table-pagination")', text)
            self.assertIn("height: availableTableHeight()", text)
            self.assertNotIn(("DP", "DP"), browser.COLUMNS)
            self.assertIn("https://www.ncbi.nlm.nih.gov/snp/", text)
            self.assertIn("https://gnomad.broadinstitute.org/variant/", text)
            self.assertIn('encodeURIComponent(prefix) + ":" + encodeURIComponent(accession)', text)
            self.assertNotIn("encodeURIComponent(match[1])", text)
            self.assertIn('"gnomad_r2_1"', text)
            self.assertIn('"gnomad_r4"', text)
            self.assertNotIn("flask", text.lower())
            self.assertNotIn("cdn.jsdelivr.net", text)

    def test_iter_bff_variants_rejects_non_array_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.json"
            path.write_text('{"data": []}\n', encoding="utf-8")
            with self.assertRaises(BrowserError):
                list(iter_bff_variants(path))

    def test_browser_inputs_report_io_json_and_panel_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            with self.assertRaisesRegex(BrowserError, "Cannot read BFF input"):
                list(iter_bff_variants(tmp / "missing.json"))

            malformed = tmp / "malformed.json"
            malformed.write_text('[\n{"impact":"HIGH",broken}\n]\n', encoding="utf-8")
            with self.assertRaisesRegex(BrowserError, "Cannot parse BFF input"):
                list(iter_bff_variants(malformed))

            valid = tmp / "valid.json"
            first = {"id": "one", "impact": "HIGH"}
            second = {"id": "two", "impact": "MODERATE"}
            write_bff(valid, [first, second])
            self.assertEqual(json.loads(valid.read_text(encoding="utf-8")), [first, second])
            variants = iter_bff_variants(valid)
            self.assertEqual(next(variants), first)
            self.assertEqual(list(variants), [second])

            jsonl = tmp / "valid.jsonl.gz"
            write_bff(jsonl, [first, second], jsonl=True)
            self.assertEqual(list(iter_bff_variants(jsonl)), [first, second])

            no_hits = tmp / "no-hits.json"
            write_bff(no_hits, [{"id": "low", "impact": "LOW"}])
            self.assertEqual(list(iter_bff_variants(no_hits)), [])

            non_object = tmp / "non-object.json"
            write_bff(non_object, ["HIGH"])
            with self.assertRaisesRegex(BrowserError, "one JSON object per line"):
                list(iter_bff_variants(non_object))

            with self.assertRaisesRegex(BrowserError, "does not exist"):
                load_gene_panels(tmp / "missing-panels")
            empty_panels = tmp / "empty-panels"
            empty_panels.mkdir()
            with self.assertRaisesRegex(BrowserError, "No .lst gene panels"):
                load_gene_panels(empty_panels)

    def test_large_report_warning_uses_rows_or_embedded_size(self) -> None:
        self.assertIsNone(browser._large_report_warning(49_999, 1024))
        self.assertIn(
            "50,000 panel-matched variants",
            browser._large_report_warning(50_000, 1024),
        )
        self.assertIn(
            "100.0 MiB",
            browser._large_report_warning(1, 100 * 1024 * 1024),
        )

    def test_gene_panels_and_sparse_variant_fields_are_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            panel_dir = Path(tmpdir)
            (panel_dir / "clinical.lst").write_text(
                "# comment\nBRCA1\n\nTP53\nBRCA1\n", encoding="utf-8"
            )
            self.assertEqual(
                load_gene_panels(panel_dir), {"clinical": {"BRCA1", "TP53"}}
            )

        row = variant_to_row(
            {
                "identifiers": {
                    "variantAlternativeIds": [
                        None,
                        {"id": "dbSNP:rs1, rs2"},
                        {"id": "ClinVar:CV1"},
                    ]
                },
                "molecularAttributes": {
                    "geneIds": [None, "BRCA1/TP53-ALT/", "BRCA1"],
                    "molecularEffects": [None, {"id": "SO:1"}],
                    "annotationImpact": ["MODERATE"],
                },
                "variantLevelData": {
                    "clinicalInterpretations": [
                        None,
                        {"effect": {"label": "Disease", "id": "MONDO:1"}},
                        {"effect": {"id": "MONDO:2"}, "clinicalRelevance": "benign"},
                    ]
                },
                "caseLevelData": [
                    None,
                    {"biosampleId": "sample-only"},
                    {"zygosity": {"label": "0/1"}, "depth": "0"},
                ],
            }
        )
        self.assertEqual(row["dbSNP"], "rs1, rs2")
        self.assertEqual(row["conditionId"], "Disease (MONDO:1), MONDO:2")
        self.assertEqual(row["biosampleId"], "sample-only, 0/1:0")
        self.assertEqual(row["_genes"], ["ALT", "BRCA1", "TP53", "TP53-ALT"])
        self.assertEqual(variant_to_row({})["clinicalRelevance"], "")

    def test_render_and_browser_cli_report_asset_and_generation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            with mock.patch.object(browser, "TEMPLATE_FILE", tmp / "missing.html"):
                with self.assertRaisesRegex(BrowserError, "template assets"):
                    browser.render_report({})

            with mock.patch.object(
                browser, "generate_browser_report", side_effect=BrowserError("bad report")
            ):
                with self.assertRaisesRegex(SystemExit, "bad report"):
                    browser.main(
                        [
                            "-i",
                            str(tmp / "input.json"),
                            "--panel-dir",
                            str(tmp),
                            "--project-id",
                            "project",
                            "--job-id",
                            "job",
                            "-o",
                            str(tmp / "report.html"),
                        ]
                    )

            with mock.patch.object(browser, "generate_browser_report") as generate:
                self.assertEqual(
                    browser.main(
                        [
                            "-i",
                            str(tmp / "input.json"),
                            "--panel-dir",
                            str(tmp),
                            "--project-id",
                            "project",
                            "--job-id",
                            "job",
                            "-o",
                            str(tmp / "report.html"),
                        ]
                    ),
                    0,
                )
            generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()

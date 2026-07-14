from __future__ import annotations

import contextlib
import gzip
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import bff_tools.vcf2bff as vcf2bff  # noqa: E402


ANN_FIELDS = (
    "Allele",
    "Annotation",
    "Annotation_Impact",
    "Gene_Name",
    "Gene_ID",
    "Feature_Type",
    "Feature_ID",
    "Transcript_BioType",
    "Rank",
    "HGVS.c",
    "HGVS.p",
    "cDNA.pos / cDNA.length",
    "CDS.pos / CDS.length",
    "AA.pos / AA.length",
    "Distance",
    "ERRORS / WARNINGS / INFO",
)
ANN_HEADER = (
    '##INFO=<ID=ANN,Number=.,Type=String,Description="Functional annotations: \''
    + " | ".join(ANN_FIELDS)
    + '\' ">'
)


def snpeff_annotation(
    allele: str,
    *,
    effect: str = "missense_variant",
    impact: str = "MODERATE",
    gene: str = "TP53",
    amino_acid: str = "p.Arg175His",
) -> str:
    values = [""] * len(ANN_FIELDS)
    values[0] = allele
    values[1] = effect
    values[2] = impact
    values[3] = gene
    values[10] = amino_acid
    return "|".join(values)


def write_vcf(directory: Path, records: list[str]) -> Path:
    path = directory / "fixture.vcf"
    path.write_text(
        "\n".join(
            (
                "##fileformat=VCFv4.2",
                ANN_HEADER,
                "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample-1\tsample-2",
                *records,
                "",
            )
        ),
        encoding="utf-8",
    )
    return path


class VcfMappingTests(unittest.TestCase):
    def test_perl_compatibility_primitives(self) -> None:
        truth_cases = (
            (None, False),
            ("", False),
            ("0", False),
            (0, False),
            ("0.0", True),
            (".", True),
        )
        for value, expected in truth_cases:
            with self.subTest(operation="truth", value=value):
                self.assertEqual(vcf2bff.perl_truth(value), expected)

        number_cases = (
            ("12", 12),
            ("1e-3", 0.001),
            ("0.12345678901234567", 0.123456789012346),
            ("not-a-number", 0),
        )
        for value, expected in number_cases:
            with self.subTest(operation="number", value=value):
                self.assertEqual(vcf2bff.perl_number(value), expected)

        self.assertEqual(vcf2bff.perl_split("a||b||", "|"), ["a", "", "b"])

    def test_annotation_metadata_uses_the_requested_assembly_without_mutating_constant(self) -> None:
        grch37 = vcf2bff.annotation_metadata("hg19")
        grch38 = vcf2bff.annotation_metadata("hg38")

        self.assertIn("vcf_GRCh37", grch37["toolReferences"]["databases"]["ClinVar"]["url"])
        self.assertIn("vcf_GRCh38", grch38["toolReferences"]["databases"]["ClinVar"]["url"])
        self.assertIn(
            "{genome}",
            vcf2bff.ANNOTATED_WITH["toolReferences"]["databases"]["ClinVar"]["url"],
        )

    def test_snp_eff_header_and_info_fields_are_parsed_explicitly(self) -> None:
        parsed_fields = vcf2bff.parse_ann_header(ANN_HEADER + "\n")
        self.assertEqual(parsed_fields[:5], list(ANN_FIELDS[:5]))
        self.assertEqual(parsed_fields[10], "HGVS.p")
        self.assertEqual(parsed_fields[11], "cDNA.pos_cDNA.length")
        self.assertEqual(parsed_fields[-1], "ERRORS_WARNINGS_INFO")
        self.assertEqual(
            vcf2bff.molecular_annotation_positions(parsed_fields),
            (3, 1, 10, 2),
        )

        self.assertEqual(
            vcf2bff.parse_info_field("DB;VT=SNP;EMPTY=", "chr1_10_A_G"),
            {"DB": "dummy", "VT": "SNP", "EMPTY": ""},
        )
        with self.assertRaisesRegex(vcf2bff.ConversionError, "Uneven INFO field count"):
            vcf2bff.parse_info_field("BROKEN=a=b", "chr1_10_A_G")

    def test_molecular_annotations_select_the_alt_and_preserve_transcripts(self) -> None:
        annotations = ",".join(
            (
                snpeff_annotation("A", gene="GENE1", amino_acid="p.Gly12Asp"),
                snpeff_annotation("C", gene="OTHER", amino_acid="p.Arg1Ter"),
                snpeff_annotation(
                    "A",
                    effect="splice_region_variant",
                    impact="LOW",
                    gene="GENE2",
                    amino_acid=".",
                ),
            )
        )

        self.assertEqual(
            vcf2bff.parse_molecular_attributes(annotations, (3, 1, 10, 2), "A"),
            {
                "geneIds": ["GENE1", "GENE2"],
                "aminoacidChanges": ["Gly12Asp", "."],
                "molecularEffects": [
                    {"id": "ENSGLOSSARY:0000150", "label": "missense_variant"},
                    {"id": "ENSGLOSSARY:0000152", "label": "splice_region_variant"},
                ],
                "annotationImpact": ["MODERATE", "LOW"],
            },
        )
        with self.assertRaisesRegex(KeyError, "G"):
            vcf2bff.parse_molecular_attributes(annotations, (3, 1, 10, 2), "G")

    def test_molecular_effect_mapping_handles_compound_intergenic_and_unknown_terms(self) -> None:
        cases = (
            ("missense_variant&splice_region_variant", "ENSGLOSSARY:0000150"),
            ("intergenic_region", "ENSGLOSSARY:0000174"),
            ("future_effect", "ENSGLOSSARY:0000000"),
        )
        for effect, expected in cases:
            with self.subTest(effect=effect):
                self.assertEqual(vcf2bff.map_molecular_effect_id(effect), expected)

    def test_population_frequencies_are_grouped_and_coerced(self) -> None:
        self.assertEqual(
            vcf2bff.map_frequency(
                {
                    "dbNSFP_1000Gp3_AFR_AF": "0.25,0.75",
                    "dbNSFP_1000Gp3_AMR_AF": "0",
                    "dbNSFP_ExAC_FIN_AF": "1e-3",
                }
            ),
            [
                {
                    "frequencies": [
                        {"population": "AFR", "alleleFrequency": 0.25}
                    ],
                    "source": "The 1000 Genomes Project Phase 3",
                    "sourceReference": "https://www.internationalgenome.org",
                    "version": "Extracted from dbNSFP4.1a",
                },
                {
                    "frequencies": [
                        {"population": "FIN", "alleleFrequency": 0.001}
                    ],
                    "source": "The Exome Aggregation Consortium (ExAC)",
                    "sourceReference": "https://gnomad.broadinstitute.org",
                    "version": "Extracted from dbNSFP4.1a",
                },
            ],
        )

    def test_identifier_precedence_and_fallbacks(self) -> None:
        variant = {"CHROM": "22", "POS": "100", "REF": "A", "ALT": "G"}
        cases = (
            (
                {
                    "dbNSFP_clinvar_hgvs": "NC_000022.10:g.100A>G",
                    "CLINVAR_CLNHGVS": "ignored",
                },
                "NC_000022.10:g.100A>G",
            ),
            ({"CLINVAR_CLNHGVS": "NC_000022.11:g.101A>G"}, "NC_000022.11:g.101A>G"),
            ({"dbNSFP_Ensembl_geneid": "ENSG1,ENSG2"}, "ENSG1:g.100A>G"),
            ({}, "22:g.100A>G"),
        )
        for info, expected in cases:
            with self.subTest(info=info):
                self.assertEqual(
                    vcf2bff.map_identifiers(variant, info)["genomicHGVSId"],
                    expected,
                )

    def test_external_and_transcript_identifiers_require_complete_pairs(self) -> None:
        variant = {"CHROM": "22", "POS": "100", "REF": "A", "ALT": "G"}
        identifiers = vcf2bff.map_identifiers(
            variant,
            {
                "dbNSFP_clinvar_hgvs": "NC_000022.10:g.100A>G",
                "dbNSFP_clinvar_id": "123",
                "dbNSFP_rs_dbSNP151": "rs456",
                "dbNSFP_HGVSp_snpEff": "p.Ala1Gly,p.Ala2Gly",
                "dbNSFP_Ensembl_proteinid": "ENSP1,ENSP2",
                "dbNSFP_HGVSc_snpEff": "c.1A>G,c.2A>G",
                "dbNSFP_Ensembl_transcriptid": "ENST1,ENST2",
            },
        )
        self.assertEqual(
            identifiers,
            {
                "genomicHGVSId": "NC_000022.10:g.100A>G",
                "clinvarVariantId": "clinvar:123",
                "proteinHGVSIds": ["ENSP1:p.Ala1Gly", "ENSP2:p.Ala2Gly"],
                "transcriptHGVSIds": ["ENST1:c.1A>G", "ENST2:c.2A>G"],
                "variantAlternativeIds": [
                    {
                        "id": "ClinVar:123",
                        "notes": "ClinVar Variation ID",
                        "reference": "https://www.ncbi.nlm.nih.gov/clinvar/variation/123",
                    },
                    {
                        "id": "dbSNP:rs456",
                        "notes": "dbSNP id",
                        "reference": "https://www.ncbi.nlm.nih.gov/snp/rs456",
                    },
                ],
            },
        )

        mismatched = vcf2bff.map_identifiers(
            variant,
            {
                "dbNSFP_HGVSp_snpEff": "p.Ala1Gly,p.Ala2Gly",
                "dbNSFP_Ensembl_proteinid": "ENSP1",
            },
        )
        self.assertNotIn("proteinHGVSIds", mismatched)

    def test_clinvar_interpretations_normalize_relevance_and_skip_empty_conditions(self) -> None:
        annotated_with = {"toolName": "SnpEff", "version": "test"}
        self.assertEqual(
            vcf2bff.map_variant_level_data(
                {
                    "CLINVAR_CLNDN": "Condition_one|Ignored_condition",
                    "CLINVAR_CLNDISDB": "MedGen:C1|.",
                    "CLINVAR_CLNSIG": "Likely_pathogenic/Pathogenic",
                    "CLINVAR_CLNSIGINCL": "123:Pathogenic",
                    "CLINVAR_ALLELEID": "456",
                },
                annotated_with,
            ),
            {
                "clinicalInterpretations": [
                    {
                        "conditionId": "Condition_one",
                        "category": {
                            "id": "MONDO:0000001",
                            "label": "disease or disorder",
                        },
                        "effect": {"id": "MedGen:C1", "label": "Condition_one"},
                        "clinicalRelevance": "likely pathogenic",
                        "_CLINVAR_CLNSIGINCL": "123:Pathogenic",
                        "_CLINVAR_ALLELEID": "456",
                        "annotatedWith": annotated_with,
                    }
                ]
            },
        )
        self.assertEqual(vcf2bff.map_variant_level_data({}, annotated_with), {})

        unsupported = vcf2bff.map_variant_level_data(
            {
                "CLINVAR_CLNDN": "Condition",
                "CLINVAR_CLNDISDB": "MedGen:C2",
                "CLINVAR_CLNSIG": "risk_factor",
            },
            annotated_with,
        )
        self.assertNotIn(
            "clinicalRelevance",
            unsupported["clinicalInterpretations"][0],
        )

    def test_complete_record_mapping_has_explicit_coordinates_types_and_quality(self) -> None:
        record = vcf2bff.map_record(
            {
                "CHROM": "22",
                "POS": "100",
                "REF": "A",
                "ALT": "T",
                "QUAL": "12.5",
                "FILTER": "PASS",
            },
            {"VT": "SNP", "DP": "999"},
            {
                "geneIds": ["GENE1"],
                "aminoacidChanges": ["Gly1Val"],
                "molecularEffects": [
                    {"id": "ENSGLOSSARY:0000150", "label": "missense_variant"}
                ],
                "annotationImpact": ["MODERATE"],
            },
            [
                {
                    "biosampleId": "sample-1",
                    "zygosity": {
                        "id": "GENO:GENO_0000458",
                        "label": "0/1",
                    },
                }
            ],
            "chr22_100_A_T",
            genome="hg19",
            dataset_id="dataset-1",
            provenance={"version": "test"},
            annotated_with={"toolName": "SnpEff"},
        )
        self.assertEqual(
            record,
            {
                "_info": {
                    "vcf2bff": {"version": "test"},
                    "genome": "hg19",
                    "datasetId": "dataset-1",
                },
                "caseLevelData": [
                    {
                        "biosampleId": "sample-1",
                        "zygosity": {
                            "id": "GENO:GENO_0000458",
                            "label": "0/1",
                        },
                    }
                ],
                "identifiers": {"genomicHGVSId": "22:g.100A>T"},
                "molecularAttributes": {
                    "geneIds": ["GENE1"],
                    "aminoacidChanges": ["Gly1Val"],
                    "molecularEffects": [
                        {
                            "id": "ENSGLOSSARY:0000150",
                            "label": "missense_variant",
                        }
                    ],
                    "annotationImpact": ["MODERATE"],
                },
                "_position": {
                    "assemblyId": "hg19",
                    "start": [99],
                    "end": [100],
                    "startInteger": 99,
                    "endInteger": 100,
                    "refseqId": "22",
                },
                "variantInternalId": "chr22_100_A_T",
                "variation": {
                    "referenceBases": "A",
                    "alternateBases": "T",
                    "variantType": "SNP",
                    "location": {
                        "sequence_id": "HGVSid:22:g.100A>T",
                        "type": "SequenceLocation",
                        "interval": {
                            "type": "SequenceInterval",
                            "start": {"type": "Number", "value": 99},
                            "end": {"type": "Number", "value": 100},
                        },
                    },
                },
                "variantQuality": {"QUAL": 12.5, "FILTER": "PASS"},
            },
        )
        self.assertNotIn("DP", record["variantQuality"])

    def test_chromosome_aliases_and_missing_quality_values(self) -> None:
        for chromosome, expected in (
            ("chr23", "X"),
            ("chr24", "Y"),
            ("chrM", "MT"),
            ("GL000220.1", ""),
        ):
            with self.subTest(chromosome=chromosome):
                record = vcf2bff.map_record(
                    {
                        "CHROM": chromosome,
                        "POS": "1",
                        "REF": "A",
                        "ALT": "G",
                        "QUAL": ".",
                        "FILTER": ".",
                    },
                    {"VT": "SNP"},
                    {},
                    [],
                    f"chr{chromosome}_1_A_G",
                    genome="hg38",
                    dataset_id="dataset",
                    provenance={},
                    annotated_with={},
                )
                self.assertEqual(record["_position"]["refseqId"], expected)
                self.assertEqual(
                    record["variantQuality"],
                    {"QUAL": None, "FILTER": None},
                )

    def test_gt_only_mapping_exercises_sparse_dense_and_truncated_inputs(self) -> None:
        self.assertEqual(vcf2bff.map_case_level_data("0/0\t./.", ("a", "b"), "GT"), [])
        self.assertEqual(vcf2bff.map_case_level_data((), (), "GT"), [])

        sparse = vcf2bff.map_case_level_data(
            "0/0\t0|1\t1|1\t./.\t1",
            ("ref", "het", "hom", "missing", "haploid"),
            "GT",
        )
        self.assertEqual([item["biosampleId"] for item in sparse], ["het", "hom", "haploid"])
        self.assertEqual(sparse[0]["zygosity"]["id"], "GENO:GENO_0000458")
        self.assertEqual(sparse[1]["zygosity"]["id"], "GENO:GENO_0000136")
        self.assertEqual(sparse[2]["zygosity"]["id"], "GENO:GENO:00000")

        sample_ids = tuple(f"sample-{index}" for index in range(257))
        dense = vcf2bff.map_case_level_data("\t".join(["0/1"] * 257), sample_ids, "GT")
        self.assertEqual(len(dense), 257)
        self.assertEqual(dense[0]["biosampleId"], "sample-0")
        self.assertEqual(dense[-1]["biosampleId"], "sample-256")

        truncated = vcf2bff.map_case_level_data(("0/1", "1/1"), ("only",), "GT")
        self.assertEqual([item["biosampleId"] for item in truncated], ["only"])

    def test_multifield_genotypes_keep_sample_depth_as_text(self) -> None:
        self.assertEqual(
            vcf2bff.map_case_level_data(
                "0/0:30\t0|1:12\t1|1:0\t./.:.",
                ("ref", "het", "hom", "missing"),
                "GT:DP",
            ),
            [
                {
                    "biosampleId": "het",
                    "zygosity": {
                        "id": "GENO:GENO_0000458",
                        "label": "0|1",
                    },
                    "depth": "12",
                },
                {
                    "biosampleId": "hom",
                    "zygosity": {
                        "id": "GENO:GENO_0000136",
                        "label": "1|1",
                    },
                    "depth": "0",
                },
            ],
        )

    def test_stream_conversion_infers_types_and_skips_unsupported_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_vcf(
                Path(tmpdir),
                [
                    "\t".join(
                        (
                            "1",
                            "10",
                            ".",
                            "A",
                            "G",
                            "42",
                            "PASS",
                            f"ANN={snpeff_annotation('G')};DB",
                            "GT",
                            "0/0",
                            "0/1",
                        )
                    ),
                    "\t".join(
                        (
                            "1",
                            "20",
                            ".",
                            "AT",
                            "A",
                            ".",
                            ".",
                            f"VT=SNP,INDEL;ANN={snpeff_annotation('A', gene='GENE2')}",
                            "GT",
                            "1/1",
                            "0/0",
                        )
                    ),
                    "1\t30\t.\tA\t<DEL>\t.\tPASS\t.\tGT\t0/1\t0/0",
                    "1\t40\t.\tC\tT\t.\tPASS\tVT=SNP\tGT\t0/1\t0/0",
                ],
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                records = list(
                    vcf2bff.iter_bff_records(
                        path,
                        genome="hg19",
                        dataset_id="dataset",
                        provenance={"version": "test"},
                    )
                )

        self.assertEqual([record["variantInternalId"] for record in records], ["chr1_10_A_G", "chr1_20_AT_A"])
        self.assertEqual([record["variation"]["variantType"] for record in records], ["SNP", "INDEL"])
        self.assertEqual(records[0]["caseLevelData"][0]["biosampleId"], "sample-2")
        self.assertEqual(records[1]["caseLevelData"][0]["biosampleId"], "sample-1")
        self.assertIn("Skipping <chr1_40_C_T>", stderr.getvalue())

    def test_stream_conversion_rejects_short_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_vcf(Path(tmpdir), ["1\t10\t."])
            with self.assertRaisesRegex(vcf2bff.ConversionError, "fewer than 8 columns"):
                list(
                    vcf2bff.iter_bff_records(
                        path,
                        genome="hg19",
                        dataset_id="dataset",
                        provenance={},
                    )
                )

    def test_empty_json_array_and_jsonl_outputs_remain_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            source = write_vcf(
                directory,
                ["1\t10\t.\tA\t<DEL>\t.\tPASS\t.\tGT\t0/1\t0/0"],
            )
            array_path, array_records = vcf2bff.convert_vcf(
                source,
                directory,
                genome="hg19",
                dataset_id="dataset",
                project_dir="project",
                threads=1,
            )
            with gzip.open(array_path, "rt", encoding="utf-8") as handle:
                self.assertEqual(json.load(handle), [])

            jsonl_path, jsonl_records = vcf2bff.convert_vcf(
                source,
                directory,
                genome="hg19",
                dataset_id="dataset",
                project_dir="project",
                threads=1,
                jsonl=True,
            )
            with gzip.open(jsonl_path, "rt", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "")

        self.assertEqual(array_records, 0)
        self.assertEqual(jsonl_records, 0)


if __name__ == "__main__":
    unittest.main()

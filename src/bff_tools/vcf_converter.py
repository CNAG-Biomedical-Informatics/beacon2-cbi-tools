from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import socket
import sys
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Sequence, TextIO

try:
    import orjson as _orjson
except ImportError:  # pragma: no cover - exercised by the explicit fallback test
    _orjson = None

try:
    from isal import igzip as _igzip
except ImportError:  # pragma: no cover - exercised by the explicit fallback test
    _igzip = None

try:
    from .version import VERSION
except ImportError:  # pragma: no cover - direct script execution from the source tree
    from version import VERSION

OUTPUT_NAME = "genomicVariationsVcf.json.gz"
ISAL_COMPRESSLEVEL = 2
STDLIB_COMPRESSLEVEL = 6
SPARSE_GT_THRESHOLD = 256

ANNOTATED_WITH = {
    "toolName": "SnpEff",
    "version": "5.0",
    "toolReferences": {
        "bio.toolsId": "https://bio.tools/snpeff",
        "url": "https://pcingola.github.io/SnpEff",
        "databases": {
            "ClinVar": {
                "url": "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_{genome}/",
                "version": "20250312",
            },
            "COSMIC": {
                "url": "https://cosmic-blog.sanger.ac.uk/cosmic-release-v92",
                "version": "COSMICv92",
            },
            "dbNSFP": {
                "url": "https://sites.google.com/site/jpopgen/dbNSFP",
                "version": "dbNSFP4.1a",
            },
        },
    },
}

CHROMOSOME_NAMES = {
    **{str(value): str(value) for value in range(1, 23)},
    **{f"chr{value}": str(value) for value in range(1, 23)},
    "X": "X",
    "Y": "Y",
    "chr23": "X",
    "23": "X",
    "chr24": "Y",
    "24": "Y",
    "chr25": "XY",
    "25": "XY",
    "chr26": "MT",
    "26": "MT",
    "chrM": "MT",
    "M": "MT",
}

SEQUENCE_ONTOLOGY = {
    "transcript_ablation": "SO:0001893",
    "splice_acceptor_variant": "SO:0001574",
    "splice_donor_variant": "SO:0001575",
    "stop_gained": "SO:0001587",
    "frameshift_variant": "SO:0001589",
    "stop_lost": "SO:0001578",
    "start_lost": "SO:0002012",
    "transcript_amplification": "SO:0001889",
    "feature_elongation": "SO:0001907",
    "feature_truncation": "SO:0001906",
    "inframe_insertion": "SO:0001821",
    "inframe_deletion": "SO:0001822",
    "missense_variant": "SO:0001583",
    "protein_altering_variant": "SO:0001818",
    "splice_donor_5th_base_variant": "SO:0001787",
    "splice_region_variant": "SO:0001630",
    "splice_donor_region_variant": "SO:0002170",
    "splice_polypyrimidine_tract_variant": "SO:0002169",
    "incomplete_terminal_codon_variant": "SO:0001626",
    "start_retained_variant": "SO:0002019",
    "stop_retained_variant": "SO:0001567",
    "synonymous_variant": "SO:0001819",
    "coding_sequence_variant": "SO:0001580",
    "mature_miRNA_variant": "SO:0001620",
    "5_prime_UTR_variant": "SO:0001623",
    "3_prime_UTR_variant": "SO:0001624",
    "non_coding_transcript_exon_variant": "SO:0001792",
    "intron_variant": "SO:0001627",
    "NMD_transcript_variant": "SO:0001621",
    "non_coding_transcript_variant": "SO:0001619",
    "coding_transcript_variant": "SO:0001968",
    "upstream_gene_variant": "SO:0001631",
    "downstream_gene_variant": "SO:0001632",
    "TFBS_ablation": "SO:0001895",
    "TFBS_amplification": "SO:0001892",
    "TF_binding_site_variant": "SO:0001782",
    "regulatory_region_ablation": "SO:0001894",
    "regulatory_region_amplification": "SO:0001891",
    "regulatory_region_variant": "SO:0001566",
    "intergenic_variant": "SO:0001628",
    "sequence_variant": "SO:0001060",
}

ENSEMBL_GLOSSARY = {
    "Transcript_ablation": "ENSGLOSSARY:0000140",
    "Splice_acceptor_variant": "ENSGLOSSARY:0000141",
    "Splice_donor_variant": "ENSGLOSSARY:0000142",
    "Stop_gained": "ENSGLOSSARY:0000143",
    "Frameshift_variant": "ENSGLOSSARY:0000144",
    "Stop_lost": "ENSGLOSSARY:0000145",
    "Start_lost": "ENSGLOSSARY:0000146",
    "Transcript_amplification": "ENSGLOSSARY:0000147",
    "Inframe_insertion": "ENSGLOSSARY:0000148",
    "Inframe_deletion": "ENSGLOSSARY:0000149",
    "Missense_variant": "ENSGLOSSARY:0000150",
    "Protein_altering_variant": "ENSGLOSSARY:0000151",
    "Splice_region_variant": "ENSGLOSSARY:0000152",
    "Incomplete_terminal_codon_variant": "ENSGLOSSARY:0000153",
    "Stop_retained_variant": "ENSGLOSSARY:0000154",
    "Synonymous_variant": "ENSGLOSSARY:0000155",
    "Coding_sequence_variant": "ENSGLOSSARY:0000156",
    "Mature_miRNA_variant": "ENSGLOSSARY:0000157",
    "5_prime_UTR_variant": "ENSGLOSSARY:0000158",
    "3_prime_UTR_variant": "ENSGLOSSARY:0000159",
    "Non_coding_transcript_exon_variant": "ENSGLOSSARY:0000160",
    "Intron_variant": "ENSGLOSSARY:0000161",
    "NMD_transcript_variant": "ENSGLOSSARY:0000162",
    "Non_coding_transcript_variant": "ENSGLOSSARY:0000163",
    "Upstream_gene_variant": "ENSGLOSSARY:0000164",
    "Downstream_gene_variant": "ENSGLOSSARY:0000165",
    "TFBS_ablation": "ENSGLOSSARY:0000166",
    "TFBS_amplification": "ENSGLOSSARY:0000167",
    "TF_binding_site_variant": "ENSGLOSSARY:0000168",
    "Regulatory_region_ablation": "ENSGLOSSARY:0000169",
    "Regulatory_region_amplification": "ENSGLOSSARY:0000170",
    "Feature_elongation": "ENSGLOSSARY:0000171",
    "Regulatory_region_variant": "ENSGLOSSARY:0000172",
    "Feature_truncation": "ENSGLOSSARY:0000173",
    "Intergenic_variant": "ENSGLOSSARY:0000174",
}

ZYGOSITY = {
    "0/1": "GENO_0000458",
    "0|1": "GENO_0000458",
    "1/0": "GENO_0000458",
    "1|0": "GENO_0000458",
    "1/1": "GENO_0000136",
    "1|1": "GENO_0000136",
}

FREQUENCY_POPULATIONS = ("AFR", "AMR", "EAS", "FIN", "NFE", "SAS")
FREQUENCY_SOURCES = (
    (
        "dbNSFP_1000Gp3",
        "The 1000 Genomes Project Phase 3",
        "https://www.internationalgenome.org",
    ),
    (
        "dbNSFP_ExAC",
        "The Exome Aggregation Consortium (ExAC)",
        "https://gnomad.broadinstitute.org",
    ),
    (
        "dbNSFP_gnomAD_exomes",
        "The Genome Aggregation Database (gnomAD)",
        "https://gnomad.broadinstitute.org",
    ),
)
DBNSFP_VERSION = ANNOTATED_WITH["toolReferences"]["databases"]["dbNSFP"]["version"]
IDENTIFIER_FIELDS = (
    ("proteinHGVSIds", "dbNSFP_HGVSp_snpEff", "dbNSFP_Ensembl_proteinid"),
    ("transcriptHGVSIds", "dbNSFP_HGVSc_snpEff", "dbNSFP_Ensembl_transcriptid"),
)
ALTERNATIVE_IDENTIFIERS = (
    (
        "ClinVar",
        "dbNSFP_clinvar_id",
        "ClinVar Variation ID",
        "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
    ),
    (
        "dbSNP",
        "dbNSFP_rs_dbSNP151",
        "dbSNP id",
        "https://www.ncbi.nlm.nih.gov/snp/",
    ),
)
ALLOWED_CLINICAL_RELEVANCE = frozenset(
    {
        "benign",
        "likely benign",
        "uncertain significance",
        "likely pathogenic",
        "pathogenic",
    }
)
MOLECULAR_ANNOTATION_FIELDS = (
    "Gene_Name",
    "Annotation",
    "HGVS.p",
    "Annotation_Impact",
)


class ConversionError(RuntimeError):
    pass


def perl_truth(value: Any) -> bool:
    return value is not None and value != "" and value != "0" and value != 0


def perl_number(value: str) -> int | float:
    try:
        # JSON::XS serializes Perl NV values with 15 significant digits.
        number = float(format(float(value), ".15g"))
    except (TypeError, ValueError):
        return 0
    return int(number) if number.is_integer() else number


def perl_split(value: str, delimiter: str) -> list[str]:
    fields = value.split(delimiter)
    while fields and fields[-1] == "":
        fields.pop()
    return fields


def annotation_metadata(genome: str) -> dict[str, Any]:
    assembly = "GRCh37" if genome in {"hs37", "hg19"} else "GRCh38"
    # Round-tripping provides a cheap deep copy of this small constant.
    metadata = json.loads(json.dumps(ANNOTATED_WITH))
    databases = metadata["toolReferences"]["databases"]
    for database in databases.values():
        if "url" in database:
            database["url"] = database["url"].replace("{genome}", assembly)
    return metadata


def parse_ann_header(line: str) -> list[str]:
    prefix = '##INFO=<ID=ANN,Number=.,Type=String,Description="Functional annotations: '
    value = line.rstrip("\n")
    if value.startswith(prefix):
        value = value[len(prefix) :]
    value = value.replace(" ", "").replace("'", "").replace('\">', "")
    value = value.replace("/", "_")
    fields = value.split("|")
    if not fields:
        raise ConversionError("Could not load SnpEff fields from the VCF header")
    return fields


def parse_info_field(value: str, uid: str) -> dict[str, str]:
    flattened: list[str] = []
    for field in value.split(";"):
        if "=" not in field:
            field += "=dummy"
        flattened.extend(field.split("="))
    if len(flattened) % 2:
        raise ConversionError(f"Uneven INFO field count for {uid}")
    return dict(zip(flattened[::2], flattened[1::2]))


def molecular_annotation_positions(names: Sequence[str]) -> tuple[int, int, int, int]:
    return tuple(names.index(name) for name in MOLECULAR_ANNOTATION_FIELDS)  # type: ignore[return-value]


def parse_molecular_attributes(
    value: str,
    positions: tuple[int, int, int, int],
    alternate: str,
) -> dict[str, Any]:
    gene_index, effect_index, amino_acid_index, impact_index = positions
    genes: list[str] = []
    amino_acids: list[str] = []
    molecular_effects: list[dict[str, str]] = []
    impacts: list[str] = []
    for raw_annotation in value.split(","):
        values = perl_split(raw_annotation, "|")
        allele = values[0] if values else ""
        if allele != alternate:
            continue
        gene = values[gene_index] if gene_index < len(values) else "."
        effect = values[effect_index] if effect_index < len(values) else "."
        amino_acid = values[amino_acid_index] if amino_acid_index < len(values) else "."
        impact = values[impact_index] if impact_index < len(values) else "."
        genes.append(gene)
        amino_acids.append(amino_acid[2:] if amino_acid.startswith("p.") else amino_acid)
        molecular_effects.append(
            {"id": map_molecular_effect_id(effect), "label": effect}
        )
        impacts.append(impact)
    if not genes:
        raise KeyError(alternate)
    return {
        "geneIds": genes,
        "aminoacidChanges": amino_acids,
        "molecularEffects": molecular_effects,
        "annotationImpact": impacts,
    }


def map_case_level_data(
    genotypes: Sequence[str] | str,
    sample_ids: Sequence[str],
    format_value: str,
) -> list[dict[str, Any]]:
    format_fields = format_value.split(":")
    mapped: list[dict[str, Any]] = []
    if len(format_fields) == 1:
        if not sample_ids or not genotypes:
            return mapped
        if isinstance(genotypes, str):
            genotype_blob = genotypes
            genotype_values = None
        else:
            limit = min(len(sample_ids), len(genotypes))
            if not limit:
                return mapped
            if len(genotypes) != limit:
                genotypes = genotypes[:limit]
            genotype_values = genotypes
            genotype_blob = "\t".join(genotype_values)
        alternate_alleles = genotype_blob.count("1")
        if not alternate_alleles:
            return mapped

        append = mapped.append
        get_zygosity = ZYGOSITY.get
        if alternate_alleles <= SPARSE_GT_THRESHOLD:
            cursor = 0
            sample_index = 0
            while True:
                position = genotype_blob.find("1", cursor)
                if position < 0:
                    break
                sample_index += genotype_blob.count("\t", cursor, position)
                if sample_index >= len(sample_ids):
                    break
                field_end = genotype_blob.find("\t", position)
                if genotype_values is None:
                    separator = genotype_blob.rfind("\t", cursor, position)
                    field_start = cursor if separator < 0 else separator + 1
                    genotype = genotype_blob[
                        field_start : field_end if field_end >= 0 else None
                    ]
                else:
                    genotype = genotype_values[sample_index]
                ontology = get_zygosity(genotype, "GENO:00000")
                append(
                    {
                        "biosampleId": sample_ids[sample_index],
                        "zygosity": {
                            "id": f"GENO:{ontology}",
                            "label": genotype,
                        },
                    }
                )
                if field_end < 0:
                    break
                cursor = field_end + 1
                sample_index += 1
            return mapped

        if genotype_values is None:
            genotype_values = genotype_blob.split("\t")
        for sample_id, genotype in zip(sample_ids, genotype_values):
            if "1" in genotype:
                ontology = get_zygosity(genotype, "GENO:00000")
                append(
                    {
                        "biosampleId": sample_id,
                        "zygosity": {
                            "id": f"GENO:{ontology}",
                            "label": genotype,
                        },
                    }
                )
        return mapped

    if isinstance(genotypes, str):
        genotypes = genotypes.split("\t") if genotypes else ()

    gt_indexes = tuple(
        index for index, field_name in enumerate(format_fields) if field_name == "GT"
    )
    dp_indexes = tuple(
        index for index, field_name in enumerate(format_fields) if field_name == "DP"
    )

    for sample_id, genotype in zip(sample_ids, genotypes):
        values = genotype.split(":")
        if not values or "1" not in values[0]:
            continue
        result: dict[str, Any] = {"biosampleId": sample_id}

        gt = None
        for index in reversed(gt_indexes):
            if index < len(values) and values[index] != "":
                gt = values[index]
                break
        if perl_truth(gt):
            ontology = ZYGOSITY.get(gt, "GENO:00000")
            result["zygosity"] = {"id": f"GENO:{ontology}", "label": gt}

        for index in reversed(dp_indexes):
            if index < len(values) and values[index] != "":
                result["depth"] = values[index]
                break
        mapped.append(result)
    return mapped


def map_frequency(info: dict[str, str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for database, source, reference in FREQUENCY_SOURCES:
        frequencies = []
        for population in FREQUENCY_POPULATIONS:
            value = info.get(f"{database}_{population}_AF")
            if perl_truth(value):
                allele_frequency = value.split(",", 1)[0]
                frequencies.append(
                    {
                        "population": population,
                        "alleleFrequency": perl_number(allele_frequency),
                    }
                )
        if frequencies:
            result.append(
                {
                    "frequencies": frequencies,
                    "source": source,
                    "sourceReference": reference,
                    "version": f"Extracted from {DBNSFP_VERSION}",
                }
            )
    return result


def map_identifiers(variant: dict[str, str], info: dict[str, str]) -> dict[str, Any]:
    identifiers: dict[str, Any] = {}
    if "dbNSFP_clinvar_hgvs" in info:
        identifiers["genomicHGVSId"] = info["dbNSFP_clinvar_hgvs"]
    elif "CLINVAR_CLNHGVS" in info:
        identifiers["genomicHGVSId"] = info["CLINVAR_CLNHGVS"]
    else:
        suffix = f":g.{variant['POS']}{variant['REF']}>{variant['ALT']}"
        genes = info.get("dbNSFP_Ensembl_geneid")
        gene = genes.split(",", 1)[0] if perl_truth(genes) else None
        identifiers["genomicHGVSId"] = f"{gene or variant['CHROM']}{suffix}"

    if perl_truth(info.get("dbNSFP_clinvar_id")):
        identifiers["clinvarVariantId"] = f"clinvar:{info['dbNSFP_clinvar_id']}"

    for output_key, hgvs_key, ensembl_key in IDENTIFIER_FIELDS:
        hgvs_ids = info[hgvs_key].split(",") if perl_truth(info.get(hgvs_key)) else []
        ensembl_ids = info[ensembl_key].split(",") if ensembl_key in info else []
        if ensembl_ids and len(ensembl_ids) == len(hgvs_ids):
            identifiers[output_key] = [
                f"{ensembl}:{hgvs}" for ensembl, hgvs in zip(ensembl_ids, hgvs_ids)
            ]

    for source, field, notes, reference in ALTERNATIVE_IDENTIFIERS:
        value = info.get(field)
        if perl_truth(value):
            identifiers.setdefault("variantAlternativeIds", []).append(
                {
                    "id": f"{source}:{value}",
                    "notes": notes,
                    "reference": f"{reference}{value}",
                }
            )
    return identifiers


def perl_ucfirst(value: str) -> str:
    return value[:1].upper() + value[1:]


def map_molecular_effect_id(value: str) -> str:
    if "&" in value:
        match = re.match(r"^(\w+)&", value)
        if match:
            value = match.group(1)
    if value == "intergenic_region":
        value = "Intergenic_variant"
    key = perl_ucfirst(value)
    return SEQUENCE_ONTOLOGY.get(key, ENSEMBL_GLOSSARY.get(key, "ENSGLOSSARY:0000000"))


def parse_acmg_value(value: str) -> str:
    match = re.search(r"(\w+)[/|,]", value)
    parsed = match.group(1) if match else value
    return parsed.lower().replace("_", " ")


def map_variant_level_data(
    info: dict[str, str], annotated_with: dict[str, Any]
) -> dict[str, Any]:
    if "CLINVAR_CLNDISDB" not in info or "CLINVAR_CLNDN" not in info:
        return {}
    condition_names = info["CLINVAR_CLNDN"].split("|")
    condition_databases = info["CLINVAR_CLNDISDB"].split("|")
    conditions = {
        name: condition_databases[index] if index < len(condition_databases) else None
        for index, name in enumerate(condition_names)
    }
    interpretations: list[dict[str, Any]] = []
    for condition, database in conditions.items():
        if database == ".":
            continue
        interpretation: dict[str, Any] = {
            "conditionId": condition,
            "category": {"id": "MONDO:0000001", "label": "disease or disorder"},
            "effect": {"id": database, "label": condition},
        }
        if "CLINVAR_CLNSIG" in info:
            relevance = parse_acmg_value(info["CLINVAR_CLNSIG"])
            if relevance in ALLOWED_CLINICAL_RELEVANCE:
                interpretation["clinicalRelevance"] = relevance
        if "CLINVAR_CLNSIGINCL" in info:
            interpretation["_CLINVAR_CLNSIGINCL"] = info["CLINVAR_CLNSIGINCL"]
        if "CLINVAR_ALLELEID" in info:
            interpretation["_CLINVAR_ALLELEID"] = info["CLINVAR_ALLELEID"]
        interpretation["annotatedWith"] = annotated_with
        interpretations.append(interpretation)
    return {"clinicalInterpretations": interpretations} if interpretations else {}


def map_record(
    variant: dict[str, str],
    info: dict[str, str],
    molecular_attributes: dict[str, Any],
    case_level_data: list[dict[str, Any]],
    uid: str,
    *,
    genome: str,
    dataset_id: str,
    provenance: dict[str, Any],
    annotated_with: dict[str, Any],
) -> dict[str, Any]:
    position = int(variant["POS"])
    start = position - 1
    identifiers = map_identifiers(variant, info)
    record: dict[str, Any] = {
        "_info": {
            "vcf2bff": provenance,
            "genome": genome,
            "datasetId": dataset_id,
        },
        "caseLevelData": case_level_data,
    }
    frequencies = map_frequency(info)
    if frequencies:
        record["frequencyInPopulations"] = frequencies
    record["identifiers"] = identifiers
    record["molecularAttributes"] = molecular_attributes
    record["_position"] = {
        "assemblyId": genome,
        "start": [start],
        "end": [position],
        "startInteger": start,
        "endInteger": position,
        "refseqId": CHROMOSOME_NAMES.get(variant["CHROM"], ""),
    }
    record["variantInternalId"] = uid
    variant_level = map_variant_level_data(info, annotated_with)
    if variant_level:
        record["variantLevelData"] = variant_level
    record["variation"] = {
        "referenceBases": variant["REF"],
        "alternateBases": variant["ALT"],
        "variantType": info["VT"],
        "location": {
            "sequence_id": f"HGVSid:{identifiers['genomicHGVSId']}",
            "type": "SequenceLocation",
            "interval": {
                "type": "SequenceInterval",
                "start": {"type": "Number", "value": start},
                "end": {"type": "Number", "value": position},
            },
        },
    }
    record["variantQuality"] = {
        "QUAL": None if variant["QUAL"] == "." else perl_number(variant["QUAL"]),
        "FILTER": None if variant["FILTER"] == "." else variant["FILTER"],
    }
    return record


def open_vcf(path: Path) -> TextIO:
    if path.suffix == ".gz":
        if _igzip is not None:
            return _igzip.open(path, "rt", encoding="utf-8")
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def open_bff_output(path: Path) -> BinaryIO:
    if _igzip is not None:
        return _igzip.open(path, "wb", compresslevel=ISAL_COMPRESSLEVEL)
    return gzip.open(path, "wb", compresslevel=STDLIB_COMPRESSLEVEL)


def json_record_encoder():
    if _orjson is not None:
        return _orjson.dumps
    encoder = json.JSONEncoder(ensure_ascii=True, separators=(",", ":")).encode
    return lambda value: encoder(value).encode("ascii")


def iter_bff_records(
    input_path: Path,
    *,
    genome: str,
    dataset_id: str,
    provenance: dict[str, Any],
    verbose: bool = False,
) -> Iterator[dict[str, Any]]:
    ann_fields: list[str] = []
    ann_positions: tuple[int, int, int, int] | None = None
    sample_ids: list[str] = []
    annotated_with = annotation_metadata(genome)
    source_records = 0
    with open_vcf(input_path) as handle:
        for line in handle:
            if line.startswith("##INFO=<ID=ANN,Number"):
                ann_fields = parse_ann_header(line)
                ann_positions = molecular_annotation_positions(ann_fields)
                continue
            if line.startswith("#CHROM") or line.startswith("#CHR"):
                sample_ids = line.rstrip("\n").split("\t")[9:]
                continue
            if line.startswith("#"):
                continue

            source_records += 1
            fields = line.rstrip("\n").split("\t", 9)
            if len(fields) < 8:
                raise ConversionError(f"VCF record {source_records} has fewer than 8 columns")
            variant = {
                "CHROM": fields[0],
                "POS": fields[1],
                "REF": fields[3],
                "ALT": fields[4],
                "QUAL": fields[5],
                "FILTER": fields[6],
            }
            if not ann_fields or ann_positions is None:
                raise ConversionError(
                    "VCF has no usable SnpEff ANN header; rerun bff-tools with "
                    "--annotate or provide a compatibly annotated VCF"
                )
            if variant["ALT"].startswith("<"):
                continue
            uid = f"chr{variant['CHROM']}_{variant['POS']}_{variant['REF']}_{variant['ALT']}"
            info = parse_info_field(fields[7], uid)
            if "VT" not in info or "," in info["VT"]:
                info["VT"] = "SNP" if len(variant["REF"]) == len(variant["ALT"]) else "INDEL"
            if "ANN" not in info:
                print(f"[vcf2bff] WARNING: Skipping <{uid}> - no INFO=<ID=ANN>", file=sys.stderr)
                continue
            molecular_attributes = parse_molecular_attributes(
                info["ANN"], ann_positions, variant["ALT"]
            )
            format_value = fields[8] if len(fields) > 8 else ""
            genotype_values = fields[9] if len(fields) > 9 else ""
            case_level_data = map_case_level_data(
                genotype_values, sample_ids, format_value
            )
            yield map_record(
                variant,
                info,
                molecular_attributes,
                case_level_data,
                uid,
                genome=genome,
                dataset_id=dataset_id,
                provenance=provenance,
                annotated_with=annotated_with,
            )
            if verbose and source_records % 10_000 == 0:
                print(f"Info: Variants processed = {source_records}")


def convert_vcf(
    input_path: Path,
    output_dir: Path,
    *,
    genome: str,
    dataset_id: str,
    project_dir: str,
    threads: int,
    verbose: bool = False,
) -> tuple[Path, int]:
    output_path = output_dir / OUTPUT_NAME
    user = os.environ.get("LOGNAME") or os.environ.get("USER") or "unknown"
    provenance = {
        "user": user,
        "hostname": socket.gethostname(),
        "cwd": os.getcwd(),
        "projectDir": project_dir,
        "version": VERSION,
        "threadshost": threads,
        "filein": str(input_path),
        "fileout": str(output_path),
    }
    records = 0
    encode_record = json_record_encoder()
    with open_bff_output(output_path) as output:
        output.write(b"[\n")
        for record in iter_bff_records(
            input_path,
            genome=genome,
            dataset_id=dataset_id,
            provenance=provenance,
            verbose=verbose,
        ):
            if records:
                output.write(b",\n")
            output.write(encode_record(record))
            records += 1
        output.write(b"\n]\n")
    return output_path, records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an annotated VCF to Beacon v2 BFF genomic variations"
    )
    parser.add_argument("--input", "-i", type=Path, required=True)
    parser.add_argument("--dataset-id", "-d", required=True)
    parser.add_argument("--project-dir", "-p", required=True)
    parser.add_argument("--genome", "-g", choices=("hg19", "hg38", "hs37"), required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    parser.add_argument("--threads", "-t", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--verbose", "-verbose", action="store_true")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s Version {VERSION}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.input.is_file():
        parser.error(f"Input VCF does not exist: {args.input}")
    if not args.out_dir.is_dir():
        parser.error(f"Output directory does not exist: {args.out_dir}")
    if args.threads < 1:
        parser.error("--threads must be a positive integer")
    try:
        output_path, records = convert_vcf(
            args.input,
            args.out_dir,
            genome=args.genome,
            dataset_id=args.dataset_id,
            project_dir=args.project_dir,
            threads=args.threads,
            verbose=args.verbose,
        )
    except (OSError, ConversionError, KeyError, ValueError) as exc:
        parser.exit(1, f"vcf2bff: {exc}\n")
    if args.verbose:
        print(f"Info: Wrote {records} variants to {output_path}")
        print("Info: vcf2bff finished OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

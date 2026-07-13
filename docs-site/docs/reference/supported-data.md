---
title: Supported Data
---

| Input | Command | Output | External resources |
|---|---|---|---|
| Beacon metadata workbook (`.xlsx`) | `bff-tools validate` | One BFF JSON file per worksheet | None |
| BFF collection files (`.json`) | `bff-tools validate` | Validation report | None |
| Streamed genomic variations (`.json` or `.json.gz`) | `bff-tools validate --gv-vcf` | Validation report | None |
| Raw VCF (`.vcf`, `.vcf.gz`) | `bff-tools vcf` | Annotated intermediates and BFF genomic variations | Full annotation profile |
| VCF with compatible SnpEff ANN data | `bff-tools vcf --no-annotate` | `genomicVariationsVcf.json.gz` | None |
| SNP-array TSV/TXT | `bff-tools tsv` | VCF intermediate, annotated intermediates, and BFF genomic variations | Full annotation profile |

## Metadata Collections

The packaged workbook and schemas cover:

- `analyses`
- `biosamples`
- `cohorts`
- `datasets`
- `individuals`
- `runs`
- `genomicVariations` when `--gv` is explicitly selected

JSON filenames must match their collection names. Gzipped, one-record-per-line genomic output may retain the generated name `genomicVariationsVcf.json.gz` when `--gv-vcf` is used.

## Assemblies

The conversion CLI accepts `hg19`, `hg38`, `hs37`, and `b37`. `b37` is treated as the `hs37` profile. Assembly labels do not automatically rename contigs or lift coordinates; the VCF and configured FASTA must already agree.

## Variant Content

The production converter handles SNVs, small insertions/deletions, multisample genotypes, and annotation fields used by the existing SnpEff/SnpSift workflow. Fully annotated regression fixtures cover ANN, dbNSFP, ClinVar, COSMIC, missing genotypes, homozygous alternate calls, indels, and 2,504-sample records.

VCF records must have a compatible SnpEff ANN header. Raw VCF and all TSV input therefore use annotation by default. Records within an otherwise annotated VCF that lack `INFO/ANN` are skipped with a warning.

The converter does not filter SNVs or nucleotide indels because `FILTER` is non-PASS or `QUAL` is low. It preserves `FILTER`, `QUAL`, per-sample depth, and assembly metadata for downstream review.

Symbolic and structural alleles remain limited and are currently skipped. The regression fixture records current behavior for symbolic copy-number alleles so future converter changes are deliberate and testable.

gVCF reference blocks are not accepted as ordinary variants. Genotype or convert a gVCF to a standard variant VCF before running annotation.

## Samples and Coordinates

Single-sample and multi-sample VCFs are supported. Sample names become `biosampleId` values in `caseLevelData`; they should match identifiers in the metadata collections.

Generated BFF intervals use 0-start, half-open coordinates. VCF `POS` is 1-based, so a single-base record at `POS` becomes `start = POS - 1` and `end = POS`.

## Standalone Report

`--browser` generates a single HTML file from genomic variation output. The table supports local search, sorting, column visibility, gene-panel filters, and pagination. No database or web service is required.

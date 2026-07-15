---
title: Validation and Trust
---

Schema validation is necessary, but it is not evidence that a dataset is biologically correct or clinically suitable.

## What Validation Establishes

With XLSX input, `bff-tools validate` first builds BFF JSON collections from the populated worksheets and writes each collection that passes validation. With JSON input, it validates existing collections without rewriting them. Both paths check every entity against the packaged dereferenced Beacon v2 schema and catch missing required properties, incompatible JSON types, malformed ontology structures, invalid enumerations, and other structural constraints.

The Python validator is regression-tested against all 10,018 records in the CINECA synthetic workbook. All six generated collections must match the versioned reference files byte-for-byte.

## Schema Versions

The package retains each dereferenced Beacon schema set under its specification version. `CURRENT` selects the one version used by default by `bff-tools validate`; archived versions remain available for reproducibility but are not maintained as additional active targets.

Every schema version includes a manifest with its source revision and SHA-256 checksums. The CINECA workbook and its generated BFF collections use the same version hierarchy, keeping each input/output pair together. Documentation uses `CINECA_synthetic_cohort_EUROPE_UK1/current/`, while top-level CINECA paths remain compatibility aliases to the same snapshot.

Use `--schema-dir` when an explicit archived or local dereferenced schema set is required:

```bash
bff-tools validate -i metadata.json \
  --schema-dir /path/to/schemas/v2.0.0
```

The current package supports Beacon schema `v2.0.0`.

## What Validation Does Not Establish

Validation does not prove that:

- identifiers refer to the intended individuals or samples;
- ontology terms are current or scientifically appropriate;
- sex labels, disease labels, and code labels match the newest ontology release;
- coordinates use the claimed assembly;
- annotation databases are current;
- a variant interpretation is clinically valid.

The serializer does not silently capitalize labels or replace ontology codes. For example, source labels such as `male` and `female` remain unchanged even when an ontology browser displays different capitalization.

## Workbook Semantics

Spreadsheet values are converted before JSON serialization:

- number-like strings become JSON numbers;
- `true` and `false` become JSON booleans;
- JSON-looking array/object values are decoded;
- empty cells are omitted;
- unknown properties are retained when allowed by the schema.

This numeric coercion is important because JSON serializers preserve stored types; a spreadsheet value intended as a number must not become a quoted JSON string.

## Schema Ambiguity

Beacon schemas can contain `oneOf` alternatives that overlap for a particular structure. A measurement object that satisfies more than one branch is invalid under `oneOf`, even if each branch is independently sensible. Resolve the structure in the source workbook rather than suppressing the issue.

Use `--ignore-validation` only to inspect generated JSON during correction. A successful write under that option is not a validation pass.

## Variant Regression Coverage

Normal CI compares the Python converter with the versioned, fully annotated 1000 Genomes reference output. The developer command `bff-tools test` starts from the compact raw GRCh37 fixture and exercises normalization, every annotation stage, conversion, schema validation, and semantic comparison across all 1,044 emitted records.

The separate CINECA chromosome 22 release run additionally covers 2,504 samples and:

- SnpEff ANN impacts and multiple transcripts;
- dense dbNSFP values;
- ClinVar and pathogenic ClinVar records;
- COSMIC annotations;
- SNVs, nucleotide indels, and symbolic copy-number alleles;
- missing and homozygous-alternate genotypes.

The complete external chr22 source contains 1,103,547 raw records, which become 1,110,240 records after normalization, and remains the final scalability and parity gate. It is read from external storage and is not stored in Git.

### Full CINECA Release Fixture

Maintainers can download the release-scale files from the public Google Drive folder [`beacon2-cbi-tools-data/CINECA_synthetic_cohort_EUROPE_UK1/vcf/`](https://drive.google.com/drive/folders/1_B30lOZKndJQZPW4Wza3ho-xGsekH4fM):

- `chr22.Test.1000G.phase3.joint.vcf.gz`: raw GRCh37/hs37d5 chromosome 22 input using contig `22`;
- `chr22.Test.1000G.phase3.joint.vcf.gz.tbi`: tabix index;
- `genomicVariationsVcf.json.gz`: versioned BFF reference output.

These are developer and release-validation assets. They are not included in the repository or annotation bundle archive, and `bff-tools install-resources` does not download them. The `bff-tools test` command continues to use its separate compact GRCh37 fixture.

## Release Checklist

Before handing data to a Beacon deployment, retain and review:

| Evidence | Check |
|---|---|
| Source checksums | Inputs are exactly the files that were approved |
| Schema result | Every collection exits successfully without ignored issues |
| Assembly | Genome label, contigs, FASTA, and coordinates agree |
| Counts | Samples, variants, and metadata entities match expectations |
| Spot checks | Representative genotypes and annotations match the source VCF |
| Resource versions | SnpEff, dbNSFP, ClinVar, COSMIC, and FASTA versions are recorded |
| Run provenance | Parameter YAML, configuration, `log.json`, and stage logs are retained |
| Privacy review | Outputs and logs contain no unintended identifying information |

VCF migration acceptance requires equal BFF data after removing run-specific provenance and normalizing only two explicitly order-insensitive arrays. No biological or schema field is excluded.

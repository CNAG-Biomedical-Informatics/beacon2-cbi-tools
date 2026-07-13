---
title: Validation and Trust
---

Schema validation is necessary, but it is not evidence that a dataset is biologically correct or clinically suitable.

## What Validation Establishes

`bff-tools validate` checks every entity against the packaged dereferenced Beacon v2 schema. It catches missing required properties, incompatible JSON types, malformed ontology structures, invalid enumerations, and other structural constraints.

The Python validator is regression-tested against all 10,018 records in the CINECA synthetic workbook. All six generated collections must match the Perl-generated reference files byte-for-byte.

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

Normal CI compares the Python converter with the existing Perl-generated, fully annotated 1000 Genomes output. The local CINECA acceptance run additionally covers 2,504 samples and:

- SnpEff ANN impacts and multiple transcripts;
- dense dbNSFP values;
- ClinVar and pathogenic ClinVar records;
- COSMIC annotations;
- SNVs, nucleotide indels, and symbolic copy-number alleles;
- missing and homozygous-alternate genotypes.

The complete external chr22 source contains 1,110,240 records and remains the final scalability and parity gate. It is read from external storage and is not stored in Git.

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

VCF migration acceptance requires equal BFF data after removing run-specific provenance and normalizing only the two arrays whose order varied between Perl hash seeds. No biological or schema field is excluded.

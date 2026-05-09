---
title: Validation and Reproducibility
---

# Validation and Reproducibility

`beacon2-cbi-tools` helps create Beacon v2-compatible data, but validation has a specific scope. Schema-valid output means the files match expected Beacon structures. It does not mean the input data are biologically complete, clinically interpreted, or suitable for medical decisions.

:::warning[Research use]
Generated annotations and outputs are intended for research and data preparation workflows. Do not use them for diagnosis, treatment, or other medical decisions.
:::

## What Validation Checks

`bff-tools validate` checks metadata workbooks or BFF JSON collections against Beacon v2 model expectations.

It helps detect:

- missing required fields
- values with the wrong type or shape
- identifiers that do not match expected patterns
- malformed nested objects or arrays
- collections that cannot be written as valid BFF JSON

## What Validation Does Not Check

Validation does not prove that:

- an ontology term is the best biological description of a subject
- phenotypic or clinical metadata are complete
- sample identifiers are correct across all source systems
- the VCF was generated with the declared reference genome
- genomic annotations are clinically meaningful
- MongoDB contains the dataset you intended to publish

Treat validation as a structural and reproducibility check, then review the scientific content separately.

## Reference Genome Sensitivity

The genomic workflow depends on the configured reference build. Keep these aligned:

| Setting or file | Must match |
|---|---|
| `genome` in `param.yaml` | VCF reference build and contig naming |
| local external reference data | selected genome and annotation workflow |
| input VCF or TSV | expected coordinate system |
| downstream Beacon deployment | loaded BFF collections |

Common labels include `hg19`, `hg38`, `hs37`, and `b37`. A mismatch can produce failed annotation, empty output, or misleading genomic variation records.

## Reproducibility Checklist

Keep enough context to rerun or audit a conversion later:

- `beacon2-cbi-tools` version or Git commit
- Docker image tag or Apptainer image digest when using containers
- command line used for the run
- `param.yaml`
- `bin/config.yaml` or deployment-specific config
- input metadata workbook or BFF JSON collections
- input VCF, VCF.gz, TSV, or TXT file checksums
- external reference data version or download date
- generated `log.json`
- stage-specific `*.log` files

## Reviewing a Run

Start with the generated run directory:

```text
beacon_*/
```

Then inspect:

| File or directory | Why it matters |
|---|---|
| `log.json` | resolved command, input paths, parameters, and runtime context |
| `vcf/run_vcf2bff.log` | VCF normalization, annotation, and BFF conversion details |
| `tsv/run_tsv2vcf.log` | SNP-array conversion details |
| `mongodb/run_bff2mongodb.log` | import and indexing status |
| metadata JSON collections | final Beacon entity payloads |

## Review by Command

| Command | Review before sharing |
|---|---|
| `validate` | generated entity files, validation messages, missing required fields, unexpected warnings |
| `vcf` | `genome` setting, VCF build, final `genomicVariationsVcf.json.gz`, VCF conversion logs |
| `tsv` | TSV format assumptions, generated VCF-like intermediates, final genomic variation output |
| `load` | MongoDB URI, target database, imported collection counts, load logs |
| `full` | all conversion and loading checks, because this mode combines multiple stages |

## Expected Warnings

Some schema warnings can reflect model ambiguity rather than a broken input file. For example, `oneOf` warnings may appear when a value matches more than one schema branch.

Do not ignore warnings automatically. Use them to decide whether the generated JSON has the structure you expect, then rerun validation after correcting the source data when needed.

## Practical Policy

- Use containers when you need reproducible installation state.
- Use explicit project directory names for runs you plan to cite or share.
- Keep input and output checksums for published datasets.
- Review a small subset of records manually before processing a large cohort.
- Load into MongoDB only after metadata and genomic variation files look correct.

## Ready to Share Checklist

Before sharing a dataset, publication supplement, or Beacon deployment, confirm that:

- the tool version or container image is recorded
- input file checksums are recorded
- `param.yaml` and runtime config are archived
- `log.json` and stage logs are preserved
- metadata JSON collections pass validation
- the reference genome label matches the input files
- a small sample of records has been reviewed manually
- MongoDB collection counts match the files you intended to load

For common failure modes, see [Troubleshooting](../troubleshooting/index.md).

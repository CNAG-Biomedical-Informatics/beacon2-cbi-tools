---
title: Supported Inputs and Outputs
---

# Supported Inputs and Outputs

Use this page to check whether your data fits one of the supported `bff-tools` workflows.

## Main Data Paths

| Starting data | Command | Main output | Notes |
|---|---|---|---|
| Beacon metadata workbook (`.xlsx`) | `bff-tools validate` | BFF JSON collections | Use the Beacon v2 workbook template for `individuals`, `biosamples`, `runs`, `datasets`, and related entities. |
| Existing BFF JSON metadata | `bff-tools validate` | validated BFF JSON collections | Useful when metadata was produced outside the workbook template. |
| VCF or VCF.gz | `bff-tools vcf` | BFF `genomicVariations` | The `genome` setting must match the input reference build and configured annotation resources. |
| SNP-array TSV or TXT | `bff-tools tsv` | VCF-like intermediates and BFF `genomicVariations` | Intended for SNP-array style data such as direct-to-consumer genotype exports. |
| BFF JSON collections | `bff-tools load` | MongoDB collections | Requires MongoDB and valid paths for `mongoimport` and `mongosh`. |
| Metadata plus VCF or TSV input | `bff-tools full` | BFF output plus MongoDB load | Convenience mode when configuration already points to the metadata collections. |

## Metadata Entities

Metadata validation can produce the standard Beacon v2 entity collections used by the toolkit:

```text
analyses.json
biosamples.json
cohorts.json
datasets.json
individuals.json
runs.json
```

The exact files depend on the sheets or JSON collections present in the input.

## Genomic Variation Output

VCF and TSV workflows generate genomic variation data in BFF form. The most common final output is:

```text
genomicVariationsVcf.json.gz
```

The output is normally written inside a run-specific project directory, for example:

```text
beacon_*/vcf/genomicVariationsVcf.json.gz
```

## Optional Inspection Paths

| Need | Tool or option | Output |
|---|---|---|
| Browse static BFF files without MongoDB | `bff2html: true` or `bff-browser` | local browser-oriented files |
| Query BFF collections loaded in MongoDB | `bff-portal` | lightweight API and web interface |
| Queue many local ingestion jobs | `bff-queue` | local job queue and status tracking |

## Current Limits

- The genomic workflow is aimed at DNA sequencing VCFs and SNP-array style TSV input.
- Structural variants and copy-number variation support are limited.
- Biological interpretation remains the user's responsibility; schema-valid output is not the same as clinically validated output.
- Reference genome labels such as `hg19`, `hg38`, `hs37`, and `b37` must be aligned with the input file and local reference data.

For copy-paste commands, continue to [Command Recipes](../workflows/recipes.md).

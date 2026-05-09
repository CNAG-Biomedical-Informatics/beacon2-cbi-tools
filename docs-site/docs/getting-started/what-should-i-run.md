---
title: What Should I Run?
---

# What Should I Run?

Use this page to choose the right `bff-tools` mode from your starting point. It is a decision page, not a tutorial.

If you want to run the bundled test data now, go to [Quick Start](quick-start.md). If you already know the mode and want copy-paste commands, use [Command Recipes](../workflows/recipes.md).

## Decision Table

| I have... | I want... | Run |
|---|---|---|
| XLSX metadata | Validate Beacon metadata and write BFF JSON collections | `bff-tools validate` |
| BFF JSON metadata | Validate existing JSON collections | `bff-tools validate` |
| A VCF or VCF.gz file | Generate BFF `genomicVariations` | `bff-tools vcf` |
| A SNP-array TSV/TXT file | Convert SNP-array data into BFF `genomicVariations` | `bff-tools tsv` |
| Existing BFF files | Load them into MongoDB | `bff-tools load` |
| Metadata plus VCF/TSV input | Convert genomic data and load everything into MongoDB | `bff-tools full` |
| Generated BFF output | Inspect it without MongoDB | `bff-browser` |
| BFF data already in MongoDB | Query it with a small web/API layer | `bff-portal` |
| Many repeated jobs | Queue and monitor them locally | `bff-queue` |

## How to Decide

### Start with `validate` when

- your first input is a Beacon metadata workbook
- you want to check existing BFF JSON metadata
- you need `individuals.json`, `biosamples.json`, `runs.json`, or `datasets.json` before loading

### Start with `vcf` or `tsv` when

- your first input is genomic data
- you only need to generate `genomicVariations`
- MongoDB loading can wait until after you inspect the output

Use `vcf` for VCF or VCF.gz. Use `tsv` for SNP-array style TSV or TXT input.

### Start with `load` when

- BFF metadata collections already exist
- genomic variation output already exists, if your Beacon includes genomic data
- MongoDB is configured and reachable

### Use `full` when

- you already have a working parameter file
- metadata paths are configured
- MongoDB settings are configured
- you want conversion and loading in one run

For a first real dataset, running `validate`, then `vcf` or `tsv`, then `load` is easier to debug than starting with `full`.

## Avoid These Mixups

| Situation | Better choice |
|---|---|
| You have not tested the install yet | Run [Quick Start](quick-start.md) first |
| You only want to see command syntax | Use [Command Recipes](../workflows/recipes.md) |
| You need file and log locations | Read [Outputs](../reference/outputs.md) |
| You are reviewing a dataset for sharing | Read [Validation and Reproducibility](../reference/validation-and-reproducibility.md) |
| You need the complete workflow explanation | Read [Data Beaconization](../workflows/data-beaconization) |

## Next Step

If you are new to the toolkit, run the [Quick Start](quick-start.md) first. If you already know your mode, continue to [Command Recipes](../workflows/recipes.md), the [CLI reference](../reference/cli.md), or the [data beaconization workflow](../workflows/data-beaconization).

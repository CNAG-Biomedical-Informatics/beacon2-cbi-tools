---
title: What Should I Run?
---

# What Should I Run?

Use this page to choose the right `bff-tools` mode from your starting point.

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

## Common Starting Points

### I only want to validate metadata

```bash
bin/bff-tools validate -i metadata.xlsx --out-dir bff_out
```

Expected output: BFF JSON collections such as `individuals.json`, `biosamples.json`, `runs.json`, and `datasets.json`.

### I have a VCF

```bash
bin/bff-tools vcf -i input.vcf.gz -p param.yaml
```

Expected output: a run directory containing BFF genomic variation output, usually under `beacon_*/vcf/`.

### I have SNP-array data

```bash
bin/bff-tools tsv -i input.txt.gz -p param.yaml
```

Expected output: a run directory containing converted VCF-like intermediates and BFF genomic variation output.

### I already have BFF files

```bash
bin/bff-tools load -p param.yaml
```

Expected output: BFF collections imported into MongoDB.

### I want conversion plus loading

```bash
bin/bff-tools full -i input.vcf.gz -p param.yaml
```

Expected output: genomic conversion output plus MongoDB import output in one run.

## Next Step

If you are new to the toolkit, run the [Quick Start](quick-start.md) first. If you already know your mode, continue to the [CLI reference](../reference/cli.md) or the [data beaconization workflow](../workflows/data-beaconization.md).

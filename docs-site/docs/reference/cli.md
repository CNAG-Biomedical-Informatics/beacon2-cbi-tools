---
title: CLI Reference
---

# CLI Reference

The main entry point is `bin/bff-tools`.

```bash
bin/bff-tools --help
```

Most users only need one mode at a time. Start from the data you already have, then choose the matching command.

## Modes

| Mode | Use when | Main output |
|---|---|---|
| `validate` | You have XLSX metadata or existing BFF JSON collections | BFF JSON metadata collections |
| `vcf` | You have VCF or VCF.gz genomic input | BFF `genomicVariations` |
| `tsv` | You have SNP-array TSV or TXT input | VCF-like intermediates and BFF `genomicVariations` |
| `load` | You already have BFF files and want MongoDB collections | imported MongoDB collections |
| `full` | You want genomic conversion plus MongoDB loading in one run | BFF output and imported MongoDB collections |

## Command Model

Most commands follow this shape:

```bash
bin/bff-tools <mode> -i <input> -p <param.yaml> [options]
```

`validate` is the exception because it can validate metadata without a genomic parameter file:

```bash
bin/bff-tools validate -i metadata.xlsx --out-dir bff_out
```

## Common Commands

### Validate Metadata

```bash
bin/bff-tools validate -i metadata.xlsx --out-dir bff_out
```

Use this before genomic conversion or MongoDB loading. It catches structural metadata problems early and writes BFF entity collections.

### Convert VCF

```bash
bin/bff-tools vcf -t 4 -i input.vcf.gz -p param.yaml
```

Use this for sequencing VCFs. The `genome` value in `param.yaml` must match the input reference build.

### Convert SNP-array TSV

```bash
bin/bff-tools tsv -i input.txt.gz -p param.yaml
```

Use this for SNP-array style files. This mode creates VCF-like intermediates before generating BFF genomic variation output.

### Load BFF Collections

```bash
bin/bff-tools load -p param.yaml
```

Use this after metadata and genomic variation files exist. The parameter file must point to the BFF collections and MongoDB configuration.

### Convert and Load

```bash
bin/bff-tools full -t 4 -i input.vcf.gz -p param.yaml
```

Use this when the parameter file already points to the metadata collections and MongoDB settings.

## Options You Will Use Often

| Option | Applies to | Purpose |
|---|---|---|
| `-i FILE` | `validate`, `vcf`, `tsv`, `full` | input workbook, VCF, TSV, or genomic file |
| `-p FILE` | `vcf`, `tsv`, `load`, `full` | runtime parameter file |
| `-t N` | `vcf`, `full` | number of threads for supported stages |
| `--out-dir DIR` | `validate` | metadata validation output directory |
| `--projectdir-override DIR` | `vcf`, `tsv`, `load`, `full` | explicit run directory name |
| `--ignore-validation` | `validate` | write generated JSON for inspection even when validation is noisy |

## Parameter File Essentials

Minimal VCF or TSV conversion:

```yaml
genome: hg38
```

Generate static browser output as part of the run:

```yaml
genome: hg38
bff2html: true
```

Load BFF files into MongoDB:

```yaml
bff:
  metadatadir: bff_out
  runs: runs.json
  cohorts: cohorts.json
  biosamples: biosamples.json
  individuals: individuals.json
  analyses: analyses.json
  datasets: datasets.json
  genomicVariationsVcf: beacon_my_project/vcf/genomicVariationsVcf.json.gz
```

## Choosing the Wrong Mode

| If you have... | Do not start with | Use |
|---|---|---|
| only metadata | `vcf` or `full` | `validate` |
| only a VCF and no metadata paths configured | `load` | `vcf` first |
| existing BFF collections | `validate` only | `load` after validating if needed |
| a failed conversion directory | rerunning into the same directory | a new `--projectdir-override` value |

For copy-paste workflows, see [Command Recipes](../workflows/recipes.md). For an end-to-end explanation, see [Data Beaconization](../workflows/data-beaconization).

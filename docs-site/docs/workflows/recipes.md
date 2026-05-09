---
title: Command Recipes
---

# Command Recipes

These short recipes cover common `beacon2-cbi-tools` tasks. Replace file names and directories with paths from your own installation.

:::tip[Start with bundled data]
If this is your first run, use the [Quick Start](../getting-started/quick-start.md) before adapting commands to real data.
:::

## Validate Metadata

Validate an XLSX workbook and write BFF JSON collections:

```bash
bin/bff-tools validate -i metadata.xlsx --out-dir bff_out
```

Validate existing BFF JSON collections:

```bash
bin/bff-tools validate -i bff_out --out-dir validated_bff
```

## Convert VCF to BFF

Run VCF conversion with four threads:

```bash
bin/bff-tools vcf -t 4 -i input.vcf.gz -p param.yaml
```

Use a deterministic project directory name:

```bash
bin/bff-tools vcf -t 4 -i input.vcf.gz -p param.yaml --projectdir-override beacon_my_project
```

Minimal `param.yaml`:

```yaml
genome: hg38
```

Enable static browser output:

```yaml
genome: hg38
bff2html: true
```

## Convert SNP-array TSV to BFF

Run SNP-array TSV conversion:

```bash
bin/bff-tools tsv -i input.txt.gz -p param.yaml
```

This mode writes TSV-specific intermediates and then continues through the VCF-style genomic variation path.

## Load BFF Collections into MongoDB

Point the parameter file to metadata and genomic variation files:

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

Then load:

```bash
bin/bff-tools load -p param.yaml
```

## Convert and Load in One Step

Use `full` when metadata paths and MongoDB settings are already configured:

```bash
bin/bff-tools full -t 4 -i input.vcf.gz -p param.yaml
```

## Inspect Output

Open the run context first:

```bash
less beacon_my_project/log.json
```

Check the VCF conversion log:

```bash
less beacon_my_project/vcf/run_vcf2bff.log
```

If browser output was enabled, inspect the static output under:

```text
beacon_my_project/browser/
```

## Optional Utilities

Browse static BFF files without MongoDB:

```bash
bff-browser
```

Query BFF collections already loaded in MongoDB:

```bash
bff-portal
```

Queue many local jobs:

```bash
bff-queue
```

For mode details and expected outputs, see [CLI Reference](../reference/cli.md) and [Outputs](../reference/outputs.md).

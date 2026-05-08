---
title: Overview
---

# Beacon v2 CBI Tools Documentation

`beacon2-cbi-tools` helps you prepare data for Beacon v2 deployments based on the Beacon Friendly Format (BFF).

With this toolkit you can:

- validate metadata from XLSX or JSON files against Beacon v2 schemas
- convert VCF or SNP-array TSV input into BFF `genomicVariations`
- load BFF collections into MongoDB
- optionally inspect the resulting data with lightweight utilities

:::warning[Research-use disclaimer]
This toolkit is intended for research use. Do not use generated annotations or results for medical decisions.
:::

## Typical Workflow

Most users follow this sequence:

1. Prepare and validate metadata with `bff-tools validate`.
2. Convert genomic data with `bff-tools vcf` or `bff-tools tsv`.
3. Load the generated BFF collections into MongoDB with `bff-tools load` or `bff-tools full`.

## Recommended Path

If you are new to the toolkit, use this order:

1. Read the [installation overview](getting-started/installation.md) and pick Docker unless your environment requires Apptainer or a direct install.
2. Use [What should I run?](getting-started/what-should-i-run.md) to choose the right command for your input.
3. Run the [Quick Start](getting-started/quick-start.md) with the bundled test data.
4. Read the [data beaconization tutorial](workflows/data-beaconization.md) before adapting the workflow to your own data.
5. Check [Outputs](reference/outputs.md) when you need to understand generated files and logs.
6. Keep the [FAQ](troubleshooting/faq.md) open while configuring reference genomes, annotation resources, and MongoDB loading.

## What You Need Before Starting

| Requirement | Why it matters |
|---|---|
| Metadata in XLSX or BFF JSON | Required for Beacon entities such as `individuals`, `biosamples`, `runs`, and `datasets` |
| VCF, VCF.gz, or SNP-array TSV input | Used to generate BFF `genomicVariations` |
| Reference genome choice | Must match your genomic input, for example `hg19`, `hg38`, `hs37`, or `b37` |
| External reference data | Required by the genomic conversion workflow |
| MongoDB | Required only when you want to load and query BFF collections |

## Choose Your Path

### I want to install the toolkit

- [Installation overview](getting-started/installation.md)
- [Docker installation](getting-started/docker)
- [Apptainer installation](getting-started/apptainer)
- [Non-containerized installation](getting-started/non-containerized)

### I want the fastest way to try it

- [What should I run?](getting-started/what-should-i-run.md)
- [Quick Start](getting-started/quick-start.md)

### I want the full end-to-end explanation

- [Tutorial: data beaconization](workflows/data-beaconization.md)

### I want to understand how it is implemented

- [Implementation overview](implementation/overview.md)

### I want examples or troubleshooting help

- [GRCh38 / hg38 example](examples/hg38)
- [Outputs reference](reference/outputs.md)
- [Troubleshooting index](troubleshooting/index.md)
- [FAQ](troubleshooting/faq.md)

## Main Commands

The main entry point is `bff-tools`.

- `bff-tools validate`: validate metadata and write BFF JSON collections
- `bff-tools vcf`: convert a VCF or VCF.gz file into BFF
- `bff-tools tsv`: convert a SNP-array TSV file into BFF
- `bff-tools load`: load BFF collections into MongoDB
- `bff-tools full`: run conversion plus loading in one step

## Utilities

The toolkit also includes optional utilities for browsing or queueing jobs:

- `bff-browser`: browse static BFF files without a database
- `bff-portal`: query BFF data stored in MongoDB
- `bff-queue`: run and monitor many ingestion jobs on a workstation

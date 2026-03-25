# Beacon v2 CBI Tools Documentation

<div align="center">
    <a href="https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools">
        <img src="https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/docs/img/logo.png" width="140" alt="beacon2-cbi-tools">
    </a>
</div>

`beacon2-cbi-tools` helps you prepare data for Beacon v2 deployments based on the Beacon Friendly Format (BFF).

With this toolkit you can:

- validate metadata from XLSX or JSON files against Beacon v2 schemas
- convert VCF or SNP-array TSV input into BFF `genomicVariations`
- load BFF collections into MongoDB
- optionally inspect the resulting data with lightweight utilities

--8<-- "about/disclaimer.md"

## Typical workflow

Most users follow this sequence:

1. Prepare and validate metadata with `bff-tools validate`.
2. Convert genomic data with `bff-tools vcf` or `bff-tools tsv`.
3. Load the generated BFF collections into MongoDB with `bff-tools load` or `bff-tools full`.

## Choose your path

### I want to install the toolkit

- [Docker installation](download-and-installation/docker-based.md)
- [Apptainer installation](download-and-installation/apptainer-based.md)
- [Non-containerized installation](download-and-installation/non-containerized.md)

### I want the fastest way to try it

- [Quick Start](quick-start.md)

### I want the full end-to-end explanation

- [Tutorial: data beaconization](data-beaconization.md)

### I want examples or troubleshooting help

- [Examples](examples/hg38.md)
- [FAQ](help/faq.md)

## Main commands

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

## Project background

This project was originally developed as part of the Beacon v2 Reference Implementation and is now maintained as `beacon2-cbi-tools` by CNAG Biomedical Informatics.

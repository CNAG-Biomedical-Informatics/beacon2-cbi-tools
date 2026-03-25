
<div align="center">
    <a href="https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools">
        <img src="https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/docs/img/logo.png" width="200" alt="beacon2-cbi-tools">
    </a>
</div>

<div align="center" style="font-family: Consolas, monospace;">
    <h1>beacon2-cbi-tools</h1>
</div>

[![Docker build](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/docker-build-multi-arch.yml/badge.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/docker-build-multi-arch.yml)
[![Documentation Status](https://github.com/cnag-biomedical-informatics/beacon2-cbi-tools/actions/workflows/documentation.yml/badge.svg)](https://github.com/cnag-biomedical-informatics/beacon2-cbi-tools/actions/workflows/documentation.yml)
![Maintenance status](https://img.shields.io/badge/maintenance-actively--developed-brightgreen.svg)
[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![version](https://img.shields.io/badge/version-2.0.12-blue)

**beacon2-cbi-tools** is a toolkit for preparing Beacon v2 data around the Beacon Friendly Format (BFF). It helps you validate metadata, convert VCF or SNP-array TSV files into `genomicVariations`, and load BFF collections into MongoDB.

> Formerly known as **beacon2-ri-tools**.

## Quick links

- Documentation: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools>
- Docker image: <https://hub.docker.com/r/manuelrueda/beacon2-cbi-tools/tags>
- Disclaimer: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/about/disclaimer/>
- Docker install: [docker/README.md](docker/README.md)
- Apptainer install: [apptainer/README.md](apptainer/README.md)
- Non-containerized install: [non-containerized/README.md](non-containerized/README.md)

## What it does

- Validate XLSX or JSON metadata against Beacon v2 schemas.
- Convert VCF.gz or SNP-array TSV files into BFF `genomicVariations`.
- Load BFF metadata and genomic variation collections into MongoDB.

The resulting BFF collections can be used by Beacon v2 implementations that operate on MongoDB.

## Main command

The main entry point is [`bin/bff-tools`](bin/README.md). It provides five modes:

- `vcf`: convert a VCF file into BFF.
- `tsv`: convert a SNP-array TSV file into BFF.
- `validate`: validate metadata and serialize it into BFF JSON collections.
- `load`: load BFF collections into MongoDB.
- `full`: run conversion plus loading in one step.

## Utilities

Additional tools live in [utils/README.md](utils/README.md):

- `bff-browser`: browse static BFF files in a lightweight web UI.
- `bff-portal`: query BFF data stored in MongoDB through a small API and UI.
- `bff-queue`: run and monitor batch jobs on a workstation.

## Example workflow

1. Prepare metadata as XLSX or JSON and validate it with `bff-tools validate`.
2. Convert genomic data with `bff-tools vcf` or `bff-tools tsv`.
3. Load the generated BFF collections into MongoDB with `bff-tools load` or `bff-tools full`.

Sample metadata and synthetic test data are available in [CINECA_synthetic_cohort_EUROPE_UK1/README.md](CINECA_synthetic_cohort_EUROPE_UK1/README.md).

## Roadmap

Current work is focused on keeping the toolkit aligned with Beacon 2.x schema changes, improving `genomicVariations` support, and refreshing the synthetic cohort examples.

## Citation

If you use these tools in published work, please cite:

Rueda, M, Ariosa R. "Beacon v2 Reference Implementation: a toolkit to enable federated sharing of genomic and phenotypic data". _Bioinformatics_, btac568, <https://doi.org/10.1093/bioinformatics/btac568>

## Author

Written by Manuel Rueda, PhD. CNAG Biomedical Informatics: <https://www.cnag.eu>

## License

The software in this repository is copyrighted. See [LICENSE](LICENSE).


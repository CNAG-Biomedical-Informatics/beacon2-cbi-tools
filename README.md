<div align="center">
  <a href="https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools">
    <img src="https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/docs-site/static/img/logo.png" width="180" alt="BFF Tools">
  </a>
  <h1>BFF Tools</h1>
</div>

[![Tests](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/tests.yml/badge.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/CNAG-Biomedical-Informatics/beacon2-cbi-tools/badge.svg?branch=main)](https://coveralls.io/github/CNAG-Biomedical-Informatics/beacon2-cbi-tools?branch=main)
[![Docker build](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/docker-build-multi-arch.yml/badge.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/docker-build-multi-arch.yml)
[![Documentation](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/documentation.yml/badge.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/documentation.yml)
![Maintenance status](https://img.shields.io/badge/maintenance-actively--developed-brightgreen.svg)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/blob/main/LICENSE)
[![Docker pulls](https://badgen.net/docker/pulls/manuelrueda/beacon2-cbi-tools?icon=docker&label=current-image-pulls)](https://hub.docker.com/r/manuelrueda/beacon2-cbi-tools/)
[![Historical Docker pulls](https://badgen.net/docker/pulls/manuelrueda/beacon2-ri-tools?icon=docker&label=beacon2-ri-tools-historical-pulls)](https://hub.docker.com/r/manuelrueda/beacon2-ri-tools/)
[![Historical EGA Docker pulls](https://badgen.net/docker/pulls/beacon2ri/beacon_reference_implementation?icon=docker&label=EGA-RI-historical-pulls)](https://hub.docker.com/r/beacon2ri/beacon_reference_implementation/)
![Version](https://img.shields.io/badge/version-2.0.13--dev-blue)

**BFF Tools** prepares portable [Beacon Friendly Format (BFF)](https://docs.genomebeacons.org/models/) data for Beacon v2. It validates phenotypic and clinical metadata, converts VCF or SNP-array TSV input into BFF `genomicVariations`, and can generate a standalone browser report.

**BFF Tools** (`beacon2-cbi-tools`) is the actively developed continuation of the original `beacon2-ri-tools`, first developed at [EGA](https://ega-archive.org) and now maintained by its original developer at [CNAG Biomedical Informatics](https://www.cnag.eu). It is used by Beacon deployers and is independent of EGA's separate [`beacon2-ri-tools-v2`](https://github.com/EGA-archive/beacon2-ri-tools-v2) project.

The two historical image badges preserve the download record of earlier distributions; those images are deprecated for new installations.

## Quick links

- Documentation: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/>
- Installation choices: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/installation/>
- Quick start: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/quick-start/>
- End-to-end tutorial: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/workflows/data-beaconization/>
- Annotation data: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/annotation-data/>
- Outputs: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/reference/outputs/>
- MongoDB import: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/reference/mongodb/>
- Troubleshooting: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/troubleshooting/faq/>
- Docker image: <https://hub.docker.com/r/manuelrueda/beacon2-cbi-tools/tags>
- Disclaimer: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/about/disclaimer/>

## What it does

- Validates XLSX workbooks and BFF JSON against the bundled Beacon v2 schemas.
- Serializes workbook metadata into deterministic BFF collections.
- Normalizes and annotates raw VCF input with SnpEff, dbNSFP, ClinVar, and COSMIC.
- Converts VCF or SNP-array TSV data into streamed, compressed BFF `genomicVariations`.
- Generates a standalone **BFF Tools Browser** for clinical-style review.

The output remains independent of a particular Beacon server or database. For serving, consider the [Beacon v2 Production Implementation](https://github.com/EGA-archive/beacon2-pi-api) or [bycon](https://codeberg.org/Progenetix/bycon/).

## How data flows

![Flow from source metadata and variants through BFF Tools to portable BFF files and a downstream Beacon service](docs-site/static/img/beaconization-workflow.svg)

## Install

Python 3.10 or newer is required:

```bash
python3 -m pip install beacon2-cbi-tools
```

Docker, Apptainer, and source/HPC installations are first-class options in the [installation guide](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/installation/). The large annotation databases are installed separately and mounted or referenced through `config.yaml`.

## Main command

The `bff-tools` command has three focused modes:

- `validate`: validate XLSX or JSON metadata and write BFF collections.
- `vcf`: annotate and convert VCF data, with optional browser generation.
- `tsv`: convert SNP-array TSV input through VCF into BFF.

```bash
bff-tools --help
```

## Quick start

Create a workbook template, fill it, and validate the result:

```bash
bff-tools validate --template-out metadata.xlsx
bff-tools validate -i metadata.xlsx -o bff
```

Convert and annotate a cohort VCF:

```bash
bff-tools vcf -i cohort.vcf.gz --genome hg38 --dataset-id cohort-1 \
  --annotate --browser -c config.yaml
```

Annotation is enabled by default and requires the external bundle. Use `--no-annotate` only when the input already contains a compatible SnpEff `ANN` header and records; dbNSFP and ClinVar fields remain strongly recommended for complete BFF output.

## Example workflow

1. Prepare and validate metadata with `bff-tools validate`.
2. Convert VCF or SNP-array input with `bff-tools vcf` or `bff-tools tsv`.
3. Inspect the generated BFF files and optional standalone browser.
4. Import the collections into the storage layer used by the selected Beacon implementation.

The populated [CINECA synthetic cohort](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/CINECA_synthetic_cohort_EUROPE_UK1) provides a real-world metadata example. Compact annotated VCF fixtures are kept in `testdata/`; full release acceptance uses the complete 2,504-sample CINECA chromosome 22 data outside Git.

## Roadmap

- Follow Beacon v2 developments, including VRS alignment.
- Move to Beacon v3 once the specification is finalized.

## Development and validation

```bash
python3 -m pip install ".[test]"
pytest -q
```

The Python validator reproduces the former Perl output byte-for-byte across all 10,018 CINECA metadata records. The VCF converter is checked against Perl-generated output with strict type-sensitive streamed comparisons, including the complete 1,110,240-record chromosome 22 acceptance dataset.

## Citation

If you use these tools in published work, please cite:

Rueda M, Ariosa R. "Beacon v2 Reference Implementation: a toolkit to enable federated sharing of genomic and phenotypic data." *Bioinformatics*, btac568. <https://doi.org/10.1093/bioinformatics/btac568>

## Author

Written by Manuel Rueda, PhD, [CNAG Biomedical Informatics](https://www.cnag.eu).

## License

GNU General Public License v3.0 or later. See the [LICENSE](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/blob/main/LICENSE).

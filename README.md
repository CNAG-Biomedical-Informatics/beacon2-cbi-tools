<div align="center">
  <a href="https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools">
    <img src="https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/docs-site/static/img/logo.png" width="180" alt="Beacon v2 CBI Tools">
  </a>
  <h1>Beacon v2 CBI Tools</h1>
</div>

[![Build and test](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/build-and-test.yml)
[![Coverage: 98%](https://img.shields.io/badge/coverage-98%25-brightgreen.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/build-and-test.yml)
[![Docker build](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/docker-build-multi-arch.yml/badge.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/docker-build-multi-arch.yml)
[![Documentation](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/documentation.yml/badge.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/actions/workflows/documentation.yml)
![Maintenance status](https://img.shields.io/badge/maintenance-actively--developed-brightgreen.svg)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/blob/main/LICENSE)
[![Docker pulls](https://badgen.net/docker/pulls/manuelrueda/beacon2-cbi-tools?icon=docker&label=current-image-pulls)](https://hub.docker.com/r/manuelrueda/beacon2-cbi-tools/)
[![Historical Docker pulls](https://badgen.net/docker/pulls/manuelrueda/beacon2-ri-tools?icon=docker&label=beacon2-ri-tools-historical-pulls)](https://hub.docker.com/r/manuelrueda/beacon2-ri-tools/)
[![Historical EGA Docker pulls](https://badgen.net/docker/pulls/beacon2ri/beacon_reference_implementation?icon=docker&label=EGA-RI-historical-pulls)](https://hub.docker.com/r/beacon2ri/beacon_reference_implementation/)
![Version](https://img.shields.io/badge/version-2.0.13--dev-blue)

**Beacon v2 CBI Tools** prepares portable [Beacon Friendly Format (BFF)](https://docs.genomebeacons.org/models/) data for Beacon v2. Its command-line interface is called **`bff-tools`**. It validates phenotypic and clinical metadata, converts VCF or SNP-array TSV input into BFF `genomicVariations`, and can generate a standalone browser report.

**Beacon v2 CBI Tools** (`beacon2-cbi-tools`) is the actively developed continuation of the original `beacon2-ri-tools`, first developed at [EGA](https://ega-archive.org) and now maintained by its original developer at [CNAG Biomedical Informatics](https://www.cnag.eu). It is used by Beacon deployers and is independent of EGA's separate [`beacon2-ri-tools-v2`](https://github.com/EGA-archive/beacon2-ri-tools-v2) project.

The two historical image badges preserve the download record of earlier distributions; those images are deprecated for new installations.

## Quick links

- Documentation: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/>
- Installation: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/installation/>
- Quick start: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/quick-start/>
- End-to-end tutorial: <https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/workflows/data-beaconization/>
- Docker image: <https://hub.docker.com/r/manuelrueda/beacon2-cbi-tools/tags>

## What it does

- Validates XLSX workbooks and BFF JSON against the bundled Beacon v2 schemas.
- Serializes workbook metadata into deterministic BFF collections.
- Normalizes and annotates raw VCF input with SnpEff, dbNSFP, ClinVar, and COSMIC.
- Converts VCF or SNP-array TSV data into streamed, compressed BFF `genomicVariations`.
- Generates a standalone **BFF Tools Browser** for clinical-style review.

The output remains independent of a particular Beacon server or database. For serving, consider the [Beacon v2 Production Implementation](https://github.com/EGA-archive/beacon2-pi-api) or [bycon](https://codeberg.org/Progenetix/bycon/).

## How data flows

![Flow from source metadata and variants through Beacon v2 CBI Tools to portable BFF files and a downstream Beacon service](docs-site/static/img/beaconization-workflow.svg)

## Install

Python 3.10 or newer is required:

```bash
python3 -m pip install beacon2-cbi-tools
```

Docker, Apptainer, and source/HPC installations are first-class options in the [installation guide](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/installation/). The large annotation bundle remains outside the package and is installed with `bff-tools install-resources` into the directory selected by `BFF_TOOLS_DATA`.

## Main command

The `bff-tools` command has three focused data modes and two operational commands:

- `validate`: build and validate BFF metadata from XLSX, or validate existing BFF JSON.
- `vcf`: annotate and convert VCF data, with optional browser generation.
- `tsv`: convert SNP-array TSV input through VCF into BFF.
- `install-resources`: download and verify the external annotation bundle.
- `test`: exercise the installed annotation stack and compare its BFF output with the packaged oracle.

```bash
bff-tools --help
```

## Quick start

Create a workbook template, fill it, then build and validate BFF JSON:

```bash
bff-tools validate --template-out metadata.xlsx
bff-tools validate -i metadata.xlsx -o bff
```

Convert and annotate a cohort VCF:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools install-resources
bff-tools test
bff-tools vcf -i cohort.vcf.gz --genome hg38 --dataset-id cohort-1 \
  --annotate --browser
```

Annotation is enabled by default and requires the external bundle. Use `--no-annotate` only when the input already contains a compatible SnpEff `ANN` header and records; dbNSFP and ClinVar fields remain strongly recommended for complete BFF output.

## Example workflow

1. Prepare and validate metadata with `bff-tools validate`.
2. Convert VCF or SNP-array input with `bff-tools vcf` or `bff-tools tsv`.
3. Inspect the generated BFF files and optional standalone browser.
4. Import the collections into the storage layer used by the selected Beacon implementation.

The populated [CINECA synthetic cohort](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/CINECA_synthetic_cohort_EUROPE_UK1) provides a real-world metadata example. Its workbook and generated BFF collections are preserved together by Beacon schema version, with compatibility aliases pointing to the current snapshot. Compact annotated VCF fixtures are kept in `testdata/`; full release acceptance uses the complete 2,504-sample CINECA chromosome 22 data outside Git.

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

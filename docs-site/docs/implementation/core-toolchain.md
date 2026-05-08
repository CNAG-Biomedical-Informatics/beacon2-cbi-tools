---
title: Core Toolchain
---

# Core Toolchain

These entry points are part of the main `bff-tools` data-preparation workflow.

## User-Facing Entrypoints

| Entrypoint | Language | Purpose |
|---|---|---|
| `bin/bff-tools` | ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) | Main command-line interface for `vcf`, `tsv`, `validate`, `load`, and `full` workflows |
| `utils/bff_validator/bff-validator` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Validator used by `bff-tools validate` for Beacon metadata in XLSX or JSON form |

## Pipeline Helpers

These helpers are normally called by `bin/bff-tools`, not by end users directly.

| Helper | Language | Purpose |
|---|---|---|
| `pipeline/internal/partial/run_tsv2vcf.sh` | ![Shell](https://img.shields.io/badge/Shell-4EAA25?logo=gnubash&logoColor=white) | Converts SNP-array TSV/TXT input into a VCF-like intermediate |
| `pipeline/internal/partial/run_vcf2bff.sh` | ![Shell](https://img.shields.io/badge/Shell-4EAA25?logo=gnubash&logoColor=white) | Runs VCF normalization, annotation, and BFF conversion |
| `pipeline/internal/partial/run_bff2html.sh` | ![Shell](https://img.shields.io/badge/Shell-4EAA25?logo=gnubash&logoColor=white) | Builds static browser-oriented output |
| `pipeline/internal/partial/run_bff2mongodb.sh` | ![Shell](https://img.shields.io/badge/Shell-4EAA25?logo=gnubash&logoColor=white) | Loads BFF collections into MongoDB |
| `pipeline/internal/complete/vcf2bff.pl` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Converts annotated VCF records into BFF `genomicVariations` |
| `pipeline/internal/complete/bff2json.pl` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Prepares JSON data for browser output |
| `pipeline/internal/complete/bff2html.pl` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Generates static HTML browser output |

## Practical Notes

- `bff-tools validate` delegates validation to `utils/bff_validator/bff-validator`.
- `bff-tools vcf`, `bff-tools tsv`, and `bff-tools full` use the shell wrappers under `pipeline/internal/partial/`.
- The Perl scripts under `pipeline/internal/complete/` contain the conversion logic used by those wrappers.

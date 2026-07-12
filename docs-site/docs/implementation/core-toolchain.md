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
| `pipeline/internal/complete/vcf2bff.pl` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Converts annotated VCF records into BFF `genomicVariations` |
| `src/bff_tools/browser.py` | ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) | Generates a standalone HTML browser report directly from BFF genomic variations |
| `src/bff_tools/orchestrator.py` | ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) | Executes browser generation and checked MongoDB imports/indexing |

## Practical Notes

- `bff-tools validate` delegates validation to `utils/bff_validator/bff-validator`.
- `bff-tools vcf`, `bff-tools tsv`, and `bff-tools full` use the shell wrappers under `pipeline/internal/partial/`.
- The VCF-to-BFF conversion remains in Perl; browser report generation now runs directly in Python.

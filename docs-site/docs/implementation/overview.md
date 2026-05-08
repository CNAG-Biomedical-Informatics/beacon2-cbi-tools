---
title: Implementation
---

# Implementation

`beacon2-cbi-tools` combines Python, Perl, and shell entry points. The important distinction is between the core `bff-tools` toolchain and optional utilities around it.

## Core Flow

![Beacon v2 CBI Tools core flow](/img/bff-tools-core-flow.svg)

## How To Read This Section

- [Core toolchain](core-toolchain.md): the main `bff-tools` command, validator, and pipeline helpers.
- [Optional utilities](utilities.md): helper applications for browsing, querying, queueing, and model-template generation.

## Language Badges

| Badge | Meaning |
|---|---|
| ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) | Python entry point |
| ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Perl entry point |
| ![Shell](https://img.shields.io/badge/Shell-4EAA25?logo=gnubash&logoColor=white) | Shell script |

## Practical Summary

- Use `bin/bff-tools` for normal data preparation.
- Treat `utils/bff_validator/bff-validator` as part of the core `bff-tools` validation path.
- Use `utils/bff_browser`, `utils/bff_portal`, or `utils/bff_queue` only when you need browsing, querying, or job orchestration.
- The shell and Perl pipeline helpers are implementation details called by `bff-tools`.

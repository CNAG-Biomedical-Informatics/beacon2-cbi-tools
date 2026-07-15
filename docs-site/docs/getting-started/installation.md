---
title: Install
---

The four supported installation paths expose the same `bff-tools` CLI. Choose based on where the application and its external annotation toolchain should run.

| Environment | Recommended path | Why |
|---|---|---|
| Python environment | [PyPI](https://pypi.org/project/beacon2-cbi-tools/) | Smallest installation for validation, pre-annotated VCF conversion, and standalone report generation |
| HPC cluster | [Apptainer / Singularity](apptainer) | No daemon or root runtime; immutable image works with schedulers and bind-mounted reference data |
| Workstation or server | [Docker](docker) | Reproducible dependencies and the shortest setup when Docker is available |
| Managed host or module stack | [From source](from-source) | Direct control over Python, Java, bcftools, and scheduler modules |

Containerized execution is the primary route for HPC and shared infrastructure. It keeps the application reproducible while the large, frequently reused biological databases remain on high-throughput shared storage.

## Install from PyPI

Create an isolated Python environment and install the published package:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install beacon2-cbi-tools
bff-tools --version
```

The package installs the command as `bff-tools`. The `bin/bff-tools` path is only a compatibility shim for running directly from a Git checkout.

The PyPI package provides the Python application, bundle installer, default annotation-resource layout, schemas, templates, panels, and browser assets. It does not contain the large external annotation bundle. Metadata validation and conversion of a compatible pre-annotated VCF can run immediately; raw VCF and TSV workflows also require the annotation layer described below.

Install and select that bundle without editing anything under `site-packages`:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools install-resources
```

Upgrade an existing environment with:

```bash
python3 -m pip install --upgrade beacon2-cbi-tools
```

## Two Installation Layers

1. Install the application from PyPI, Docker, Apptainer, or source.
2. Prepare the [annotation data](annotation-data) used by most real-world VCF workflows and export `BFF_TOOLS_DATA`.

Metadata validation can run after layer 1. Raw VCF and TSV conversion requires both layers. A VCF with a compatible SnpEff `ANN` header can skip re-annotation with `--no-annotate` and still use the same converter.

## Supported Platforms

- Linux on x86-64 or ARM64;
- Python 3.10 or newer for PyPI and source installations;
- at least 4 GB RAM for basic use;
- memory sized for Java/SnpEff and cohort scale for annotation;
- at least 200 GB free for the maintained annotation bundle and more for intermediates.

## Verify the Application

Every installation should provide:

```bash
bff-tools --version
bff-tools validate --help
bff-tools vcf --help
bff-tools install-resources --help
```

After preparing annotation data, process a small representative VCF with the production configuration before starting a cohort-scale run. Project and bundle maintainers can additionally run the [developer integration test](annotation-data#developer-integration-test).

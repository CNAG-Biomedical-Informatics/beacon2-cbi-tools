---
title: Install
---

The three supported installation paths expose the same `bff-tools` CLI and use the same external annotation bundle.

| Environment | Recommended path | Why |
|---|---|---|
| HPC cluster | [Apptainer / Singularity](apptainer) | No daemon or root runtime; immutable image works with schedulers and bind-mounted reference data |
| Workstation or server | [Docker](docker) | Reproducible dependencies and the shortest setup when Docker is available |
| Managed host or module stack | [From source](from-source) | Direct control over Python, Java, bcftools, and scheduler modules |

Containerized execution is the primary route for HPC and shared infrastructure. It keeps the application reproducible while the large, frequently reused biological databases remain on high-throughput shared storage.

For a Python environment that only needs validation or conversion of pre-annotated VCFs:

```bash
python3 -m pip install beacon2-cbi-tools
```

## Two Installation Layers

1. Install the application through Docker, Apptainer, or source.
2. Prepare the [annotation data](annotation-data) used by most real-world VCF workflows.

Metadata validation can run after layer 1. Raw VCF and TSV conversion requires both layers. A VCF with a compatible SnpEff `ANN` header can skip re-annotation with `--no-annotate` and still use the same converter.

## Supported Platforms

- Linux on x86-64 or ARM64;
- Python 3.10 or newer for source installations;
- at least 4 GB RAM for basic use;
- memory sized for Java/SnpEff and cohort scale for annotation;
- at least 200 GB free for the maintained annotation bundle and more for intermediates.

## Verify the Application

Every installation should provide:

```bash
bff-tools --version
bff-tools validate --help
bff-tools vcf --help
```

After preparing annotation data, run the [full deployment integration](annotation-data#full-deployment-integration) before processing a cohort.

---
title: Configuration
---

Configuration is split between workflow parameters and external annotation resources. They are separate YAML files with different purposes.

### Parameter file (`-p`, `--param`)

**Optional.** Stores run choices such as assembly, dataset ID, annotation, browser output, and output prefix. Use it when preserving a run profile is more convenient than repeating CLI options.

### Annotation configuration (`-c`, `--config`)

**Required for raw VCF and TSV annotation.** Stores paths to Java, bcftools, FASTA, SnpEff/SnpSift, and annotation databases.

A parameter file does not replace the annotation configuration.

## Parameters

Parameter YAML is optional. This example can be saved as `cohort.yaml` and passed with `-p cohort.yaml`:

```yaml
genome: hg38
datasetid: cohort-1
projectdir: cohort-bff
annotate: true
bff2html: true
```

| Key | Default | Purpose |
|---|---|---|
| `genome` | `hg19` | Input assembly profile |
| `datasetid` | `default_beacon_1` | Dataset attached to generated variants |
| `projectdir` | `beacon` plus a run ID | Output-directory prefix |
| `sampleid` | `23andme_1` | Sample name used for TSV conversion |
| `annotate` | `true` | Annotate raw input; set false only for a compatibly annotated VCF |
| `bff2html` | `false` | Generate the standalone HTML report |
| `center` | `CNAG` | Provenance metadata |
| `organism` | `Homo sapiens` | Organism metadata |
| `technology` | `Illumina HiSeq 2000` | Sequencing-technology metadata |

Equivalent CLI options override YAML values. For example, `--genome hg38 --no-annotate` wins over both keys in the file.

## Annotation Configuration

The external configuration is required for raw VCF and TSV input. A pre-annotated VCF can bypass it with `--no-annotate` when it already contains a compatible SnpEff `ANN` header.

```yaml
base: /data/beacon2-cbi-tools

javabin: /usr/bin/java
bcftools: "{base}/soft/NGSutils/bcftools-1.21-103_{arch}/bcftools"
snpeff: "{base}/soft/snpEff/snpEff.jar"
snpsift: "{base}/soft/snpEff/SnpSift.jar"

hg38fasta: "{base}/databases/genomes/hg38.fa.gz"
hg38dbnsfp: "{base}/databases/snpeff/v5.0/hg38/dbNSFP4.1a_hg38.txt.gz"
hg38clinvar: "{base}/databases/snpeff/v5.0/hg38/clinvar_20250312.vcf.gz"
hg38cosmic: "{base}/databases/snpeff/v5.0/hg38/CosmicCodingMuts.normal.hg38.vcf.gz"

tmpdir: "{base}/tmp"
mem: 8G
dbnsfpset: all
```

Start from the repository [`bin/config.yaml`](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/blob/main/bin/config.yaml) rather than retyping paths. `{base}` and `{arch}` placeholders are expanded after loading; `{arch}` becomes `x86_64` or `arm64`. `dbnsfpset` accepts `cnag` for the focused field set or `all` for every dbNSFP header field.

Pass the file with `--config`. For a stable workstation or HPC installation, set it once in the environment instead:

```bash
export BFF_TOOLS_CONFIG=/shared/beacon2-cbi-tools/config.yaml
bff-tools vcf -i cohort.vcf.gz --genome hg38
```

An explicit `--config` takes precedence over `BFF_TOOLS_CONFIG`. Source checkouts fall back to `bin/config.yaml`; installed packages require one of the explicit forms for annotation.

For `hs37`, ClinVar, COSMIC, and dbNSFP default to the configured `hg19` resources, while a distinct `hs37fasta` is still required.

`mem` controls the Java heap used by SnpEff and SnpSift. It is not a total process or scheduler memory limit. `tmpdir` must exist and be writable in the host or container namespace where the command runs.

## Conditional Checks

- `vcf --no-annotate` checks only the installed Python runtime and bundled converter, then verifies the VCF has a usable SnpEff `ANN` header.
- `vcf` and `tsv` annotation check Java, SnpEff, SnpSift, bcftools, FASTA, ClinVar, COSMIC, dbNSFP, and the temporary directory.
- `tsv --no-annotate` is rejected because the generated VCF has no ANN annotations.
- `--browser` checks the packaged gene-panel directory.

Failures identify the missing key or path before a run directory is created.

## Project Directories

Without `-o`, the default prefix `beacon` receives a unique run identifier. An explicit `-o cohort-bff` is convenient for scripts, but that directory must not already exist. This prevents an accidental retry from mixing files from different inputs or annotation versions.

## Legacy MongoDB Keys

Commented `mongoimport`, `mongostat`, `mongodburi`, and `mongosh` examples remain in repository configurations only as migration references. They are not read by the current application and will disappear after the compatibility period. MongoDB tools are installed separately.

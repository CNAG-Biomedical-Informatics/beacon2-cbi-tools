---
title: Configuration
---

Configuration is split between optional workflow parameters and the external annotation-resource layout. The standard layout is packaged with the application, while the large data itself remains outside the Python package.

### Parameter file (`-p`, `--param`)

**Optional.** Stores run choices such as assembly, dataset ID, annotation, browser output, and output prefix. Use it when preserving a run profile is more convenient than repeating CLI options.

### Annotation data root (`BFF_TOOLS_DATA`)

**Required for the standard raw VCF and TSV annotation workflow.** Points to the extracted external bundle. The driver resolves it once, expands `~`, converts it to an absolute path, validates the selected resources, and records the resolved paths in `log.json`.

### Annotation configuration (`-c`, `--config`)

**Optional override.** Stores a nonstandard mapping for Java, bcftools, FASTA, SnpEff/SnpSift, and annotation databases. Most users of the maintained bundle do not need this file.

## Parameters

Parameter YAML is optional. This example can be saved as `cohort.yaml` and passed with `-p cohort.yaml`:

```yaml
genome: hg38
datasetid: cohort-1
projectdir: cohort-bff
annotate: true
bff2html: true
jsonl: false
progress_every: 10000
```

| Key | Default | Purpose |
|---|---|---|
| `genome` | `hg19` | Input assembly profile |
| `datasetid` | `default_beacon_1` | Dataset attached to generated variants |
| `projectdir` | `beacon` plus a run ID | Output-directory prefix |
| `sampleid` | `23andme_1` | Sample name used for TSV conversion |
| `annotate` | `true` | Annotate raw input; set false only for a compatibly annotated VCF |
| `bff2html` | `false` | Generate the standalone HTML report |
| `jsonl` | `false` | Write `genomicVariationsVcf.jsonl.gz` for streaming imports instead of a JSON array |
| `progress_every` | `10000` | With verbose output, report VCF progress every N records |
| `center` | `CNAG` | Provenance metadata |
| `organism` | `Homo sapiens` | Organism metadata |
| `technology` | `Illumina HiSeq 2000` | Sequencing-technology metadata |

Equivalent CLI options override YAML values. For example, `--genome hg38 --no-annotate` wins over both keys in the file.

## Annotation Data and Layout

For the maintained bundle, select its root and use the packaged layout:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools vcf -i cohort.vcf.gz --genome hg38
```

A pre-annotated VCF can bypass external annotation data with `--no-annotate` when it already contains a compatible SnpEff `ANN` header.

The packaged configuration is equivalent to the repository [`bin/config.yaml`](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/blob/main/bin/config.yaml). A custom layout can override it:

```yaml
base: /data/beacon2-cbi-tools

javabin: /usr/bin/java
bcftools: "{base}/soft/NGSutils/bcftools-1.21-103_{arch}/bcftools"
snpeff: "{base}/soft/snpEff/snpEff.jar"
snpeffdata: "{base}/databases/snpeff/v5.0"
snpsift: "{base}/soft/snpEff/SnpSift.jar"

hg38fasta: "{base}/databases/genomes/hg38.fa.gz"
hg38dbnsfp: "{base}/databases/snpeff/v5.0/hg38/dbNSFP4.1a_hg38.txt.gz"
hg38clinvar: "{base}/databases/snpeff/v5.0/hg38/clinvar_20250312.vcf.gz"
hg38cosmic: "{base}/databases/snpeff/v5.0/hg38/CosmicCodingMuts.normal.hg38.vcf.gz"

tmpdir: "{base}/tmp"
mem: 8G
dbnsfpset: all
```

Start from that file rather than retyping paths. `{base}` and `{arch}` placeholders are expanded after loading; `{arch}` becomes `x86_64` or `arm64`. `BFF_TOOLS_DATA` takes precedence over `base`. Absolute resource paths without `{base}` remain unchanged, which allows an HPC profile to use site-managed executables alongside the shared bundle. `dbnsfpset` accepts `cnag` for the focused field set or `all` for every dbNSFP header field.

Pass a custom file with `--config`. For a stable workstation or HPC installation, select a shared custom layout once instead:

```bash
export BFF_TOOLS_CONFIG=/shared/beacon2-cbi-tools/config.yaml
bff-tools vcf -i cohort.vcf.gz --genome hg38
```

Layout precedence is explicit `--config`, then `BFF_TOOLS_CONFIG`, then `bin/config.yaml` in a source checkout or the packaged default in an installed wheel. Independently, `BFF_TOOLS_DATA` overrides the selected layout's `base` value.

For `hs37`, ClinVar, COSMIC, and dbNSFP default to the configured `hg19` resources, while a distinct `hs37fasta` is still required.

`snpeffdata` identifies the local SnpEff database directory. The generated command passes it through `-dataDir` and uses `-nodownload`, so users do not edit `snpEff.config`. `mem` controls the Java heap used by SnpEff and SnpSift. It is not a total process or scheduler memory limit. `tmpdir` must exist and be writable in the host or container namespace where the command runs.

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

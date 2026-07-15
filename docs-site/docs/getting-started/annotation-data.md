---
title: Annotation Data
---

Raw research VCFs and SNP-array input require the complete annotation workflow. It normalizes alleles and adds the SnpEff ANN fields required by the BFF converter:

| Stage | Purpose |
|---|---|
| bcftools | Normalize and split alleles against the selected FASTA |
| SnpEff | Add transcript consequences in `ANN` |
| SnpSift + dbNSFP | Add prediction scores, frequencies, gene and protein identifiers |
| SnpSift + ClinVar | Add clinical variation identifiers and interpretations |
| SnpSift + COSMIC | Add somatic catalogue annotations to the VCF |

The current BFF converter requires ANN and uses dbNSFP and ClinVar extensively. COSMIC is retained in the annotated VCF and provenance even where a field is not yet mapped into BFF. A VCF that already has compatible ANN data can use `--no-annotate`, but dbNSFP and ClinVar remain strongly recommended for complete output.

## Storage and Licensing

Allow at least **200 GB** for the distributed bundle, extraction, indexes, temporary files, and annotation intermediates. Production cohorts may require considerably more working space.

Reference databases have their own terms of use. In particular, confirm that your use of dbNSFP and COSMIC complies with their academic or institutional licenses before downloading or redistributing data.

The external bundle has its own revision lifecycle and is not renamed for every application release. An application release continues to use the same bundle revision and checksum until the bundle contents change.

| Revision | Date | Status | Main change |
|---|---|---|---|
| `r1` | 2022-08 | Historical | Original annotation bundle |
| `r2` | 2025-03 | Historical | Added ARM64 support and refreshed annotation tools and databases |
| `r3` | 2026-07 | Current | Removed obsolete MongoDB utilities while retaining the annotation toolchain |

Google Drive provides only the current revision because retaining several copies of this large archive is impractical. The revision identifies an immutable bundle artifact, not a biological-database generation or an application version.

## Install the Maintained Bundle

Choose the persistent directory that will contain `databases/`, `soft/`, and writable `tmp/`, then run the installer supplied by every PyPI, container, and source distribution:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools install-resources
```

Use a clean directory when replacing `r1` or `r2`. The installer deliberately refuses to overlay an unversioned existing `databases/` or `soft/` layout, which prevents obsolete files from surviving an upgrade.

The command downloads only missing `r3` files, resumes an interrupted part, verifies all seven split-part checksums, streams their concatenation into `beacon2-cbi-tools-data-r3.tar.gz`, extracts directly into `BFF_TOOLS_DATA`, records the installed revision, and creates `tmp/`. Rerunning it after an interrupted download or completed extraction is safe.

Google Drive may reject or throttle the download after several large parts. Completed parts are retained, and rerunning the command later resumes the interrupted part. To download a rejected part through a browser, print the public folder and individual links without starting another automatic download:

```bash
bff-tools install-resources --print-links
```

Download the named files into `$BFF_TOOLS_DATA`, then rerun `bff-tools install-resources`; existing non-empty files are reused. If checksum verification identifies a bad or incomplete part, remove only that part and rerun. After successful extraction, the split parts and assembled archive may be removed when storage is limited; retain the checksum manifest with the run provenance.

## Select the Bundle

Set one environment variable to the extracted bundle root:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
```

The PyPI wheel, container image, and source checkout contain the standard resource layout. The driver expands and resolves `BFF_TOOLS_DATA`, validates the files needed for the selected assembly, and records the resolved paths in `log.json`. It also passes the local SnpEff directory through `-dataDir` with downloads disabled, so `snpEff.config` does not need to be edited.

The packaged layout is equivalent to [`bin/config.yaml`](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/blob/main/bin/config.yaml):

```yaml
base: /beacon2-cbi-tools-data

javabin: /usr/bin/java
hs37fasta: "{base}/databases/genomes/hs37d5.fa.gz"
hg19fasta: "{base}/databases/genomes/ucsc.hg19.fasta.gz"
hg38fasta: "{base}/databases/genomes/hg38.fa.gz"

hg19clinvar: "{base}/databases/snpeff/v5.0/hg19/clinvar_20250312.vcf.gz"
hg38clinvar: "{base}/databases/snpeff/v5.0/hg38/clinvar_20250312.vcf.gz"
hg19cosmic: "{base}/databases/snpeff/v5.0/hg19/CosmicCodingMuts.normal.hg19.vcf.gz"
hg38cosmic: "{base}/databases/snpeff/v5.0/hg38/CosmicCodingMuts.normal.hg38.vcf.gz"
hg19dbnsfp: "{base}/databases/snpeff/v5.0/hg19/dbNSFP4.1a_hg19.txt.gz"
hg38dbnsfp: "{base}/databases/snpeff/v5.0/hg38/dbNSFP4.1a_hg38.txt.gz"

snpeff: "{base}/soft/snpEff/snpEff.jar"
snpeffdata: "{base}/databases/snpeff/v5.0"
snpsift: "{base}/soft/snpEff/SnpSift.jar"
bcftools: "{base}/soft/NGSutils/bcftools-1.21-103_{arch}/bcftools"
tmpdir: "{base}/tmp"
mem: 8G
dbnsfpset: all
```

`hs37` uses its own FASTA and the configured hg19 annotation resources. Confirm that this is appropriate for the contigs and coordinates in your VCF.

`BFF_TOOLS_DATA` overrides `base` in this mapping. Use `--config` or `BFF_TOOLS_CONFIG` only for a different directory structure or site-managed executable paths.

## Run with Docker

Build or pull the annotation-capable image, then mount the bundle and expose its in-container root:

```bash
docker run --rm \
  -v "$PWD:/work" \
  -v "/absolute/path/to/beacon2-cbi-tools-data:/beacon2-cbi-tools-data" \
  -e BFF_TOOLS_DATA=/beacon2-cbi-tools-data \
  beacon2-cbi-tools:annotation \
  vcf -i /work/cohort.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  --annotate \
  -o /work/cohort-bff
```

## Run Directly or on HPC

Install Java and the configured bcftools binary, then select the host-visible bundle root:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools vcf \
  -i cohort.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  --annotate
```

On a scheduler, request memory and temporary storage for both Java annotation and all intermediate VCF files. `mem` controls the Java heap; it is not a total-job memory limit.

## Preflight

The CLI checks every required executable, reference file, and temporary directory before creating output. A successful preflight does not verify biological version compatibility, so record database versions and manually inspect representative ANN, dbNSFP, ClinVar, and COSMIC records after each resource update.

## Packaged Integration Test

:::note[Maintainer check]
`bff-tools test` is intended for application developers and annotation-bundle maintainers. Routine users do not need to run it before beaconizing data.
:::

Distributions include a compact chromosome 1 input fixture and its versioned reference BFF output. Exercise the installed application and selected annotation bundle through the CLI:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools test
```

Temporary output is removed after a successful run. Retain the generated project for inspection when diagnosing an installation:

```bash
bff-tools test --output-dir annotation-integration-review --verbose
```

This built-in test starts from a compact raw **1000 Genomes GRCh37 chromosome 1** VCF packaged with the application. It runs bcftools normalization, SnpEff, dbNSFP, ClinVar, COSMIC, Python VCF-to-BFF conversion, streamed schema validation, and semantic comparison of all 1,044 emitted records. The fixture needs no separate download, but the annotation bundle must exist at `BFF_TOOLS_DATA` or be supplied with `--data-dir`. The manually dispatched GitHub Actions workflow invokes this same compact test on a self-hosted runner.

This compact test is distinct from the full CINECA chromosome 22 release gate. The latter is also GRCh37/hs37d5 and covers 1,103,547 raw records, 1,110,240 normalized records, and 2,504 samples. Its files remain outside Git. Beacon v2 CBI Tools performs the full annotation, conversion, and validation run, but `bff-tools test` does not select or download that fixture. See [Full CINECA Release Fixture](../reference/validation-and-reproducibility#full-cineca-release-fixture) for the exact procedure.

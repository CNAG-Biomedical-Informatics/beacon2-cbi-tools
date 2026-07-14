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

The current compatibility archive predates the beaconization-only product scope and may contain legacy MongoDB runtime files that `bff-tools` no longer uses. Keep the downloaded archive intact for path compatibility. The next bundle will retain annotation tools and databases, omit MongoDB files, and use the code version of the release that introduces it. Later application releases will reuse that exact bundle filename and checksum until its contents change.

## Download the Maintained Bundle

Run this in the directory that will hold the external data:

```bash
python3 -m pip install gdown
wget https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/deploy/01_download_external_data.py
python3 01_download_external_data.py
md5sum -c data.tar.gz.md5
cat data.tar.gz.part-?? > data.tar.gz
tar -xzf data.tar.gz
mkdir -p data/tmp
```

The download is split into multiple Google Drive objects. The script skips parts already present, so an interrupted download can be resumed. If Google Drive rejects an automated request, use the printed URL to retrieve that part manually and rerun the checksum.

## Select the Bundle

Set one environment variable to the extracted `data` directory:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/data
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
  -v "/absolute/path/to/data:/beacon2-cbi-tools-data" \
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
export BFF_TOOLS_DATA=/absolute/path/to/data
bff-tools vcf \
  -i cohort.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  --annotate
```

On a scheduler, request memory and temporary storage for both Java annotation and all intermediate VCF files. `mem` controls the Java heap; it is not a total-job memory limit.

## Preflight

The CLI checks every required executable, reference file, and temporary directory before creating output. A successful preflight does not verify biological version compatibility, so record database versions and manually inspect representative ANN, dbNSFP, ClinVar, and COSMIC records after each resource update.

## Full Deployment Integration

The repository retains a full annotation integration test. Reuse an extracted bundle:

```bash
BFF_TOOLS_DATA=/absolute/path/to/data \
  deploy/02_test_deployment.sh
```

Or let the test download, verify, combine, and extract every archive part before running:

```bash
deploy/02_test_deployment.sh --download /path/with/at-least-200GB-free
```

The test runs bcftools normalization, SnpEff, dbNSFP, ClinVar, COSMIC, Python VCF-to-BFF conversion, streamed schema validation, and semantic comparison with the committed reference output. A self-hosted manual GitHub Actions workflow exposes the same test without forcing the large download on ordinary pull requests.

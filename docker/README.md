# Containerized Installation with Docker

Docker is the recommended runtime for workstations and servers. The published image contains `bff-tools`, Python, Java, bcftools, SnpEff, and SnpSift. Large reference and annotation databases remain outside the image and are mounted at runtime.

The image does **not** install MongoDB, `mongosh`, or MongoDB Database Tools. `bff-tools` produces BFF files; database loading is an optional downstream step.

## Requirements

- Linux on `amd64` or `arm64`;
- a working Docker Engine with permission to run containers;
- at least 4 GB RAM for validation and more for Java annotation;
- at least 200 GB for the annotation bundle, plus working space for intermediate VCFs and BFF output.

## 1. Pull the Published Image

Use a numbered tag for reproducible work. `latest` follows the newest published release:

```bash
docker pull manuelrueda/beacon2-cbi-tools:latest
docker run --rm manuelrueda/beacon2-cbi-tools:latest --version
```

## 2. Validate Metadata

Mount the working directory at `/work`. Supplying the host user and group avoids root-owned output files:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" \
  manuelrueda/beacon2-cbi-tools:latest \
  validate -i /work/metadata.xlsx -o /work/bff
```

Export a fresh workbook template in the same way:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" \
  manuelrueda/beacon2-cbi-tools:latest \
  validate --template-out /work/metadata.xlsx
```

## 3. Prepare Annotation Data

Raw VCF and SNP-array input requires the external annotation bundle. Download it once on the host, verify its checksum, and configure SnpEff as described in the [annotation-data guide](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/annotation-data/).

Keep the mount point stable. The examples use:

```text
/beacon2-cbi-tools-data
```

The host directory and container path do not have to match, but every path in `config.yaml` must be valid **inside** the container.

## 4. Annotate and Convert a Raw VCF

Place `cohort.vcf.gz` and a copy of `config.yaml` in the working directory:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" \
  -v "/absolute/path/to/data:/beacon2-cbi-tools-data" \
  manuelrueda/beacon2-cbi-tools:latest \
  vcf -i /work/cohort.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  -c /work/config.yaml \
  -o /work/cohort-bff
```

Annotation is enabled by default. The command normalizes the VCF, applies SnpEff, dbNSFP, ClinVar, and COSMIC, then writes BFF genomic variations.

If `tmpdir` is inside the annotation-data mount, that mount must be writable. A stricter deployment can mount reference directories read-only and bind a separate writable temporary directory.

## 5. Convert an Already Annotated VCF

Use `--no-annotate` only when the input has a compatible SnpEff `ANN` header and record annotations:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" \
  manuelrueda/beacon2-cbi-tools:latest \
  vcf -i /work/cohort.annotated.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  --no-annotate \
  -o /work/cohort-bff
```

dbNSFP and ClinVar fields are not mandatory for parsing, but they are strongly recommended for complete BFF identifiers, frequencies, predictions, and clinical interpretations.

## 6. Open an Interactive Shell

The normal image entry point is `bff-tools`. Override it only when a shell is useful for inspecting mounts or logs:

```bash
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  --entrypoint bash \
  -v "$PWD:/work" \
  -v "/absolute/path/to/data:/beacon2-cbi-tools-data" \
  manuelrueda/beacon2-cbi-tools:latest
```

One-shot `docker run --rm` commands are preferred for production because inputs, mounts, and image tags remain visible in job provenance.

## 7. Build Locally

Build from a repository checkout so the image contains the exact source you
selected. For a released version, check out its tag before building. The
version and Git revision can be recorded in the image metadata:

```bash
docker build --target core \
  --build-arg BFF_TOOLS_VERSION="$(cat VERSION)" \
  --build-arg VCS_REF="$(git rev-parse HEAD)" \
  -t beacon2-cbi-tools:core -f docker/Dockerfile .

docker build --target runtime \
  --build-arg BFF_TOOLS_VERSION="$(cat VERSION)" \
  --build-arg VCS_REF="$(git rev-parse HEAD)" \
  -t beacon2-cbi-tools:annotation -f docker/Dockerfile .
```

The `core` target supports metadata validation and `--no-annotate` VCF conversion. The default `runtime` target adds the annotation executables but still requires the external databases.

Inspect the source revision recorded in an image with:

```bash
docker inspect beacon2-cbi-tools:annotation \
  --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}'
```

GitHub Actions uses the same model: it checks out one commit, passes that
checkout as the Docker build context, and records the commit in the OCI image
labels. No source is cloned while the image is being built.

## Verification

Smoke-test the installed command:

```bash
docker run --rm manuelrueda/beacon2-cbi-tools:latest validate --help
docker run --rm manuelrueda/beacon2-cbi-tools:latest vcf --help
```

After mounting the complete bundle, run the repository's [full annotation integration test](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/annotation-data/#full-deployment-integration) before processing a production cohort.

## Troubleshooting

### A configured file does not exist

The path is checked inside the container. Confirm the host bind source exists, the destination matches `{base}` in `config.yaml`, and architecture-specific paths resolve to `x86_64` or `arm64`.

### SnpEff tries to use the network

Set `data.dir` in the `snpEff.config` beside the configured jar to the mounted database path visible inside the container.

### The output directory already exists

Runs do not overwrite project directories. Select a new `-o` path or archive and move the previous result.

### Docker cannot resolve package or image hosts

This is a Docker daemon or host-networking problem rather than a `bff-tools` error. Correct proxy, DNS, certificate, or registry access and retry.

## MongoDB

There is no Compose stack in this repository. For an optional MongoDB deployment, install the clients separately and follow the [MongoDB import guide](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/reference/mongodb/).

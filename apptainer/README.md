# Containerized Installation with Apptainer or Singularity

Apptainer is the recommended installation for HPC systems. It runs an immutable image without a Docker daemon and binds cluster filesystems directly into interactive sessions and scheduler jobs.

The image does **not** contain MongoDB or the large annotation databases. Store reference data once on shared high-throughput storage.

## Requirements

- Linux on `amd64` or `arm64`;
- Apptainer or Singularity, commonly supplied as an environment module;
- project storage for the SIF, cache, annotation bundle, intermediates, and BFF output;
- scheduler memory sized above the configured Java heap.

## 1. Load the Runtime

```bash
module load apptainer
apptainer --version
```

Use `singularity` in place of `apptainer` on clusters that retain the older command name.

## 2. Pull the Image

Put cache and temporary files on project storage rather than a small home directory:

```bash
export APPTAINER_CACHEDIR=/path/to/project/cache
export APPTAINER_TMPDIR=/path/to/project/tmp

apptainer pull beacon2-cbi-tools.sif \
  docker://manuelrueda/beacon2-cbi-tools:latest
```

For reproducible work, record the application version and SIF checksum:

```bash
apptainer exec beacon2-cbi-tools.sif bff-tools --version
sha256sum beacon2-cbi-tools.sif
```

## 3. Validate Metadata

```bash
apptainer exec \
  --bind "$PWD:/work" \
  beacon2-cbi-tools.sif \
  bff-tools validate -i /work/metadata.xlsx -o /work/bff
```

Apptainer runs with the invoking user's identity, so output files retain normal cluster ownership.

## 4. Prepare Annotation Data

Raw VCF and SNP-array input requires the external annotation bundle. Download and verify it once, then follow the [annotation-data guide](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/annotation-data/).

Use a stable bind destination such as `/beacon2-cbi-tools-data`, and make all paths in `config.yaml` refer to the paths visible inside the container.

## 5. Annotate and Convert a Raw VCF

```bash
apptainer exec \
  --bind "$PWD:/work" \
  --bind "/shared/beacon2-data:/beacon2-cbi-tools-data" \
  beacon2-cbi-tools.sif \
  bff-tools vcf -i /work/cohort.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  -c /work/config.yaml \
  -o /work/cohort-bff
```

Annotation is enabled by default. Use `--no-annotate` only for VCF input that already has a compatible SnpEff `ANN` header and record annotations.

## 6. Bind Writable Scratch Space

Java annotation and compressed intermediates can be large. If `/tmp` is restricted, configure `tmpdir` and bind a scheduler-local or project scratch directory:

```bash
mkdir -p /path/to/project/bff-tmp

apptainer exec \
  --bind "$PWD:/work" \
  --bind "/shared/beacon2-data:/beacon2-cbi-tools-data" \
  --bind "/path/to/project/bff-tmp:/bff-tmp" \
  beacon2-cbi-tools.sif \
  bff-tools vcf -i /work/cohort.vcf.gz \
  --genome hg38 -c /work/config.yaml -o /work/cohort-bff
```

Set `tmpdir: /bff-tmp` in the configuration used by that command.

## 7. Open an Interactive Shell

```bash
apptainer shell \
  --bind "$PWD:/work" \
  --bind "/shared/beacon2-data:/beacon2-cbi-tools-data" \
  beacon2-cbi-tools.sif
```

Direct `apptainer exec` commands are preferred in scheduler scripts because they preserve the full invocation in the job record.

## 8. Slurm Example

```bash
#!/usr/bin/env bash
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --tmp=200G

set -euo pipefail
module load apptainer

apptainer exec \
  --bind "$SLURM_SUBMIT_DIR:/work" \
  --bind "/shared/beacon2-data:/beacon2-cbi-tools-data" \
  /shared/images/beacon2-cbi-tools.sif \
  bff-tools vcf -i /work/cohort.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  -c /work/config.yaml \
  -t "$SLURM_CPUS_PER_TASK" \
  -o /work/cohort-bff
```

Adjust wall time, memory, and scratch space to the cohort. `mem` in `config.yaml` controls only the Java heap and must remain below the scheduler memory request.

## Verification

```bash
apptainer exec beacon2-cbi-tools.sif bff-tools validate --help
apptainer exec beacon2-cbi-tools.sif bff-tools vcf --help
```

After binding the complete annotation bundle, run the repository's [full annotation integration test](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/annotation-data/#full-deployment-integration) before a production cohort.

## Common HPC Problems

- **Quota exceeded:** move `APPTAINER_CACHEDIR` and `APPTAINER_TMPDIR` to project storage.
- **Configured file not found:** bind every input, output, configuration, reference, and temporary path used inside the container.
- **SnpEff attempts a download:** set `data.dir` to the mounted local database path.
- **Permission denied:** ensure output and scratch bind sources are writable by the submitting user.
- **Killed by scheduler:** keep the Java heap below the requested memory and account for bcftools, compression, and filesystem cache.
- **Slow shared storage:** use node-local scratch for intermediates when site policy permits, then copy final output and provenance back to project storage.

Keep the image tag or checksum, annotation-bundle version, configuration, and scheduler script together in run provenance. Do not run full annotation jobs on login nodes.

## MongoDB

Apptainer provides no database service. Install MongoDB clients separately when needed and follow the [MongoDB import guide](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/reference/mongodb/).

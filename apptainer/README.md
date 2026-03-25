# Containerized Installation with Apptainer

This setup is intended for environments that use Apptainer or Singularity, including HPC systems. As with Docker, the large reference data stays outside the image.

## 1. Prepare external data

Work in a directory with at least 150 GB of free space:

```bash
wget https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/deploy/01_download_external_data.py
python3 01_download_external_data.py
md5sum -c data.tar.gz.md5
cat data.tar.gz.part-?? > data.tar.gz
tar -xzvf data.tar.gz
mkdir tmp
```

If Google Drive blocks the download, use the URL printed by the script and fetch the file manually.

Then edit:

```text
/path/to/downloaded/data/soft/NGSutils/snpEff_v5.0/snpEff.config
```

Set:

```text
data.dir = /beacon2-cbi-tools-data/soft/NGSutils/snpEff_v5.0/data
```

## 2. Pull the image

If your system uses environment modules:

```bash
module load apptainer
```

Then pull the image once:

```bash
apptainer pull beacon2-cbi-tools_latest.sif docker://manuelrueda/beacon2-cbi-tools:latest
```

## 3. Run the image

Interactive shell:

```bash
apptainer shell \
  --bind /absolute/path/to/beacon2-cbi-tools-data:/beacon2-cbi-tools-data \
  beacon2-cbi-tools_latest.sif
```

Direct command execution from the host:

```bash
alias bff-tools='apptainer exec --bind /absolute/path/to/beacon2-cbi-tools-data:/beacon2-cbi-tools-data beacon2-cbi-tools_latest.sif /usr/share/beacon2-cbi-tools/bin/bff-tools'
bff-tools
```

Example:

```bash
bff-tools vcf -i /beacon2-cbi-tools-data/chr22.Test.1000G.phase3.joint.vcf.gz \
  -p /beacon2-cbi-tools-data/param.yaml \
  --projectdir-override /beacon2-cbi-tools-data/my_test_dir
```

You can also set the project directory in the parameter file:

```yaml
projectdir: /beacon2-cbi-tools-data/my_test_dir
```

## 4. Writable temporary directories

If `/tmp` is restricted, bind a writable scratch directory:

```bash
apptainer shell \
  --bind /absolute/path/to/beacon2-cbi-tools-data:/beacon2-cbi-tools-data \
  --bind /absolute/path/to/tmp:/tmp \
  beacon2-cbi-tools_latest.sif
```

## 5. Test the deployment

```bash
cd deploy
bash 02_test_deployment.sh
```

## MongoDB note

Apptainer does not provide a `docker compose` equivalent. If you need `load` or `full`, run MongoDB outside the container and make sure `bin/config.yaml` points to the correct `mongodburi` and `mongosh`.

## Runtime note

The image includes the core Python and Perl dependencies needed by `bff-tools` and `validate`. Optional utilities under `utils/` and the MkDocs toolchain are not included by default.

## System requirements

- `linux/amd64` or `linux/arm64`
- Apptainer or Singularity
- at least 4 GB RAM, ideally more
- at least 200 GB of disk space for the full data setup

## Cleanup

Remove the image:

```bash
rm beacon2-cbi-tools_latest.sif
```

Remove downloaded data:

```bash
rm -rf /absolute/path/to/beacon2-cbi-tools-data
```

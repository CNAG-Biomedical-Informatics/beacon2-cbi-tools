# Containerized Installation with Docker

This setup keeps the large reference data outside the container. Prepare that data once, then mount it into the image when you run `bff-tools`.

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

```bash
docker pull manuelrueda/beacon2-cbi-tools:latest
docker image tag manuelrueda/beacon2-cbi-tools:latest cnag/beacon2-cbi-tools:latest
```

## 3. Run the container

```bash
docker run -tid \
  --volume /absolute/path/to/beacon2-cbi-tools-data:/beacon2-cbi-tools-data \
  --name beacon2-cbi-tools \
  cnag/beacon2-cbi-tools:latest
```

Open a shell:

```bash
docker exec -ti beacon2-cbi-tools bash
```

Or call the main tool directly:

```bash
alias bff-tools='docker exec -ti beacon2-cbi-tools /usr/share/beacon2-cbi-tools/bin/bff-tools'
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

## 4. Optional: build locally

If you want to build the image yourself:

```bash
wget https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/docker/Dockerfile
docker buildx build -t cnag/beacon2-cbi-tools:latest .
```

If `buildx` is not available, use `docker build`.

## 5. Optional: run the full stack with Compose

To start `beacon2-cbi-tools`, MongoDB, and Mongo Express together:

```bash
wget https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/docker/docker-compose.all.yml
docker compose -f docker-compose.all.yml up -d
```

Make sure the compose file points to your external data directory, for example through `BEACON2_DATA_DIR`.

## 6. Test the deployment

```bash
cd deploy
bash 02_test_deployment.sh
```

## MongoDB note

If you are not using `docker-compose.all.yml`, start MongoDB separately and make sure the paths in `bin/config.yaml` match your environment. If the container must reach an external MongoDB service, place both on the same Docker network.

## Runtime note

The container already includes the core Python and Perl dependencies needed by `bff-tools` and `validate`. The MkDocs documentation toolchain is not included.

## System requirements

- `linux/amd64` or `linux/arm64`
- Docker and Docker Compose
- at least 4 GB RAM, ideally more
- at least 200 GB of disk space for the full data setup

## Troubleshooting

If image builds fail with DNS or package resolution errors, fix Docker host networking first and retry the build.

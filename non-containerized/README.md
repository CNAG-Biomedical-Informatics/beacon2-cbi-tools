# Non-containerized Installation

Use this path if you want to run `beacon2-cbi-tools` directly on the host without Docker or Apptainer.

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
data.dir = /path/to/downloaded/data/soft/NGSutils/snpEff_v5.0/data
```

## 2. Install system packages

```bash
sudo apt install git wget gcc make libperl-dev libbz2-dev zlib1g-dev libncurses5-dev libncursesw5-dev liblzma-dev libcurl4-openssl-dev libssl-dev cpanminus perl python3 python3-pip default-jre
```

If you plan to use MongoDB loading, install `mongosh` as well.

## 3. Clone the repository

```bash
git clone https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools.git
cd beacon2-cbi-tools
```

To update an existing checkout later:

```bash
git pull
```

## 4. Install Python and Perl dependencies

Core Python dependencies:

```bash
pip install -r requirements.txt
```

Core Perl dependencies:

```bash
cpanm --notest --installdeps .
```

Optional utility dependencies:

```bash
pip install -r utils/bff_browser/requirements.txt
cpanm --notest Mojolicious MongoDB Minion Minion::Backend::SQLite
```

Documentation dependencies:

```bash
pip install -r requirements-docs.txt
```

## 5. Configure the toolkit

Update `bin/config.yaml` so that:

- `base` points to the directory where you unpacked the external data
- `mongosh` points to the correct executable on your system

## 6. Test the deployment

```bash
cd deploy
bash 02_test_deployment.sh
```

Installing `jq` may help when running the test scripts.

## System requirements

- `linux/amd64` or `linux/arm64`
- Python 3.8+
- Perl 5
- at least 4 GB RAM, ideally more
- at least 200 GB of disk space for the full data setup

## Troubleshooting

If Python modules are missing, rerun:

```bash
pip install -r requirements.txt
```

If Perl modules are missing, rerun:

```bash
cpanm --notest --installdeps .
```

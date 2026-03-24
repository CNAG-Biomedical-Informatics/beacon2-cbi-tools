# Containerized Installation (Apptainer / Singularity)

## Downloading Required Databases and Software

First, we need to download the necessary databases and software. As with the Docker-based setup, the data lives outside the container. This improves data persistence and allows software updates without requiring a full re-download of all data.

### Step 1: Download Required Files

Navigate to a directory with at least **150GB** of available space and run:

```bash
wget https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/scripts/01_download_external_data.py
```

Then execute the script:

```bash
python3 01_download_external_data.py
```

> **Note:** Google Drive can sometimes restrict downloads. If you encounter an error, use the provided error URL in a browser to retrieve the file manually.

### Step 2: Verify Download Integrity

Run a checksum to ensure the files were not corrupted:

```bash
md5sum -c data.tar.gz.md5
```

### Step 3: Reassemble Split Files

The downloaded data is split into parts. Reassemble it into a single tar archive (**~130GB required**):

```bash
cat data.tar.gz.part-?? > data.tar.gz
```

Once the files are successfully merged, delete the split parts to free up space:

```bash
rm data.tar.gz.part-??
```

### Step 4: Extract Data

Extract the tar archive:

```bash
tar -xzvf data.tar.gz
```

Make sure a `tmp` directory exists in the directory where you extracted your data:

```bash
mkdir tmp
```

### Step 5: Configure Path in SnpEff

1. Navigate to your downloaded data and locate the **SnpEff configuration file**. It is located at:

```bash
/path/to/downloaded/data/soft/NGSutils/snpEff_v5.0/snpEff.config
```

2. Open `snpEff.config` with a text editor and find the line containing the `data.dir` variable.

3. Update the `data.dir` variable to match the directory path where you plan to mount the data (recommended: `/beacon2-cbi-tools-data/`). It should look like this:

```bash
data.dir = /beacon2-cbi-tools-data/soft/NGSutils/snpEff_v5.0/data
```

## Installation Options

### Method 1: Pull from Docker Hub with Apptainer

If your HPC system uses environment modules, load Apptainer first:

```bash
module load apptainer
```

Then pull the latest image from Docker Hub and save it as a local `.sif` file:

```bash
apptainer pull beacon2-cbi-tools_latest.sif docker://manuelrueda/beacon2-cbi-tools:latest
```

This command only needs to be run once.

---

### Method 2: Run Directly from Docker Hub

Apptainer can also execute the Docker image directly without creating a persistent `.sif` file in the current directory:

```bash
apptainer shell docker://manuelrueda/beacon2-cbi-tools:latest
```

This is convenient for quick tests, but for reproducible workflows or batch jobs, pulling the image explicitly is the better option.

---

## Runtime Note

Inside the container, the core Python and Perl runtime dependencies needed by `bff-tools` and `validate` are already provided. Optional utilities under `utils/` and the MkDocs documentation toolchain are not installed by default.

## Running and Interacting with the Container

Apptainer images are read-only, so bind your external data directory when launching the container.

### Interactive shell

```bash
# Please update '/absolute/path/to/beacon2-cbi-tools-data' with your actual local data path
apptainer shell \
  --bind /absolute/path/to/beacon2-cbi-tools-data:/beacon2-cbi-tools-data \
  beacon2-cbi-tools_latest.sif
```

### Run tools directly from the host

```bash
alias bff-tools='apptainer exec --bind /absolute/path/to/beacon2-cbi-tools-data:/beacon2-cbi-tools-data beacon2-cbi-tools_latest.sif /usr/share/beacon2-cbi-tools/bin/bff-tools'
bff-tools
```

Example run:

```bash
bff-tools vcf -i /beacon2-cbi-tools-data/chr22.Test.1000G.phase3.joint.vcf.gz  \
              -p /beacon2-cbi-tools-data/param.yaml \
              --projectdir-override /beacon2-cbi-tools-data/my_test_dir
```

Note: You can also set the path for the projectdir via parameters file.

```yaml
projectdir: /beacon2-cbi-tools-data/my_test_dir
```

### Writable temporary directories

If your HPC environment restricts `/tmp`, you may need to bind a writable scratch directory as well:

```bash
apptainer shell \
  --bind /absolute/path/to/beacon2-cbi-tools-data:/beacon2-cbi-tools-data \
  --bind /absolute/path/to/tmp:/tmp \
  beacon2-cbi-tools_latest.sif
```

### Test the Deployment

```bash
cd scripts
bash 02_test_deployment.sh
```

## MongoDB: External Setup

Apptainer does not provide an equivalent to `docker compose`. If you want to use `load` mode against MongoDB, run MongoDB outside the container and make sure the `mongodburi` and `mongosh` paths in `bin/config.yaml` point to your environment.

If `mongosh` is available on the host and bind-mounted into the container environment, `bff-tools load` and `bff-tools full` can use it normally.

## System requirements

- OS/ARCH supported: **linux/amd64** and **linux/arm64**.
- Ideally a Debian-based distribution (Ubuntu or Mint), but any other (e.g., CentOS, OpenSUSE) should do as well (untested).
- Apptainer or Singularity
- 4GB of RAM (ideally 16GB).
- \>= 1 core (ideally i7 or Xeon).
- At least 200GB HDD.

The `bff-tools` wrapper itself does not need a lot of RAM, but external tools do (e.g., process `mongod` [MongoDB's daemon]).

## Notes

- Apptainer images (`.sif`) are regular files on disk.
- User data and configuration should remain outside the container.
- For HPC batch systems such as Slurm, prefer using a pulled `.sif` image rather than running directly from Docker Hub.

## Cleaning Up

To remove the image:

```bash
rm beacon2-cbi-tools_latest.sif
```

To remove the externally downloaded data:

```bash
rm -rf /absolute/path/to/beacon2-cbi-tools-data
```

## References

1. BCFtools
    Danecek P, Bonfield JK, et al. Twelve years of SAMtools and BCFtools. Gigascience (2021) 10(2):giab008 [link](https://pubmed.ncbi.nlm.nih.gov/33590861)

2.  SnpEff
    "A program for annotating and predicting the effects of single nucleotide polymorphisms, SnpEff: SNPs in the genome of Drosophila melanogaster strain w1118; iso-2; iso-3.", Cingolani P, Platts A, Wang le L, Coon M, Nguyen T, Wang L, Land SJ, Lu X, Ruden DM. Fly (Austin). 2012 Apr-Jun;6(2):80-92. PMID: 22728672.

3. SnpSift
    "Using Drosophila melanogaster as a model for genotoxic chemical mutational studies with a new program, SnpSift", Cingolani, P., et. al., Frontiers in Genetics, 3, 2012. PMID: 22435069.
4.  dbNSFP v4
    1. Liu X, Jian X, and Boerwinkle E. 2011. dbNSFP: a lightweight database of human non-synonymous SNPs and their functional predictions. Human Mutation. 32:894-899.
    2. Liu X, Jian X, and Boerwinkle E. 2013. dbNSFP v2.0: A Database of Human Non-synonymous SNVs and Their Functional Predictions and Annotations. Human Mutation. 34:E2393-E2402.
    3. Liu X, Wu C, Li C, and Boerwinkle E. 2016. dbNSFP v3.0: A One-Stop Database of Functional Predictions and Annotations for Human Non-synonymous and Splice Site SNVs. Human Mutation. 37:235-241.
    4. Liu X, Li C, Mou C, Dong Y, and Tu Y. 2020. dbNSFP v4: a comprehensive database of transcript-specific functional predictions and annotations for human nonsynonymous and splice-site SNVs. Genome Medicine. 12:103.

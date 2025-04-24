# Containerized Installation

## Downloading Required Databases and Software

First, we need to download the necessary databases and software. In contrast to `beacon2-ri-tools`, where **the data was bundled inside the container to provide a zero-configuration experience for users, we now store the data externally**. This change improves data persistence and allows software updates without requiring a full re-download of all data.

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

### Step 5: Configure Path in SnpEff

1. Navigate to your downloaded data and locate the **SnpEff configuration file**. It is located at:

```bash
/path/to/downloaded/data/soft/NGSutils/snpEff_v5.0/snpEff.config
```

2. Open `snpEff.config` with a text editor and find the line containing the `data.dir` variable.

3. Update the `data.dir` variable to reflect the correct path to your downloaded data directory. It should look similar to this:

```bash
data.dir = /path/to/downloaded/data/soft/NGSutils/snpEff_v5.0/data
```

**Important:** Ensure that you use an absolute path and verify that the directory exists to avoid any errors during subsequent analyses.

---

## Installation Options

### Method 1: Installing from Docker Hub

Pull the latest Docker image from [Docker Hub](https://hub.docker.com/r/manuelrueda/beacon2-cbi-tools):

```bash
docker pull manuelrueda/beacon2-cbi-tools:latest
docker image tag manuelrueda/beacon2-cbi-tools:latest cnag/beacon2-cbi-tools:latest
```

---

### Method 2: Installing from Dockerfile

Download the `Dockerfile` from [GitHub](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/blob/main/Dockerfile):

```bash
wget https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/docker/Dockerfile
```

Then build the container:

- **For Docker version 19.03 and above (supports buildx):**

  ```bash
  docker buildx build -t cnag/beacon2-cbi-tools:latest .
  ```

- **For Docker versions older than 19.03 (no buildx support):**

  ```bash
  docker build -t cnag/beacon2-cbi-tools:latest .
  ```

---

### Method 3: Full Stack with Docker Compose

We now provide an extended Docker Compose file (`docker-compose.all.yml`) to launch **beacon2-cbi-tools**, **MongoDB**, and **Mongo Express** together in one command. This is recommended if you're deploying the full data-loading and querying stack.


1. **Download** `docker-compose.yml`

```bash
wget https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/docker/docker-compose.all.yml
```


2. **Configure the Data Directory**

   Ensure you have a directory containing the required data for beacon2-cbi-tools. You can set this directory in the compose file using an environment variable or by editing the volume mapping directly. For example, the volume is defined as:

   ```yaml
   volumes:
     - ${BEACON2_DATA_DIR:-/absolute/path/to/beacon2-cbi-tools-data}:/beacon2-cbi-tools-data
   ```

   You can set the `BEACON2_DATA_DIR` variable in a `.env` file or in your shell, or replace the default path with the actual absolute path.

3. **Deploy the Complete Stack**

   Run the following command from your project directory:

   ```bash
   docker compose -f docker-compose.all.yml up -d
   ```

   This command will pull the required images from Docker Hub (if not available locally) and start containers for MongoDB, Mongo Express, and beacon2-cbi-tools, all connected on the same network.

4. **Verify and Interact**

   Check that all containers are running with:

   ```bash
   docker ps
   ```

   You can then connect to the beacon2-cbi-tools container or interact with the services as needed.

---

## Running and Interacting with the Container

### 🔹 If You Used Method 1 or 2 (Docker Hub or Dockerfile)

```bash
# Please update '/absolute/path/to/beacon2-cbi-tools-data' with your actual local data path
docker run -tid --volume /absolute/path/to/beacon2-cbi-tools-data:/beacon2-cbi-tools-data --name beacon2-cbi-tools cnag/beacon2-cbi-tools:latest
```

To connect to the container:

```bash
docker exec -ti beacon2-cbi-tools bash
```

Or, to run tools directly from the host:

```bash
alias bff-tools='docker exec -ti beacon2-cbi-tools /usr/share/beacon2-cbi-tools/bin/bff-tools'
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


---

### 🔹 If You Used Method 3 (Docker Compose)

Your container should already be running if you used:

```bash
docker compose -f docker-compose.all.yml up -d
```

To connect:

```bash
docker exec -ti beacon2-cbi-tools bash
```

To run tools from the host (optional):

```bash
alias bff-tools='docker exec -ti beacon2-cbi-tools /usr/share/beacon2-cbi-tools/bin/bff-tools'
bff-tools
```

---

### ✅ Test the Deployment

```bash
cd test
bash 02_test_deployment.sh
```

---

## MongoDB: Manual Setup (Optional)

> ⚠️ This section is only needed if you're **not** using `docker-compose.all.yml`, or want to run MongoDB manually.

### Step 1: Download `docker-compose.yml`

```bash
wget https://raw.githubusercontent.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/main/docker/docker-compose.yml
```

### Step 2: Start MongoDB

```bash
docker network create my-app-network
docker compose up -d
```

Mongo Express will be accessible at `http://localhost:8081` with default credentials `admin` and `pass`.

> **IMPORTANT:** If you plan to load data into MongoDB from inside the `beacon2-cbi-tools` container, read the section below.

### Access MongoDB from Inside the Container

#### Option A: Before running the container

```bash
docker run -tid --network=my-app-network --volume /media/mrueda/4TBB/beacon2-cbi-tools-data:/beacon2-cbi-tools-data --name beacon2-cbi-tools cnag/beacon2-cbi-tools:latest
```

#### Option B: After running the container

```bash
docker network connect my-app-network beacon2-cbi-tools
```

---

## System requirements

- OS/ARCH supported: **linux/amd64** and **linux/arm64**.
- Ideally a Debian-based distribution (Ubuntu or Mint), but any other (e.g., CentOS, OpenSUSE) should do as well (untested).
- Docker and docker compose
- Perl 5 (>= 5.10 core; installed by default in most Linux distributions). Check the version with perl -v
- 4GB of RAM (ideally 16GB).
- \>= 1 core (ideally i7 or Xeon).
- At least 200GB HDD.

Perl itself does not require much RAM (max load ~400MB), but external tools (e.g., `mongod` [MongoDB's daemon]) do.

---

## Common errors: Symptoms and treatment

  * Dockerfile:

          * DNS errors

            - Error: Temporary failure resolving 'foo'

              Solution: https://askubuntu.com/questions/91543/apt-get-update-fails-to-fetch-files-temporary-failure-resolving-error
---

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

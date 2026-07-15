#!/bin/bash

#SBATCH --job-name=beacon2-cbi-tools
#SBATCH -q short
#SBATCH -D /software/biomed/test
#SBATCH -e /software/biomed/test/slurm-%N.%j.err
#SBATCH -o /software/biomed/test/slurm-%N.%j.out
#SBATCH -c 1
#SBATCH -t 00:10:00
#SBATCH --mem 8000
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=manuel.rueda@cnag.eu

# Optional
cd /software/biomed/test

# use a simple ASCII locale
export LANG=C
export LC_ALL=C

# Mandatory set up for modules
module load BCFtools/1.17-GCC-12.2.0
export PYTHONPATH="/software/biomed/cbi_py3/lib/python3.10/site-packages:${PYTHONPATH}"

# Variable definition
BFFTOOLS_DIR="/software/biomed/beacon2-cbi-tools"
BFFTOOLS="$BFFTOOLS_DIR/bin/bff-tools"
export BFF_TOOLS_DATA="/software/biomed/beacon2-cbi-tools-data"

# Job execution
"$BFFTOOLS" test \
    --threads 1 \
    --output-dir "bff-tools-integration-${SLURM_JOB_ID}"

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
module load Perl/5.36.0-GCCcore-12.2.0
module load BCFtools/1.17-GCC-12.2.0
eval "$(perl -Mlocal::lib=/software/biomed/cbi_perl5)"

# Variable definition
BFFTOOLS_DIR="/software/biomed/beacon2-cbi-tools"
BFFTOOLS="$BFFTOOLS_DIR/bin/bff-tools"
INPUT="$BFFTOOLS_DIR/test/vcf/test_1000G.vcf.gz"
PARAM="$BFFTOOLS_DIR/test/vcf/param.yaml"
CONFIG="$BFFTOOLS_DIR/bin/cnag-hpc-config.yaml"

# Job execution
"$BFFTOOLS" vcf \
    -i "$INPUT" \
    -p "$PARAM" \
    -c "$CONFIG" \
    --no-color \
    --no-emoji \
    -t 1

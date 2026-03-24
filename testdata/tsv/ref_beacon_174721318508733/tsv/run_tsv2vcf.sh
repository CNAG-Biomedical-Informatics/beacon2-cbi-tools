#!/usr/bin/env bash
#
#   Script that generates VCF format from TSV
#
#   Last Modified: Mar/17/2025
#
#   Version taken from $BEACON
#
#   Copyright (C) 2023-2025 Manuel Rueda - CNAG (manuel.rueda@cnag.eu)
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <https://www.gnu.org/licenses/>.
#
#   If this program helps you in your research, please cite.

set -euo pipefail
export LC_ALL=C

export TMPDIR=/media/mrueda/2TBS/tmp
ZIP='/usr/bin/pigz -p 11'
BCFTOOLS=/media/mrueda/2TBS/NGSutils/bcftools-1.21-103_x86_64/bcftools
SAMPLE_ID=23andme_1
GENOME='hg19'
REF=/media/mrueda/2TBS/Databases/genomes/hs37d5.fa.gz
DATASETID=default_beacon_1
PROJECTDIR=beacon_174721318508733

function usage {
    echo "Usage: $0 <input_tsv.gz>"
    exit 1
}

# Check if the arguments are provided
if [ $# -lt 1 ]; then
    usage
fi

# Load input arguments
INPUT_TSV=$1
BASE=$(basename "$INPUT_TSV" .vcf.gz)

echo "# Running bcftools convert --tsv2vcf"
# 23andMe outputs alleles alphabetically, so unphased hets may appear as 0/1 or 1/0
$BCFTOOLS convert --tsv2vcf "$INPUT_TSV" -f "$REF" -s "$SAMPLE_ID" -Oz -o "$SAMPLE_ID.vcf.gz"

echo "# Filtering empty ALT"
$BCFTOOLS view -e 'ALT="."' "$SAMPLE_ID.vcf.gz" -Oz -o "$SAMPLE_ID.filtered.vcf.gz"

echo "# Finished OK"

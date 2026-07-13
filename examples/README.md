# Worked Examples

The runnable inputs, parameter file, and HPC example are kept in the repository's [`examples/` directory](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/examples).

## GRCh38 / hg38

The repository includes `test_1000G_hg38.vcf.gz`, a compact, multisample 1000 Genomes-derived input. It uses GRCh38 coordinates with UCSC-style `chr22` contigs.

### Run the Included Input

Prepare the external annotation data and update `../bin/config.yaml`, then run from `examples/`:

```bash
../bin/bff-tools vcf \
  -i test_1000G_hg38.vcf.gz \
  -p param_hg38.yaml \
  -c ../bin/config.yaml \
  -o example-hg38
```

`param_hg38.yaml` selects `hg38` and enables annotation. The pipeline normalizes the VCF and applies SnpEff, dbNSFP, ClinVar, and COSMIC before conversion.

The primary result is:

```text
example-hg38/vcf/genomicVariationsVcf.json.gz
```

Validate it and optionally generate the standalone report:

```bash
../bin/bff-tools validate \
  -i example-hg38/vcf/genomicVariationsVcf.json.gz --gv-vcf

../bin/bff-tools vcf \
  -i test_1000G_hg38.vcf.gz \
  -p param_hg38.yaml \
  -c ../bin/config.yaml \
  --browser \
  -o example-hg38-browser
```

Run directories are not overwritten. Use a new `-o` value for each attempt.

### Recreate the Input Subset

The source is the 2,504-sample chromosome 22 GRCh38 callset from the 1000 Genomes Project. One maintained mirror is the [UCSC 1000 Genomes directory](https://hgdownload.soe.ucsc.edu/gbdb/hg38/1000Genomes/).

Download and index the chromosome file:

```bash
wget https://hgdownload.soe.ucsc.edu/gbdb/hg38/1000Genomes/ALL.chr22.shapeit2_integrated_snvindels_v2a_27022019.GRCh38.phased.vcf.gz

bcftools index -t \
  ALL.chr22.shapeit2_integrated_snvindels_v2a_27022019.GRCh38.phased.vcf.gz
```

The source records use contig `22`, while the configured hg38 resources use `chr22`. Subset the original coordinates and rename the contig with bcftools:

```bash
printf '22\tchr22\n' > rename-chrs.txt

bcftools view \
  -r 22:10516173-11016173 \
  -Ou \
  ALL.chr22.shapeit2_integrated_snvindels_v2a_27022019.GRCh38.phased.vcf.gz \
  | bcftools annotate --rename-chrs rename-chrs.txt \
      -Oz -o test_1000G_hg38.vcf.gz

bcftools index -t test_1000G_hg38.vcf.gz
```

This is a contig-name normalization within the same GRCh38 coordinate system. It is not a liftover. Preserve the source URL, checksum, region, rename map, and commands with any regenerated fixture.

### Use Existing Compatible Annotations

To skip re-annotation, the VCF must already contain a compatible SnpEff `ANN` header and annotations:

```bash
../bin/bff-tools vcf \
  -i cohort.hg38.annotated.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  --no-annotate \
  -o cohort-hg38-bff
```

dbNSFP and ClinVar fields remain strongly recommended for complete BFF output.

## GRCh37 / hs37

Compact GRCh37 fixtures and Perl-generated reference outputs are under [`testdata/vcf`](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/testdata/vcf). Use `hs37` for hs37d5-style contigs such as `22`; use `hg19` only with matching hg19 coordinates, contigs, FASTA, and annotation resources.

## Metadata

The populated [CINECA synthetic cohort](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/CINECA_synthetic_cohort_EUROPE_UK1) is the real-world metadata example. It accompanies the packaged workbook template and serves as the 10,018-record validator parity fixture.

Full VCF release acceptance uses an external, fully annotated CINECA chromosome 22 file with 2,504 samples. That full file is not committed to Git or included in the PyPI package.

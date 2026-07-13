# Test Data and Reproducible Examples

This directory contains compact inputs and expected outputs for VCF-to-BFF, TSV-to-VCF-to-BFF, validator, and browser regression tests. These files are small enough for normal development and CI; the full CINECA chromosome 22 acceptance input remains outside Git.

## Before Running the Raw Inputs

Both `testdata/vcf/test_1000G.vcf.gz` and `testdata/tsv/input.txt.gz` require annotation. Prepare the external annotation bundle and ensure `bin/config.yaml` points to its FASTA, SnpEff, SnpSift, dbNSFP, ClinVar, and COSMIC resources.

Run commands from a fresh checkout or choose output paths that do not already exist.

## GRCh37 / hs37 VCF

`vcf/test_1000G.vcf.gz` is a compact 1000 Genomes Phase 3 chromosome 1 subset using hs37-style contigs.

From `testdata/vcf/`:

```bash
../../bin/bff-tools vcf \
  -i test_1000G.vcf.gz \
  -p param.yaml \
  -c ../../bin/config.yaml \
  --no-browser \
  -o local-hs37-test
```

Validate the generated collection:

```bash
../../bin/bff-tools validate \
  -i local-hs37-test/vcf/genomicVariationsVcf.json.gz \
  --gv-vcf
```

Compare it semantically with the Perl-generated reference while ignoring only run-specific provenance and the two legacy hash-order arrays:

```bash
python3 ../../tools/compare_bff_outputs.py \
  ref_beacon_166403275914916/vcf/genomicVariationsVcf.json.gz \
  local-hs37-test/vcf/genomicVariationsVcf.json.gz
```

The historical source region can be recreated from the 1000 Genomes GRCh37 release:

```bash
wget https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz
wget https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz.tbi

bcftools view -r 1:10000-200000 \
  -Oz -o test_1000G.vcf.gz \
  ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz
```

Record a checksum whenever the fixture is regenerated.

## SNP-Array TSV

`tsv/input.txt.gz` exercises the supported SNP-array/23andMe-style path. It is first converted with bcftools, filtered for missing ALT alleles, annotated, and then mapped to BFF.

From `testdata/tsv/`:

```bash
../../bin/bff-tools tsv \
  -i input.txt.gz \
  -p param.yaml \
  -c ../../bin/config.yaml \
  -o local-tsv-test

python3 ../../tools/compare_bff_outputs.py \
  ref_beacon_174721318508733/vcf/genomicVariationsVcf.json.gz \
  local-tsv-test/vcf/genomicVariationsVcf.json.gz
```

TSV conversion cannot use `--no-annotate` because its VCF intermediate does not contain SnpEff ANN data.

## Fully Annotated Parity Fixtures

- `vcf/ref_beacon_166403275914916/` contains the compact fully annotated 1000 Genomes input and Perl-generated BFF expected output.
- `vcf/cineca_annotated/` contains 5,002 fully annotated source records with all 2,504 CINECA samples and a 4,998-record Perl-generated BFF expected output.

These fixtures test ANN, dbNSFP, ClinVar, COSMIC, SNVs, indels, missing genotypes, homozygous alternate calls, and large multi-sample lines without committing the full chromosome.

## Automated Tests

```bash
pytest -q tests/test_vcf_conversion.py tests/test_vcf_parity.py
```

The full release gate additionally compares every emitted record from the external CINECA chromosome 22 input. See the documentation's Validation and Trust page for the acceptance criteria.

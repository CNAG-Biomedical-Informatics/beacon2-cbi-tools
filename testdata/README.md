# Test Data and Reproducible Examples

This directory contains compact inputs and expected outputs for TSV-to-VCF-to-BFF, validator, and browser regression tests. The GRCh37 VCF integration fixture is packaged under `src/bff_tools/integration_assets/` so the installed `bff-tools test` command and repository tests use the same files. The full CINECA chromosome 22 acceptance input remains outside Git.

## Before Running the Raw Inputs

The packaged `test_1000G.vcf.gz` and `testdata/tsv/input.txt.gz` require annotation. Prepare the external annotation bundle and select it with `BFF_TOOLS_DATA`.

Run commands from a fresh checkout or choose output paths that do not already exist.

## GRCh37 / hs37 VCF

`src/bff_tools/integration_assets/test_1000G.vcf.gz` is a compact 1000 Genomes Phase 3 chromosome 1 subset using hs37-style contigs. Run its complete annotation, validation, and semantic-parity contract through the installed CLI:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools test
```

Pass `--output-dir local-hs37-test` to retain the generated project for inspection. The command validates the output and compares it semantically with the versioned reference BFF output while ignoring only run-specific provenance and the two legacy hash-order arrays.

The historical source region can be recreated from the 1000 Genomes GRCh37 release:

```bash
wget https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz
wget https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz.tbi

bcftools view -r 1:10000-200000 \
  -Oz -o src/bff_tools/integration_assets/test_1000G.vcf.gz \
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

bff-tools compare \
  --expected ref_beacon_174721318508733/vcf/genomicVariationsVcf.json.gz \
  --actual local-tsv-test/vcf/genomicVariationsVcf.json.gz
```

TSV conversion cannot use `--no-annotate` because its VCF intermediate does not contain SnpEff ANN data.

## Fully Annotated Parity Fixtures

- `src/bff_tools/integration_assets/` contains the compact raw and fully annotated 1000 Genomes inputs plus the Perl-generated BFF expected output.
- `vcf/cineca_annotated/` contains 5,002 fully annotated source records with all 2,504 CINECA samples and a 4,998-record Perl-generated BFF expected output.

These fixtures test ANN, dbNSFP, ClinVar, COSMIC, SNVs, indels, missing genotypes, homozygous alternate calls, and large multi-sample lines without committing the full chromosome.

## Automated Tests

```bash
pytest -q tests/test_vcf_conversion.py tests/test_vcf_parity.py
```

The full release gate additionally compares every emitted record from the external CINECA chromosome 22 input. See the documentation's Validation and Trust page for the acceptance criteria.

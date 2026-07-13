# Fully Annotated VCF Migration Fixture

This fixture is extracted from:

```text
CINECA_synthetic_cohort_EUROPE_UK1/vcf/
  cineca_uk1_174687799538538/vcf/
  chr22.Test.1000G.phase3.joint.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz
```

It is not a synthetic hand-written VCF. It retains complete headers, full ANN/dbNSFP/ClinVar/COSMIC annotation fields, and all 2,504 sample columns from the real CINECA-derived input.

The compact file contains 5,000 consecutive records plus later targeted records for dense dbNSFP and pathogenic ClinVar behavior. Targeted coverage and current symbolic-allele behavior are recorded in `manifest.json`.

## Regenerate the Input

```bash
python3 tools/extract_annotated_vcf_fixture.py \
  /path/to/chr22.Test.1000G.phase3.joint.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz \
  testdata/vcf/cineca_annotated/fully_annotated.vcf.gz \
  testdata/vcf/cineca_annotated/manifest.json \
  --baseline-records 5000
```

## Regenerate the Perl Baseline

The retired converter is not part of the current package. Check out the
pre-migration implementation in a temporary worktree, as described in
[`tools/README.md`](../../../tools/README.md), then run:

```bash
perl /tmp/beacon2-cbi-tools-perl-oracle/pipeline/internal/complete/vcf2bff.pl \
  --input testdata/vcf/cineca_annotated/fully_annotated.vcf.gz \
  --genome hg19 \
  --dataset-id CINECA_synthetic_cohort_EUROPE_UK1 \
  --project-dir cineca_annotated_fixture \
  --out-dir testdata/vcf/cineca_annotated \
  --threads 1
```

## Current Parity Gate

The normal test suite converts this fixture with Python and compares all 4,998
emitted records with the committed Perl-generated BFF output:

```bash
pytest -q tests/test_vcf_conversion.py \
  -k cineca_annotated_converter_matches_perl_generated_bff
```

Release acceptance additionally compares the complete 1,110,240-record chr22
source against the preserved Perl output. Both gates use strict semantic and
type-sensitive comparison; only run-specific converter provenance and the two
arrays whose order depended on Perl hash seeding are normalized.

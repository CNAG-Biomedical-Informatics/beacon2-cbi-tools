# Maintainer checks

## Full CINECA chr22 VCF parity

The release acceptance input and both full outputs are kept outside Git under
`/media/mrueda/2TBS/CNAG/Project_Beacon/CINECA`. Rerun Python and compare it
with the preserved Perl golden output:

```bash
SOURCE=/media/mrueda/2TBS/CNAG/Project_Beacon/CINECA/CINECA_synthetic_cohort_EUROPE_UK1/vcf/cineca_uk1_174687799538538/vcf/chr22.Test.1000G.phase3.joint.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz
PARITY=/media/mrueda/2TBS/CNAG/Project_Beacon/CINECA/beacon2-cbi-tools-parity

mkdir -p "$PARITY/python"
/usr/bin/time -v python3 src/bff_tools/vcf_converter.py \
  --input "$SOURCE" --genome hg19 \
  --dataset-id CINECA_synthetic_cohort_EUROPE_UK1 \
  --project-dir cineca_chr22 --out-dir "$PARITY/python" --threads 1

PYTHONPATH=src python3 tools/compare_bff_outputs.py \
  "$PARITY/perl/genomicVariationsVcf.json.gz" \
  "$PARITY/python/genomicVariationsVcf.json.gz"
```

To regenerate both outputs, read the legacy converter from the pre-migration
commit in a temporary worktree:

```bash
git worktree add /tmp/beacon2-cbi-tools-perl-oracle 8c13235
cpanm --notest JSON::XS Path::Tiny YAML::XS PerlIO::gzip \
  Data::Structure::Util List::MoreUtils

PYTHONPATH=src python3 tools/compare_vcf_converters.py \
  --perl-converter /tmp/beacon2-cbi-tools-perl-oracle/pipeline/internal/complete/vcf2bff.pl \
  --fixture /media/mrueda/2TBS/CNAG/Project_Beacon/CINECA/CINECA_synthetic_cohort_EUROPE_UK1/vcf/cineca_uk1_174687799538538/vcf/chr22.Test.1000G.phase3.joint.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz
```

The command runs both converters independently, streams their BFF output, and
reports the first unequal record. It ignores only run-specific `_info.vcf2bff`
provenance and normalizes the two arrays whose order varied with Perl hash
seeding.

A direct `sha256sum` is a useful fast gate only when the compared artifacts are
expected to be byte-for-byte deterministic. The Perl and Python gzip streams
can differ in compression details, provenance, and order-insensitive arrays, so
the migration gate must use the semantic comparator. After the Python output
becomes the sole golden artifact, retain its SHA-256 checksum for exact
regression checks and run the comparator only when a checksum differs and a
record-level diagnosis is needed.

Remove the worktree after the comparison:

```bash
git worktree remove /tmp/beacon2-cbi-tools-perl-oracle
```

## Validator golden output

The CINECA workbook test compares all six generated collections byte-for-byte
with the committed Perl-generated output:

```bash
pytest -q tests/test_validator.py \
  -k perl_generated_bff_byte_for_byte
```

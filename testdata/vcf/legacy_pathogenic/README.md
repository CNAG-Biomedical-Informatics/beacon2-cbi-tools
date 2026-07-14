# Legacy Pathogenic VCF Regression Fixture

This compact fixture preserves the production BFF regression case that was
previously exercised by `pipeline/internal/complete/t/03-vcf2bff.t`.

The files were restored from revision
`8c132350a97fe5fb65e4f9b1537ce168c81594a5`, immediately before the legacy
Perl pipeline was removed in commit `38a68cd`:

- `test_pathogenic.vcf.gz` is the fully annotated input VCF.
- `genomicVariationsVcf.json.gz` is the Perl-generated production BFF output.

The Python regression test converts all 15 records with the original test
parameters and performs the same type-sensitive semantic comparison used by
the larger migration fixtures. Run it with:

```bash
python -m unittest \
  tests.test_vcf_conversion.VcfConversionTests.test_legacy_pathogenic_fixture_matches_perl_and_schema \
  -v
```

The obsolete developer-only `json` and `bff-pretty` outputs have deliberately
not been restored.

## Checksums

```text
438c3465cd18822742e3f820b96a3eb4e86d9f222ab89a7a7a4a799868f5163b  test_pathogenic.vcf.gz
9bd4c9163f080d76a63b3342305eebcb60b4e66bae9597f640301797f83cb7d5  genomicVariationsVcf.json.gz
```

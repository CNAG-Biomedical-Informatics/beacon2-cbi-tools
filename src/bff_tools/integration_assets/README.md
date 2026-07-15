# Packaged Annotation Integration Fixture

This directory contains the compact GRCh37/hs37 fixture used by
`bff-tools test` and by the VCF conversion regression tests.

- `test_1000G.vcf.gz` is an unannotated 1000 Genomes Phase 3 chromosome 1
  subset.
- `param.yaml` selects the historical b37 annotation profile.
- `test_1000G.norm.ann.dbnsfp.clinvar.cosmic.vcf.gz` is the fully annotated
  converter fixture.
- `genomicVariationsVcf.json.gz` is the versioned reference BFF output.

The full CINECA chromosome 22 acceptance input remains outside Git.

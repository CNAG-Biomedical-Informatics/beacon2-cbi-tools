---
title: Configuration
---

# Configuration

The main runtime configuration lives in YAML files.

Common files include:

- `bin/config.yaml`: default local runtime configuration
- `bin/cnag-hpc-config.yaml`: CNAG HPC-oriented configuration
- `testdata/vcf/param.yaml`: VCF test configuration
- `testdata/tsv/param.yaml`: SNP-array TSV test configuration
- `examples/param_hg38.yaml`: GRCh38 / hg38 example configuration

## Common Parameters

| Parameter | Purpose |
|---|---|
| `genome` | Reference genome label, such as `hg19`, `hg38`, `hs37`, or `b37` |
| `projectdir` | Output project directory |
| `bff2html` | Whether to generate browser-oriented HTML output |
| `annotate` | Whether the VCF workflow should run annotation |
| `bff.metadatadir` | Directory containing metadata BFF JSON collections for loading |
| `bff.genomicVariationsVcf` | Path to generated genomic variation output |

Keep the genome setting aligned with the VCF contig naming and annotation resources used by your installation.

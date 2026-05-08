---
title: CLI Reference
---

# CLI Reference

The main entry point is `bin/bff-tools`.

```bash
bin/bff-tools --help
```

## Modes

| Mode | Purpose |
|---|---|
| `validate` | Validate XLSX or JSON metadata and write BFF JSON collections |
| `vcf` | Convert VCF or VCF.gz genomic input into BFF `genomicVariations` |
| `tsv` | Convert SNP-array TSV or TXT input into BFF `genomicVariations` |
| `load` | Load existing BFF collections into MongoDB |
| `full` | Run conversion plus MongoDB loading in one command |

For an end-to-end example, see [Data Beaconization](../workflows/data-beaconization.md).

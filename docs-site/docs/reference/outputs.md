---
title: Outputs
---

# Outputs

This page explains the files and directories you should expect after running `bff-tools`.

## Run Directory

Conversion and loading modes create a run-specific project directory. By default, this directory usually has a generated name such as:

```text
beacon_XXXXXXXXXXXXXXX/
```

You can override the project directory with:

```bash
bin/bff-tools vcf -i input.vcf.gz -p param.yaml --projectdir-override my_project
```

## Common Files

| Output | Created by | Purpose |
|---|---|---|
| `log.json` | `vcf`, `tsv`, `load`, `full` | Captures resolved arguments, configuration, and parameters for reproducibility |
| `genomicVariationsVcf.json.gz` | `vcf`, `tsv`, `full` | BFF genomic variation collection generated from VCF-style input |
| `*.log` files | pipeline stages | Stage-specific execution logs for debugging |
| `run_*.sh` scripts | pipeline stages | Rendered shell scripts used to execute the run |

## Metadata Validation Output

`bff-tools validate` writes BFF JSON collections to the requested output directory.

Typical files include:

```text
analyses.json
biosamples.json
cohorts.json
datasets.json
individuals.json
runs.json
```

If `genomicVariations` validation is enabled, genomic variation output may also be written.

## VCF Conversion Output

`bff-tools vcf` usually writes under:

```text
beacon_*/vcf/
```

Typical contents include:

- normalized and annotated VCF intermediates
- `genomicVariationsVcf.json.gz`
- `run_vcf2bff.sh`
- `run_vcf2bff.log`

## TSV Conversion Output

`bff-tools tsv` usually writes under:

```text
beacon_*/tsv/
beacon_*/vcf/
```

The `tsv` step first creates a VCF-like intermediate, then continues through the same BFF genomic conversion path.

## Browser Output

If `bff2html: true` is enabled in the parameter file, static browser output is written under:

```text
beacon_*/browser/
```

This output is useful for local inspection without MongoDB.

## MongoDB Loading Output

`bff-tools load` and `bff-tools full` usually write MongoDB import logs under:

```text
beacon_*/mongodb/
```

The actual data is inserted into MongoDB using the configured `mongodburi`.

## Debugging Tips

- Start with `log.json` to confirm the resolved configuration and input files.
- Check the relevant `*.log` file when a stage fails.
- Confirm that the reference genome in `param.yaml` matches your input.
- For MongoDB issues, inspect the `mongodb/` logs and verify `mongodburi`, `mongoimport`, and `mongosh`.

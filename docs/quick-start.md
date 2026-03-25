# Quick Start

This page shows the shortest path for running `bff-tools` after installation.

If you have not installed the toolkit yet, start with one of these pages:

- [Docker installation](download-and-installation/docker-based.md)
- [Apptainer installation](download-and-installation/apptainer-based.md)
- [Non-containerized installation](download-and-installation/non-containerized.md)

--8<-- "about/disclaimer.md"

## 1. Check the command

```bash
bin/bff-tools --help
```

## 2. Validate metadata

```bash
mkdir bff_out
bin/bff-tools validate -i utils/bff_validator/Beacon-v2-Models_template.xlsx --out-dir bff_out
```

This validates metadata and writes BFF JSON collections to `bff_out`.

## 3. Convert genomic data

### VCF input

```bash
bin/bff-tools vcf -i testdata/vcf/test_1000G.vcf.gz -p testdata/vcf/param.yaml
```

### SNP-array TSV input

```bash
bin/bff-tools tsv -i testdata/tsv/input.txt.gz -p testdata/tsv/param.yaml
```

Use `vcf` for VCF or VCF.gz input. Use `tsv` for SNP-array style TSV or TXT input.

## 4. Load into MongoDB

Once you have BFF metadata plus genomic variations, load them with:

```bash
bin/bff-tools load -p param.yaml
```

If you want conversion plus loading in one step, use:

```bash
bin/bff-tools full -i input.vcf.gz -p param.yaml
```

## Which command do I need?

- I only want to validate metadata: `bff-tools validate`
- I want to convert a VCF: `bff-tools vcf`
- I want to convert a SNP-array TSV: `bff-tools tsv`
- I already have BFF files and want to ingest them: `bff-tools load`
- I want conversion and loading in one run: `bff-tools full`

## Next steps

- For the full workflow, continue to the [tutorial](data-beaconization.md).
- For installation details, go back to the [installation pages](download-and-installation/docker-based.md).
- For troubleshooting and edge cases, see the [FAQ](help/faq.md).

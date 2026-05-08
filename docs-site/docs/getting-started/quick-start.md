# Quick Start

This page shows the shortest path for running `bff-tools` after installation.

## Assumptions

This page assumes you are running commands from the repository root or from a container where the repository is available at the current working directory. If you installed with Docker or Apptainer, open the runtime shell first and then run the commands below.

If you have not installed the toolkit yet, start with one of these pages:

- [Docker installation](docker)
- [Apptainer installation](apptainer)
- [Non-containerized installation](non-containerized)

:::warning[Research-use disclaimer]
This toolkit is intended for research use. Do not use generated annotations or results for medical decisions.
:::

## 1. Check the command

```bash
bin/bff-tools --help
```

Expected result: the command prints available modes such as `validate`, `vcf`, `tsv`, `load`, and `full`.

## 2. Validate metadata

```bash
mkdir bff_out
bin/bff-tools validate -i utils/bff_validator/Beacon-v2-Models_template.xlsx --out-dir bff_out
```

This validates metadata and writes BFF JSON collections to `bff_out`.

Expected result: JSON collections such as `individuals.json`, `biosamples.json`, `runs.json`, and `datasets.json`.

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

Expected result: a run-specific directory containing generated genomic variation output, usually under `beacon_*/vcf/` or `beacon_*/tsv/`.

## 4. Load into MongoDB

Once you have BFF metadata plus genomic variations, load them with:

```bash
bin/bff-tools load -p param.yaml
```

If you want conversion plus loading in one step, use:

```bash
bin/bff-tools full -i input.vcf.gz -p param.yaml
```

Expected result: BFF collections are inserted into MongoDB and indexes are created or updated.

## Which command do I need?

For more examples, see [What should I run?](what-should-i-run.md).

| Goal | Command |
|---|---|
| I only want to validate metadata | `bff-tools validate` |
| I want to convert a VCF | `bff-tools vcf` |
| I want to convert a SNP-array TSV | `bff-tools tsv` |
| I already have BFF files and want to ingest them | `bff-tools load` |
| I want conversion and loading in one run | `bff-tools full` |

## Next steps

- If you are not sure which mode matches your data, see [What should I run?](what-should-i-run.md).
- To understand generated files and logs, see [Outputs](../reference/outputs.md).
- For the full workflow, continue to the [tutorial](../workflows/data-beaconization.md).
- For installation details, go back to the [installation overview](installation.md).
- For troubleshooting and edge cases, see the [FAQ](../troubleshooting/faq.md).

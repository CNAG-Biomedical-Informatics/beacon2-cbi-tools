---
title: Quick Start
---

This path builds and validates BFF metadata and shows the normal raw-VCF workflow, the explicit shortcut for compatible pre-annotated VCFs, and SNP-array conversion.

## Which Command Do I Need?

| Starting data | Command | Result |
|---|---|---|
| XLSX metadata workbook | `bff-tools validate` | Validated BFF JSON collections |
| Existing BFF JSON | `bff-tools validate` | Validation report only |
| Raw or annotated VCF | `bff-tools vcf` | BFF `genomicVariations` |
| Supported SNP-array TSV/TXT | `bff-tools tsv` | BFF `genomicVariations` |
| External annotation bundle | `bff-tools install-resources` | Verified local annotation resources |

Raw VCF and TSV input is annotated by default and requires the external annotation data. Only an already annotated VCF can use `--no-annotate`.

:::info[Configuration inputs]
The optional **parameter file** (`-p`) stores run choices such as `genome`, `datasetid`, and `bff2html`. The installed package already contains the standard annotation-resource layout; `BFF_TOOLS_DATA` selects its external root. Use `-c` only for a different layout or site-specific executable paths.
:::

:::warning[Research use]
The toolkit prepares research data and annotations. It is not a medical device and its output must not be used by itself for clinical or medical decisions. See the [full disclaimer](../about/disclaimer).
:::

## 1. Check the Command

```bash
bff-tools --version
bff-tools --help
```

The primary user commands are `validate`, `vcf`, `tsv`, and `install-resources`. The separate `test` command is a developer integration check.

## 2. Create and Validate Metadata JSON

Export the packaged Beacon workbook template:

```bash
bff-tools validate --template-out metadata.xlsx
```

After filling the workbook, convert each populated worksheet into a BFF JSON collection and validate its records:

```bash
bff-tools validate -i metadata.xlsx -o bff
```

The output directory contains collections such as `individuals.json`, `biosamples.json`, `analyses.json`, and `datasets.json`. Each collection is written only when its rows pass the corresponding Beacon v2 schema, unless `--ignore-validation` is explicitly used.

Existing JSON follows a validation-only path and is not rewritten:

```bash
bff-tools validate -i bff/individuals.json bff/biosamples.json
```

## 3. Convert and Annotate Variants

For most raw VCFs, first prepare the [annotation data](annotation-data), then run:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools install-resources
bff-tools vcf \
  -i cohort.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  --annotate \
  -o cohort-bff
```

For a repeatable run, put the same choices in an optional parameter file:

```yaml title="cohort.yaml"
genome: hg38
datasetid: cohort-1
projectdir: cohort-bff
annotate: true
bff2html: true
```

Then keep the command shorter:

```bash
bff-tools vcf -i cohort.vcf.gz -p cohort.yaml
```

CLI options override values from `cohort.yaml`. See [Configuration](../reference/configuration) for all accepted keys and defaults.

If the VCF already contains a compatible SnpEff `ANN` header and annotations, disable re-annotation explicitly. dbNSFP and ClinVar fields are still strongly recommended for complete output:

```bash
bff-tools vcf -i cohort.annotated.vcf.gz \
  --genome hg38 --dataset-id cohort-1 --no-annotate -o cohort-bff
```

The primary output is:

```text
cohort-bff/vcf/genomicVariationsVcf.json.gz
```

Add `--browser` to generate a standalone HTML report alongside the BFF output:

```bash
bff-tools vcf -i cohort.vcf.gz \
  --genome hg38 --dataset-id cohort-1 \
  --browser -o cohort-bff-browser
```

## 4. Convert SNP-Array Data

TSV/TXT conversion needs a sample identifier, the matching reference assembly, and the annotation bundle selected above:

```bash
bff-tools tsv \
  -i genotypes.txt.gz \
  --sample-id sample-1 \
  --genome hg19 \
  --dataset-id cohort-1 \
  -o sample-1-bff
```

The command creates a VCF intermediate, annotates it, and converts it through the same production VCF-to-BFF path. `--no-annotate` is not accepted for TSV input.

## 5. Verify Annotation and Output

Annotation-enabled runs retain normalized and annotated VCF intermediates. Inspect representative ANN, dbNSFP, ClinVar, and COSMIC fields and record every database version with the run.

```bash
bff-tools validate -i cohort-bff/vcf/genomicVariationsVcf.json.gz --gv-vcf
```

See [Configuration](../reference/configuration) for the profile, [Annotation Data](annotation-data) for the complete setup and integration test, and [Outputs](../reference/outputs) for the resulting directory layout.

For a connected metadata-and-variants workflow, continue with the [end-to-end tutorial](../workflows/data-beaconization). The [GRCh38 worked example](../examples/hg38) shows how the included 1000 Genomes subset was prepared, and the [FAQ](../troubleshooting/faq) retains common errors and fixes.

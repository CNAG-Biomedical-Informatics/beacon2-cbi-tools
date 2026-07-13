---
title: CLI
---

```text
bff-tools {validate,vcf,tsv} [options]
```

Run `bff-tools <command> --help` for the installed version. Conversion creates a new project directory and never overwrites an existing one.

## `validate`

Export the packaged template:

```bash
bff-tools validate --template-out metadata.xlsx
```

Validate and serialize a workbook:

```bash
bff-tools validate -i metadata.xlsx -o bff
```

Validate one or more collection files:

```bash
bff-tools validate -i individuals.json biosamples.json
```

| Option | Meaning |
|---|---|
| `-i`, `--input FILE ...` | One XLSX workbook or one or more named JSON collections |
| `--template-out PATH` | Export a fresh metadata workbook instead of validating |
| `-o`, `--out-dir DIR` | XLSX serialization destination; created when absent |
| `-s`, `--schema-dir DIR` | Override the packaged dereferenced schemas |
| `--gv` | Include the workbook `genomicVariations` sheet or JSON collection |
| `--gv-vcf` | Stream a generated `genomicVariations[Vcf].json[.gz]` array |
| `--ignore-validation` | Write workbook output despite validation issues |
| `--verbose` | Print progress for large inputs |

Validation exits nonzero when schema issues are found, unless they are explicitly ignored.

## `vcf`

Annotate and convert raw VCF input:

```bash
bff-tools vcf -i cohort.vcf.gz --genome hg38 --dataset-id cohort-1 -c config.yaml
```

Annotation is enabled by default because the converter requires a compatible SnpEff `ANN` header. Pass `--no-annotate` only when the input VCF is already annotated. Raw input requires the external annotation bundle and `config.yaml`.

```bash
bff-tools vcf -i cohort.annotated.vcf.gz \
  --genome hg38 --dataset-id cohort-1 --no-annotate
```

The input may be plain `.vcf` or gzip/BGZF-compressed `.vcf.gz`. Single-sample and multi-sample VCFs are supported. gVCFs must first be genotyped or converted to a standard variant VCF.

## `tsv`

```bash
bff-tools tsv -i genotypes.txt.gz --sample-id sample-1 --genome hg19
```

TSV conversion creates a VCF intermediate, annotates it, and then uses the same VCF-to-BFF converter. Annotation cannot be disabled for TSV input.

## Conversion Options

| Option | Meaning |
|---|---|
| `-i`, `--input FILE` | Input VCF, TSV, or supported compressed equivalent |
| `-p`, `--param FILE` | Optional YAML parameters |
| `-c`, `--config FILE` | External tool and annotation-resource configuration |
| `-o`, `--project-dir DIR` | Explicit new run directory |
| `-t`, `--threads N` | Positive thread count passed to external stages and compression |
| `--genome NAME` | `hg19`, `hg38`, `hs37`, or `b37` |
| `--dataset-id ID` | Dataset identifier embedded in BFF records |
| `--sample-id ID` | Sample identifier used by TSV conversion |
| `--annotate`, `--no-annotate` | Annotation is enabled by default; disable only for a compatibly annotated VCF |
| `--browser`, `--no-browser` | Enable or disable standalone HTML generation |
| `--verbose` | Stream stage output rather than showing the interactive spinner |

Values supplied directly on the command line override parameter YAML values. YAML values override built-in defaults.

The Python VCF-to-BFF conversion itself is single-process and streaming. Increasing `-t` helps only stages that support threads; it does not partition records across Python workers.

## Common Options

| Option | Meaning |
|---|---|
| `--verbose` | Print stage output and converter progress instead of the interactive spinner |
| `--debug N` | Preserve detailed execution output for diagnosis |
| `-nc`, `--no-color` | Disable ANSI colors |
| `-ne`, `--no-emoji` | Disable emoji output |
| `-V`, `--version` | Print the application version |

## Exit Behavior

- argument, configuration, preflight, and pipeline failures exit nonzero;
- validation issues exit nonzero unless `--ignore-validation` was explicitly supplied;
- a VCF without a usable SnpEff ANN header exits nonzero with instructions to annotate it;
- stage failures name the generated log file to inspect.

## Removed Commands

The former `load` and `full` commands were retired in `2.0.13`. Data preparation remains in `bff-tools`; database deployment remains independent. See [MongoDB Import](./mongodb) for the preserved indexing and loading procedure.

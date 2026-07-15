---
title: CLI
---

```text
bff-tools {validate,vcf,tsv,demo,install-resources,test,compare} [options]
```

Run `bff-tools <command> --help` for the installed version. Conversion creates a new project directory and never overwrites an existing one.

## `validate`

With XLSX input, this command converts each populated worksheet into a BFF JSON collection, validates its records, and writes valid collections to the output directory. With JSON input, it validates the existing collections without rewriting them.

Export the packaged template:

```bash
bff-tools validate --template-out metadata.xlsx
```

Build and validate BFF JSON from a workbook:

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
| `--gv-vcf` | Stream generated `genomicVariationsVcf.json[.gz]` or `.jsonl[.gz]` records |
| `--check-schema` | Self-validate all schemas when used alone, or each input-selected schema before checking data |
| `--ignore-validation` | Write workbook output despite validation issues |
| `--verbose` | Print progress for large inputs |

Validation exits nonzero when schema issues are found, unless they are explicitly ignored.
`bff-tools validate --check-schema` checks the complete schema registry without requiring input data. Combined with `--input`, it checks only the selected schemas before ordinary record validation.

## `demo`

Exercise the installed converter, schema validator, and standalone browser using a packaged, fully annotated fixture:

```bash
bff-tools demo
```

The default destination is a new `bff-tools-demo/` directory. Use `--output-dir DIR` to select another path or `--no-browser` to generate only BFF. The command requires no external annotation resources because it does not rerun annotation; it is an onboarding example, not a raw-VCF integration test.

## `install-resources`

Install the maintained external annotation bundle into the directory selected by `BFF_TOOLS_DATA`:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools install-resources
```

Pass `--data-dir DIR` instead of exporting the environment variable, or use `--print-links` to list the public Google Drive files for manual download. The command reuses existing files, verifies every archive part, assembles and extracts the bundle, and creates its writable `tmp/` directory.

## `test` (development)

Developers and bundle maintainers can run the packaged **compact** annotation integration test against the selected external bundle:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools test
```

The command annotates the packaged chromosome 1 1000 Genomes fixture, validates the resulting BFF, and compares all records semantically with the versioned reference output. It does **not** run the external CINECA chromosome 22 fixture. It is a development and bundle check, not a required user workflow. Use `--data-dir DIR` instead of the environment variable, `--threads N` for annotation, or `--output-dir DIR` to retain the generated project. Add `--verbose` for detailed pipeline output.

The release-scale chromosome 22 procedure uses the regular `bff-tools vcf` and `bff-tools validate` commands plus the installed `bff-tools compare` command. Do not use plain `diff` or compare compressed-file checksums for this parity gate. See [Full CINECA Release Fixture](./validation-and-reproducibility#full-cineca-release-fixture).

## `compare`

Compare two BFF genomic-variation files semantically. The command streams compressed or uncompressed JSON, ignores run-specific provenance and known order-only differences, and exits nonzero with the first differing record and JSON path:

```bash
bff-tools compare \
  --expected reference/genomicVariationsVcf.json.gz \
  --actual run/vcf/genomicVariationsVcf.json.gz
```

## `vcf`

Annotate and convert raw VCF input:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
bff-tools vcf -i cohort.vcf.gz --genome hg38 --dataset-id cohort-1
```

Annotation is enabled by default because the converter requires a compatible SnpEff `ANN` header. Pass `--no-annotate` only when the input VCF is already annotated. Raw input requires the external annotation bundle selected through `BFF_TOOLS_DATA`.

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
| `-c`, `--config FILE` | Override the packaged external-tool and annotation-resource layout |
| `-o`, `--project-dir DIR` | Explicit new run directory |
| `-t`, `--threads N` | Positive thread count passed to external stages and compression |
| `--genome NAME` | `hg19`, `hg38`, `hs37`, or `b37` |
| `--dataset-id ID` | Dataset identifier embedded in BFF records |
| `--sample-id ID` | Sample identifier used by TSV conversion |
| `--annotate`, `--no-annotate` | Annotation is enabled by default; disable only for a compatibly annotated VCF |
| `--browser`, `--no-browser` | Enable or disable standalone HTML generation |
| `--jsonl`, `--no-jsonl` | Write JSON Lines (`.jsonl.gz`) instead of the default JSON array |
| `--verbose` | Stream stage output rather than showing the interactive spinner |
| `--progress-every N` | With `--verbose`, report VCF progress every N records (default: 10,000) |

Values supplied directly on the command line override parameter YAML values. YAML values override built-in defaults.

`BFF_TOOLS_DATA` overrides the `{base}` root in the selected resource layout. Layout selection is explicit `--config`, then `BFF_TOOLS_CONFIG`, then the repository or packaged default. Absolute paths in a custom layout remain unchanged.

The Python VCF-to-BFF conversion itself is single-process and streaming. Increasing `-t` helps only stages that support threads; it does not partition records across Python workers.

Standard BFF JSON arrays remain the default for compatibility. Use `--jsonl` when a downstream tool such as `mongoimport` benefits from one complete JSON document per line. Browser generation and `validate --gv-vcf` accept either generated format.

For finer-grained diagnostics on a short file, combine `--verbose` with a smaller interval, for example `--progress-every 100`. The same option is available when running `src/bff_tools/vcf2bff.py` directly. Progress is also retained in `<project>/vcf/run_vcf2bff.log`.

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

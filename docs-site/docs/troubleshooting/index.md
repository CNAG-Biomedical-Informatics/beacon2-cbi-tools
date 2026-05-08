---
title: Troubleshooting
---

# Troubleshooting

Start here when a run fails or output does not look right. The fastest debugging path is usually:

1. Open the run directory.
2. Inspect `log.json` to confirm resolved inputs, configuration, and parameters.
3. Inspect the stage-specific `*.log` file.
4. Match the symptom below.

For more detailed explanations, continue to the [FAQ](faq.md).

## Symptom Index

| Symptom | Likely cause | First place to check |
|---|---|---|
| `bff-tools` command is not found | Runtime shell is not active, wrong working directory, or install path is not configured | [Installation](../getting-started/installation.md), then [Quick Start](../getting-started/quick-start.md) |
| `bff-tools vcf` fails early | Missing parameter file, invalid input extension, or input path not visible inside the runtime | `log.json`, [What should I run?](../getting-started/what-should-i-run.md), [CLI reference](../reference/cli.md) |
| SnpEff download or database error | External reference data is missing, inaccessible, or configured with the wrong path | Installation page for your runtime, then [FAQ](faq.md) |
| VCF contig or reference mismatch | `genome` in `param.yaml` does not match the VCF/reference data naming | `param.yaml`, `run_vcf2bff.log`, [Configuration](../reference/configuration.md) |
| VCF annotation fields are missing | Annotation was disabled or the input VCF does not contain expected fields | `annotate` in `param.yaml`, `run_vcf2bff.log`, [FAQ](faq.md) |
| TSV conversion fails | SNP-array file format or genome setting does not match the expected conversion path | `run_tsv2vcf.log`, [What should I run?](../getting-started/what-should-i-run.md) |
| Metadata validation reports missing fields | Required Beacon model fields are absent in XLSX/JSON input | Validator output, generated JSON, [data beaconization workflow](../workflows/data-beaconization.md) |
| Metadata validation reports `oneOf` warnings | Beacon schema ambiguity or a value that matches multiple schema alternatives | Validator output, [FAQ](faq.md) |
| Output directory already exists | `bff-tools` avoids silently overwriting existing run directories | Choose a new `--projectdir-override` value or move the old output |
| `genomicVariationsVcf.json.gz` is missing | VCF/TSV conversion failed before final BFF output was written | `run_vcf2bff.log`, [Outputs](../reference/outputs.md) |
| Browser output is missing | `bff2html: true` is not enabled or the HTML stage failed | `param.yaml`, `run_bff2html.log`, [Outputs](../reference/outputs.md) |
| MongoDB import fails | MongoDB is not reachable, credentials/URI are wrong, or `mongoimport`/`mongosh` paths are invalid | `run_bff2mongodb.log`, `mongodburi`, [Configuration](../reference/configuration.md) |
| Loaded data is not visible through an API | Data was not loaded into the expected database, or the Beacon API points to a different MongoDB URI | `mongodburi`, API configuration, MongoDB collections |
| Runs are slow or disk usage grows quickly | Large VCFs create several intermediate files and annotation can be expensive | Disk space, split-by-region strategy, [FAQ](faq.md) |

## Which Log Should I Open?

| Stage | Typical log |
|---|---|
| TSV conversion | `beacon_*/tsv/run_tsv2vcf.log` |
| VCF to BFF conversion | `beacon_*/vcf/run_vcf2bff.log` |
| Static browser output | `beacon_*/browser/run_bff2html.log` |
| MongoDB loading | `beacon_*/mongodb/run_bff2mongodb.log` |
| Overall resolved run context | `beacon_*/log.json` |

## Minimal Debug Checklist

- Confirm the input file exists from inside the selected runtime.
- Confirm `param.yaml` uses the expected `genome`.
- Confirm the external data directory is mounted or configured correctly.
- Confirm enough disk space is available before retrying large VCF jobs.
- Use a new project directory when rerunning a failed attempt.

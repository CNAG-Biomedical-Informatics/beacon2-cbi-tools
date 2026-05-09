---
title: Overview
---

<div className="beaconDocHero">
  <p className="beaconEyebrow">Overview</p>
  <h2>Build Beacon v2-ready datasets from metadata and genomic files.</h2>
  <p>
    `beacon2-cbi-tools` helps validate Beacon metadata, convert VCF or SNP-array input into Beacon Friendly Format, and load the resulting collections into MongoDB.
  </p>
  <div className="beaconHeroActions">
    <a className="button button--primary" href="workflows/recipes">Command recipes</a>
    <a className="button button--secondary" href="getting-started/what-should-i-run">What should I run?</a>
    <a className="button button--secondary" href="reference/supported-data">Supported data</a>
  </div>
</div>

`beacon2-cbi-tools` helps you prepare data for Beacon v2 deployments based on the Beacon Friendly Format (BFF).

With this toolkit you can:

- validate metadata from XLSX or JSON files against Beacon v2 schemas
- convert VCF or SNP-array TSV input into BFF `genomicVariations`
- load BFF collections into MongoDB
- optionally inspect the resulting data with lightweight utilities

:::warning[Research-use disclaimer]
This toolkit is intended for research use. Do not use generated annotations or results for medical decisions.
:::

## Typical Workflow

Most users follow this sequence:

1. Prepare and validate metadata with `bff-tools validate`.
2. Convert genomic data with `bff-tools vcf` or `bff-tools tsv`.
3. Load the generated BFF collections into MongoDB with `bff-tools load` or `bff-tools full`.

<div className="beaconWorkflowBand">
  <div>
    <span>Input</span>
    <strong>XLSX or BFF metadata</strong>
    <strong>VCF or SNP-array TSV</strong>
  </div>
  <div>
    <span>Process</span>
    <strong>validate</strong>
    <strong>vcf / tsv / load / full</strong>
  </div>
  <div>
    <span>Output</span>
    <strong>BFF JSON collections</strong>
    <strong>MongoDB and browser files</strong>
  </div>
</div>

## Recommended Path

If you are new to the toolkit, use this order:

1. Read the [installation overview](getting-started/installation.md) and pick Docker unless your environment requires Apptainer or a direct install.
2. Use [What should I run?](getting-started/what-should-i-run.md) to choose the right command for your input.
3. Check [Supported Inputs and Outputs](reference/supported-data.md) to confirm your data fits a supported path.
4. Run the [Quick Start](getting-started/quick-start.md) with the bundled test data.
5. Use [Command Recipes](workflows/recipes.md) for copy-paste commands.
6. Read the [data beaconization tutorial](workflows/data-beaconization) before adapting the workflow to your own data.
7. Check [Validation and Reproducibility](reference/validation-and-reproducibility.md) and [Outputs](reference/outputs.md) when reviewing generated files and logs.
8. Keep the [FAQ](troubleshooting/faq.md) open while configuring reference genomes, annotation resources, and MongoDB loading.

## What You Need Before Starting

| Requirement | Why it matters |
|---|---|
| Metadata in XLSX or BFF JSON | Required for Beacon entities such as `individuals`, `biosamples`, `runs`, and `datasets` |
| VCF, VCF.gz, or SNP-array TSV input | Used to generate BFF `genomicVariations` |
| Reference genome choice | Must match your genomic input, for example `hg19`, `hg38`, `hs37`, or `b37` |
| External reference data | Required by the genomic conversion workflow |
| MongoDB | Required only when you want to load and query BFF collections |

## Choose Your Path

<div className="beaconPathGrid">
  <a href="getting-started/installation">
    <span>Setup</span>
    <h3>Install the toolkit</h3>
    <p>Choose Docker, Apptainer, or a non-containerized setup for your workstation, server, or HPC environment.</p>
  </a>
  <a href="workflows/recipes">
    <span>Run</span>
    <h3>Copy a command</h3>
    <p>Use short recipes for validation, VCF conversion, SNP-array input, MongoDB loading, and inspection.</p>
  </a>
  <a href="workflows/data-beaconization">
    <span>Workflow</span>
    <h3>Prepare real data</h3>
    <p>Follow the end-to-end data beaconization tutorial before adapting the workflow to your own cohort.</p>
  </a>
  <a href="reference/validation-and-reproducibility">
    <span>Review</span>
    <h3>Check reproducibility</h3>
    <p>Understand what validation checks, what it cannot prove, and what to keep when sharing a run.</p>
  </a>
  <a href="examples/hg38">
    <span>Examples</span>
    <h3>Start from test data</h3>
    <p>Use the GRCh38 / hg38 example and bundled datasets to confirm that your runtime works.</p>
  </a>
  <a href="troubleshooting/">
    <span>Help</span>
    <h3>Debug a run</h3>
    <p>Find the right log file and match common symptoms around reference data, validation, and MongoDB loading.</p>
  </a>
</div>

## Main Commands

The main entry point is `bff-tools`.

- `bff-tools validate`: validate metadata and write BFF JSON collections
- `bff-tools vcf`: convert a VCF or VCF.gz file into BFF
- `bff-tools tsv`: convert a SNP-array TSV file into BFF
- `bff-tools load`: load BFF collections into MongoDB
- `bff-tools full`: run conversion plus loading in one step

## Utilities

The toolkit also includes optional utilities for browsing or queueing jobs:

- `bff-browser`: browse static BFF files without a database
- `bff-portal`: query BFF data stored in MongoDB
- `bff-queue`: run and monitor many ingestion jobs on a workstation

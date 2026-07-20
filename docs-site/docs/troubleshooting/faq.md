---
title: FAQ
description: Practical answers for installing bff-tools, correcting Beacon metadata, annotating VCFs, and reviewing BFF output.
---

<div className="faqLead">
  Start with the question closest to the failed stage. Pipeline failures name a log file; preserve that log and the generated stage script before changing the input or configuration.
</div>

## Command Guide

| Starting data | Command | Result |
|---|---|---|
| XLSX metadata | `bff-tools validate -i metadata.xlsx -o bff` | Validated BFF JSON collections |
| Existing BFF JSON | `bff-tools validate -i individuals.json biosamples.json` | Validation report only |
| Raw VCF or VCF.gz | `bff-tools vcf -i input.vcf.gz` | Annotated BFF genomic variations |
| VCF with compatible SnpEff ANN data | `bff-tools vcf -i input.vcf.gz --no-annotate` | BFF genomic variations |
| SNP-array TSV/TXT | `bff-tools tsv -i input.txt.gz` | BFF genomic variations |
| Generated genomic BFF | `bff-tools validate -i genomicVariationsVcf.json.gz --gv-vcf` | Validation report only |
| External annotation bundle | `bff-tools install-resources` | Verified local resources |
| Installation or resource diagnosis | `bff-tools doctor --genome NAME` | Capability report and actionable fixes |

## Installation and Annotation

<div className="faqList">

<details>
<summary>How do I check an installation before running data?</summary>

Run `bff-tools doctor`. It checks packaged assets, schemas, required shell tools, and the selected annotation profile without creating output. `CORE READY (annotation not configured)` is successful when no external bundle has been selected. After setting `BFF_TOOLS_DATA`, run `bff-tools doctor --genome hg19`, `hg38`, or `hs37`; an explicitly configured missing or incomplete resource exits nonzero and names the path to correct.

</details>

<details>
<summary>Do I need the annotation bundle?</summary>

For a raw VCF or SNP-array file, **yes**. The converter requires SnpEff `ANN` data, and normal production output also uses dbNSFP and ClinVar fields. Annotation is therefore enabled by default.

Use `--no-annotate` only when a VCF already has a compatible SnpEff `ANN` header and per-record annotations. If the header is absent, conversion stops with an actionable error instead of writing an empty BFF collection.

Metadata workbook conversion and JSON validation do not need the bundle. Install it for annotation with `bff-tools install-resources`; see [Annotation Data](../getting-started/annotation-data) for storage and configuration instructions.

</details>

<details>
<summary>Why does SnpEff report a missing database?</summary>

A current `bff-tools` run does not allow SnpEff to download databases. A missing-genome or missing-database error means SnpEff cannot find the selected local database directory.

Confirm that `BFF_TOOLS_DATA` names the extracted bundle root as seen by the process or **inside** Docker or Apptainer. The expected standard directory is:

For example:

```text
/beacon2-cbi-tools-data/databases/snpeff/v5.0
```

`bff-tools` passes this directory to SnpEff through `-dataDir` and uses `-nodownload`; do not edit the packaged application or `snpEff.config`.

</details>

<details>
<summary>Why does annotation fail before a run directory is created?</summary>

The CLI performs a preflight check before starting. Errors such as:

```text
Configured hg38clinvar file does not exist: /data/.../clinvar.vcf.gz
Configured bcftools executable is not available: /data/.../bcftools
```

identify the unresolved key after `BFF_TOOLS_DATA`, `{base}`, and `{arch}` resolution. Check the selected genome, host or container path, executable permission, architecture (`x86_64` or `arm64`), Java path, temporary directory, and all FASTA, dbNSFP, ClinVar, and COSMIC files.

</details>

<details>
<summary>Does the Docker image include MongoDB?</summary>

No. The core image contains the Python application. The annotation image adds Java, bcftools, SnpEff, and SnpSift. Neither image contains a MongoDB server, `mongosh`, or MongoDB Database Tools.

MongoDB is an optional downstream destination. Install its clients separately and follow [MongoDB Import](../reference/mongodb) when needed.

</details>

</div>

## VCF, Coordinates, and Assemblies

<div className="faqList">

<details>
<summary>What should I check first when VCF conversion fails?</summary>

Read the log path printed by `bff-tools`, then check these in order:

1. The selected assembly matches the VCF coordinates.
2. VCF contig names match the configured FASTA and annotation resources.
3. The VCF header defines every INFO and FORMAT field used by records.
4. A pre-annotated VCF contains a usable SnpEff `ANN` header.
5. The output directory does not already exist.

Compare contigs without rewriting the source file:

```bash
bcftools query -f '%CHROM\n' cohort.vcf.gz | head
cut -f1 /path/to/reference.fa.gz.fai | head
```

If one side uses `chr22` and the other uses `22`, select matching resources. Do not assume that adding or removing `chr` changes GRCh37 into hg19 or performs a liftover.

</details>

<details>
<summary>Which assembly name should I use?</summary>

Use the assembly and contig convention that produced the input VCF:

| Profile | Typical contigs | Notes |
|---|---|---|
| `hg38` | `chr1`, `chr2`, ... | GRCh38 coordinates with UCSC-style names |
| `hg19` | commonly `chr1`, `chr2`, ... | UCSC hg19 resources |
| `hs37` | commonly `1`, `2`, ... | 1000 Genomes hs37d5 resources |
| `b37` | commonly `1`, `2`, ... | Alias normalized by the CLI to `hs37` |

The CLI does not rename contigs or lift coordinates. `hg19` and `hs37` are not interchangeable merely because both derive from GRCh37.

</details>

<details>
<summary>Are worked GRCh38 and GRCh37 inputs available?</summary>

Yes. The repository includes a compact [GRCh38 / hg38 worked example](../examples/hg38) derived from 1000 Genomes chromosome 22, including the commands used to recreate and beaconize it. Compact [GRCh37 / hs37 fixtures](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/src/bff_tools/integration_assets) provide converter regression inputs and expected outputs. The [CINECA synthetic cohort](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/CINECA_synthetic_cohort_EUROPE_UK1) provides a populated metadata example; its full GRCh37/hs37d5 chromosome 22 release fixture is [downloaded separately](https://drive.google.com/drive/folders/1_B30lOZKndJQZPW4Wza3ho-xGsekH4fM).

The compact files are suitable for learning and CI. `bff-tools test` uses the packaged chromosome 1 fixture; it does not run chromosome 22. The complete CINECA chr22 VCF used for release acceptance is intentionally kept outside Git and is processed separately with the application's normal VCF and validation commands.

</details>

<details>
<summary>How do I handle a malformed INFO field?</summary>

Prefer correcting the VCF producer or its header. If bcftools names one disposable tag, you can remove only that tag after checking that it is not needed downstream. The historical `IDREP` workaround was:

```bash
bcftools annotate -x INFO/IDREP \
  -Oz -o input.no-IDREP.vcf.gz input.vcf.gz
bcftools index -t input.no-IDREP.vcf.gz
```

Removing a tag loses data. Do not apply this command to unrelated cardinality or parsing errors, and keep the original VCF plus the transformation command in provenance.

</details>

<details>
<summary>Can I use single-sample and multi-sample VCFs?</summary>

Yes. Both are supported. Multi-sample genotypes are represented in `caseLevelData` with the VCF sample name as `biosampleId`. Confirm those identifiers match your metadata before handing the files to a Beacon implementation.

</details>

<details>
<summary>Can I use a gVCF?</summary>

Not directly. First genotype or convert it into a standard variant VCF with ALT alleles. Prefer the workflow recommended by the caller that produced the gVCF.

bcftools also provides `--gvcf2vcf`:

```bash
bcftools convert --gvcf2vcf -f reference.fa \
  -Oz -o expanded.vcf.gz input.g.vcf.gz
```

This expands reference blocks and can emit non-variant sites, so filter and inspect the result before annotation. See the official [bcftools convert documentation](https://samtools.github.io/bcftools/bcftools#convert).

</details>

<details>
<summary>Can I use SNP-array data such as 23andMe exports?</summary>

Yes. Use `bff-tools tsv` for the supported TSV/TXT layout:

```bash
bff-tools tsv -i genotypes.txt.gz \
  --sample-id sample-1 --genome hg19
```

bcftools first converts coordinates and alleles with the matching FASTA. The resulting VCF is then annotated because it does not yet contain SnpEff `ANN` data.

</details>

<details>
<summary>Are Beacon genomic variation coordinates 0-based or 1-based?</summary>

The generated BFF uses **0-start, half-open** intervals. VCF `POS` is 1-based; the converter writes `start = POS - 1` and `end = POS` for a single-base record. This follows the [Beacon coordinate recommendation](https://docs.genomebeacons.org/formats-standards/#genome-coordinates).

</details>

<details>
<summary>Can I keep my existing VCF annotations?</summary>

Yes, when they follow the SnpEff ANN structure expected by the converter. Run with `--no-annotate` to preserve the input and skip normalization and re-annotation:

```bash
bff-tools vcf -i cohort.annotated.vcf.gz \
  --genome hg38 --dataset-id cohort-1 --no-annotate
```

ANN is required. dbNSFP and ClinVar are not required for parsing, but omitting them produces less complete identifiers, frequencies, prediction fields, and clinical interpretations.

</details>

<details>
<summary>Are structural variants and copy-number variants supported?</summary>

Support is limited. The production mapping is designed for SNVs and nucleotide insertions/deletions. Symbolic ALT alleles such as `<DEL>` and `<CNV>` are currently skipped. Do not infer that a successful run means structural variation was represented exhaustively.

</details>

</div>

## Metadata and Validation

<div className="faqList">

<details>
<summary>Is XLSX the only metadata input?</summary>

No. `bff-tools validate` accepts existing BFF JSON collections directly. The workbook is provided because it makes mapping nested Beacon entities approachable and produces deterministic JSON.

For REDCap, OMOP CDM, Phenopackets v2, or general CSV conversion, see [Convert-Pheno](https://github.com/CNAG-Biomedical-Informatics/convert-pheno), then validate the resulting BFF JSON here.

</details>

<details>
<summary>Why was a workbook collection not written?</summary>

By default, a worksheet with schema issues is not written. The report names the collection, the actual workbook row, and the generated JSON path:

```text
individuals: 1 validation issue(s)
  row 2: $: 'id' is a required property
```

Correct the named workbook row and rerun. `--ignore-validation` can write intermediate JSON for diagnosis, but that output has not passed validation.

</details>

<details>
<summary>What does a CURIE error mean?</summary>

Ontology identifiers require a prefix and local identifier separated by a colon:

```text
row 2: ethnicity.id: 'European' does not match '^\w[^:]+:.+$'
```

Replace free text in the `.id` column with a real ontology identifier such as `PREFIX:TERM`, and put the human-readable value in `.label`. Do not invent a code merely to satisfy the pattern.

</details>

<details>
<summary>Why does oneOf say that multiple rules match?</summary>

JSON Schema `oneOf` requires exactly one branch to match. Time and measurement objects can accidentally contain properties from multiple alternatives, and some Beacon v2 schema branches overlap.

Use `--ignore-validation` only to inspect the generated JSON. Remove mixed representations so the object describes one quantity, ontology term, age, range, or date. If one intended representation still matches multiple branches because of schema overlap, record the schema issue; do not describe the record as validated.

</details>

<details>
<summary>Why did a workbook string become a JSON number or boolean?</summary>

The serializer preserves the legacy behavior: number-like cells become JSON numbers, and case-insensitive `true` or `false` become booleans. This coercion is deliberate because JSON serializers distinguish stored strings from numbers.

Identifiers that look numeric need a source representation that remains unambiguously textual. Inspect generated JSON whenever leading zeros or identifier types matter.

</details>

<details>
<summary>Are Unicode values supported?</summary>

Yes. Cell values and JSON output use UTF-8. Copying from external systems can still introduce non-breaking spaces, typographic quotes, or invisible control characters. When an error is difficult to locate, generate debugging output with `--ignore-validation`, inspect the exact JSON value, correct the workbook, and validate again without the flag.

</details>

</div>

## Output, Scale, and Inspection

<div className="faqList">

<details>
<summary>Does conversion discard variants based on FILTER or QUAL?</summary>

No. SNVs and nucleotide indels are not removed because `FILTER` is non-PASS or `QUAL` is low. `FILTER`, `QUAL`, per-sample `FORMAT/DP`, and assembly metadata are retained for downstream review. Aggregate site-level `INFO/DP` is not mapped. Records without ANN and currently unsupported symbolic alleles are separate exceptions and are reported or skipped explicitly.

</details>

<details>
<summary>How much disk space should I reserve?</summary>

Annotation retains normalized, SnpEff, dbNSFP, ClinVar, and COSMIC VCF intermediates, plus the final BFF JSON. As a planning estimate, reserve up to **10 times the compressed input VCF size**, in addition to the annotation bundle itself. Multi-sample BFF output can be larger than the source VCF.

After a run is validated and archived, intermediates may be removed according to your reproducibility policy. Keep source checksums, commands, logs, resource versions, and the final annotated input used by the converter.

</details>

<details>
<summary>Should I split a very large VCF by chromosome?</summary>

It can simplify scheduler requests, retries, storage management, and acceptance checks. The Python converter is single-process and streams records with low memory use; splitting does not inherently make one record convert faster.

Use bcftools so headers remain valid:

```bash
bcftools view -r chr22 -Oz -o cohort.chr22.vcf.gz cohort.vcf.gz
bcftools index -t cohort.chr22.vcf.gz
```

Do not concatenate completed JSON arrays with plain `cat`. Import chromosome outputs separately or merge them with a JSON-aware streaming process.

</details>

<details>
<summary>What performance should I expect?</summary>

Conversion time scales with records, annotations, sample count, compression, and storage speed. On a 6-core ARM64 workstation, a complete CINECA chr22 run covering normalization, SnpEff, dbNSFP, ClinVar and COSMIC annotation, VCF-to-BFF conversion, and browser generation completed in 13 minutes 52 seconds. It normalized 1,103,547 source records into 1,110,240 records, produced 1,109,368 BFF records for 2,504 samples, and selected 14,305 panel-matched variants for the report.

Measured separately, conversion of the already annotated VCF took 1 minute 47 seconds with about 20 MB peak RAM. That VCF uses `FORMAT=GT`; multi-field sample values such as `GT:DP:AD` require additional parsing and may take longer. Browser generation took 44 seconds with about 22 MB peak RAM. Treat these as observed reference measurements rather than runtime guarantees.

</details>

<details>
<summary>Where is the standalone HTML report?</summary>

Pass `--browser` or set `bff2html: true`. The generated HTML is under `<project>/browser/` and opens directly without a local server. The **BFF Tools Browser** provides search, sorting, column controls, gene panels, database links, and pagination. The `biosamples` column is hidden by default.

Input is streamed, so chromosome size does not determine generator memory. Browser memory still scales with the panel-matched variants embedded in the standalone report. A runtime warning is emitted at 50,000 retained rows or 100 MiB of embedded row data; use narrower panels or disable `bff2html` for very large reports.

</details>

</div>

## Downstream Use and Project History

<div className="faqList">

<details>
<summary>How do I load BFF files into MongoDB now?</summary>

MongoDB loading is no longer built into `bff-tools`. Install MongoDB Database Tools and `mongosh` separately, create the recommended indexes, and stream the generated JSON arrays through `mongoimport` as documented in [MongoDB Import](../reference/mongodb).

The documented imports use stable upsert fields, so rerunning the same data is idempotent. Index creation with the same specification is also idempotent. Imports do not remove records absent from a newer file.

</details>

<details>
<summary>Which Beacon server can consume the output?</summary>

BFF files are portable handoff artifacts rather than a bundled server. Two downstream implementations are:

- [EGA Beacon v2 PI API](https://github.com/EGA-archive/beacon2-pi-api)
- [Progenetix bycon](https://codeberg.org/Progenetix/bycon/)

Confirm each implementation's current storage and ingestion requirements before loading production data.

</details>

<details>
<summary>Where did bff-browser, bff-portal, and bff-queue go?</summary>

The useful static-browser workflow is integrated into `bff-tools vcf --browser` and produces a standalone report. The older Flask `bff-browser`, MongoDB-backed `bff-portal`, and workstation `bff-queue` were retired so the project can focus on data beaconization. Use an HPC scheduler or an external workflow manager for job orchestration.

</details>

<details>
<summary>Should I update to the latest release?</summary>

Generally, yes. Releases contain converter fixes, schema alignment, dependency updates, and documentation corrections. Review `CHANGELOG.md` and run your representative inputs in a separate output directory before replacing a production installation. Keep the previous image or environment until record counts, validation, and biological spot checks pass.

</details>

<details>
<summary>Where can I get the full CINECA synthetic cohort?</summary>

The populated metadata workbook is included in the repository. The full synthetic WGS data is available through EGA dataset [EGAD00001006673](https://ega-archive.org/datasets/EGAD00001006673). The GRCh37/hs37d5 chromosome 22 release fixture, its tabix index, and the versioned BFF reference output are available from the public [CINECA fixture folder](https://drive.google.com/drive/folders/1_B30lOZKndJQZPW4Wza3ho-xGsekH4fM). These developer assets are intentionally not committed to Git or included in the PyPI distribution.

</details>

<details>
<summary>Does bff-tools upload personal or genomic data?</summary>

No input data is sent to an application service. Conversion and validation run locally. Downloading the annotation bundle and container images contacts their hosting services, and downstream storage is your responsibility. Review BFF output, browser reports, logs, mounted paths, backups, and access controls before handling sensitive data.

</details>

<details>
<summary>What should I preserve from a run?</summary>

Keep source checksums, parameter and configuration YAML, `log.json`, stage scripts and logs, annotation resource versions, schema results, record counts, and representative biological spot checks. See [Validation and Trust](../reference/validation-and-reproducibility).

</details>

<details>
<summary>Is the project open source, and how should I cite it?</summary>

Yes. The code is distributed under GPL-3.0. Cite the Beacon v2 Reference Implementation paper shown on the [Citation](../about/citation) page, and review the [research-use disclaimer](../about/disclaimer).

</details>

</div>

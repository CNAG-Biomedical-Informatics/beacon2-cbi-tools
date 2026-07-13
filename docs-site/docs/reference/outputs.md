---
title: Outputs
---

## Metadata Validation

An XLSX validation run writes one JSON array per selected worksheet:

```text
bff/
├── analyses.json
├── biosamples.json
├── cohorts.json
├── datasets.json
├── individuals.json
└── runs.json
```

Keys are sorted and formatting is deterministic. The collections reproduce the former Perl validator output byte-for-byte.

## VCF Conversion

A conversion run creates a new project directory:

```text
cohort-bff/
├── log.json
├── vcf/
│   ├── genomicVariationsVcf.json.gz
│   ├── run_vcf2bff.sh
│   └── run_vcf2bff.log
└── browser/
    ├── <run-id>.html
    └── run_bff2html.log
```

The `browser/` directory exists only when browser generation is enabled. Annotation-enabled runs also retain normalization and annotation intermediates in `vcf/`.

## `genomicVariationsVcf.json.gz`

This is a compressed JSON array formatted with one BFF record per line. The layout allows `bff-tools validate --gv-vcf` and the standalone report generator to process large collections incrementally.

Records may contain:

- variant identifiers and VRS-style variation data;
- coordinates and assembly metadata;
- per-sample `caseLevelData`;
- quality values and filters;
- molecular attributes from ANN/dbNSFP;
- clinical interpretations from ClinVar when present;
- converter provenance under `_info`.

Extra fields such as `assemblyId`, `DP`, `QUAL`, and `FILTER` are retained because the Beacon schemas permit additional properties and they are useful for downstream inspection.

## Reproducibility Files

`log.json` records resolved arguments, parameters, and non-secret configuration. Generated shell scripts capture the exact stage commands. Paths and host details can vary between runs; the biological BFF content should remain semantically stable.

Do not publish logs before checking them for local paths or operational metadata that your project considers sensitive.

## Serving the Data

`bff-tools` stops at portable BFF files. See [MongoDB Import](./mongodb.md) for repeatable loading commands, the legacy wildcard indexes, and links to complete Beacon server implementations.

---
title: Overview
---

import useBaseUrl from '@docusaurus/useBaseUrl';

<div className="beaconDocHero">
  <p className="beaconEyebrow">Beacon v2 data preparation</p>
  <h2>Turn metadata and genomic files into portable BFF collections.</h2>
  <p>
    Build and validate BFF metadata from XLSX, validate existing JSON, convert genomic data, and inspect the result before connecting it to a Beacon implementation.
  </p>
  <div className="beaconHeroActions">
    <a className="button button--primary" href="workflows/data-beaconization">Start the tutorial</a>
    <a className="button button--secondary" href="getting-started/quick-start">Quick start</a>
    <a className="button button--secondary" href="reference/supported-data">Supported data</a>
  </div>
</div>

**Beacon v2 CBI Tools** does one job: it prepares data in the Beacon Friendly Format (BFF) for Beacon v2. Its command-line interface is called **`bff-tools`**.

<div className="beaconFlowDiagramFrame">
  <img
    className="beaconFlowDiagram"
    src={useBaseUrl('/img/beaconization-workflow.svg')}
    alt="Flow from metadata, VCF, and SNP-array inputs through bff-tools to portable BFF files, followed by an independently deployed storage layer and Beacon API"
  />
</div>

## Choose a Starting Point

<div className="beaconPathGrid">
  <a href="getting-started/quick-start">
    <span>Two minutes</span>
    <h3>Run the packaged demo</h3>
    <p>Convert an annotated VCF, validate BFF, and open the standalone browser without external resources.</p>
  </a>
  <a href="workflows/data-beaconization">
    <span>Complete workflow</span>
    <h3>Beaconize a dataset</h3>
    <p>Follow metadata and variants from source files through validation and review.</p>
  </a>
  <a href="reference/validation-and-reproducibility">
    <span>Quality control</span>
    <h3>Build trust in the output</h3>
    <p>Check schema results, provenance, biological assumptions, and reproducibility.</p>
  </a>
  <a href="examples/hg38">
    <span>Worked input</span>
    <h3>Run the GRCh38 example</h3>
    <p>Recreate and beaconize the included 1000 Genomes chromosome 22 subset.</p>
  </a>
  <a href="troubleshooting/faq">
    <span>Help</span>
    <h3>Resolve a failed run</h3>
    <p>Find focused answers for workbooks, VCF conversion, annotation, and reports.</p>
  </a>
</div>

## Core Commands

| Command | Use it for |
|---|---|
| `bff-tools doctor` | Check installed capabilities and annotation-resource readiness without running a pipeline |
| `bff-tools demo` | Verify an installation and inspect generated BFF without external annotation resources |
| `bff-tools validate` | Build and validate BFF metadata from XLSX, or validate existing BFF JSON |
| `bff-tools vcf` | Convert a VCF or VCF.gz file into BFF `genomicVariations` |
| `bff-tools tsv` | Convert supported SNP-array text data through VCF into BFF |

Raw VCF and SNP-array workflows require the [full annotation data](getting-started/annotation-data.md) to add ANN, dbNSFP, ClinVar, and COSMIC fields before conversion. Annotation is enabled by default. Use `--no-annotate` only for a VCF that already contains a compatible SnpEff `ANN` header and annotations.

:::warning[Research use]
The toolkit prepares and validates data structures. It does not establish clinical validity and must not be used by itself for medical decisions.
:::

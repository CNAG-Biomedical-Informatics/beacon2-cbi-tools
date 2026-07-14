# Direct Installation from PyPI or Source

Use a direct installation when the host or HPC environment already manages Python, Java, bcftools, and reference data through packages or environment modules.

Perl, `xlsx2csv`, MongoDB, `mongosh`, and MongoDB Database Tools are not application dependencies.

## Requirements

- Linux on `amd64` or `arm64`;
- Python 3.10 or newer;
- Java, bcftools, SnpEff, and SnpSift for raw VCF or TSV annotation;
- the external FASTA, dbNSFP, ClinVar, and COSMIC resources;
- sufficient temporary and output storage for retained annotation intermediates.

Metadata validation and conversion of a compatibly annotated VCF need only Python and the installed package.

## 1. Install the Released Package

Create an isolated environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install beacon2-cbi-tools
```

Verify it:

```bash
bff-tools --version
bff-tools validate --help
bff-tools vcf --help
```

## 2. Install from a Source Checkout

Use this route for development or for an unreleased version:

```bash
git clone https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools.git
cd beacon2-cbi-tools
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install .
```

The `bin/bff-tools` checkout shim invokes the same package code without requiring a global installation.

## 3. Validate Metadata

```bash
bff-tools validate --template-out metadata.xlsx
bff-tools validate -i metadata.xlsx -o bff
```

No annotation bundle is needed for this step.

## 4. Install the Annotation Runtime

For raw VCF and TSV input, install or load:

- Java compatible with the selected SnpEff/SnpSift release;
- bcftools;
- SnpEff and SnpSift jars;
- a matching FASTA plus dbNSFP, ClinVar, and COSMIC data.

On Debian or Ubuntu, the system executables can be installed with:

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends \
  bcftools default-jre-headless libsnpsift-java snpeff
```

HPC users should prefer site modules when available. Prepare the shared bundle using the [annotation-data guide](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/docs/getting-started/annotation-data/), then select its extracted root once:

```bash
export BFF_TOOLS_DATA=/absolute/path/to/beacon2-cbi-tools-data
```

The installed package contains the standard resource layout. Use `--config` or `BFF_TOOLS_CONFIG` only when the bundle layout or site-managed executable paths differ from that default.

## 5. Annotate and Convert

```bash
bff-tools vcf -i cohort.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  -o cohort-bff
```

Annotation is enabled by default. For a VCF that already has a compatible SnpEff `ANN` header and annotations:

```bash
bff-tools vcf -i cohort.annotated.vcf.gz \
  --genome hg38 \
  --dataset-id cohort-1 \
  --no-annotate \
  -o cohort-bff
```

TSV input cannot disable annotation because the generated VCF does not contain ANN data.

## 6. Test the Installation

Install test dependencies in a source checkout and run the normal suite:

```bash
python3 -m pip install ".[test]"
pytest -q
```

After installing the complete external bundle, run the full annotation integration:

```bash
BFF_TOOLS_DATA=/absolute/path/to/data \
  deploy/02_test_deployment.sh
```

That test covers normalization, SnpEff, dbNSFP, ClinVar, COSMIC, VCF-to-BFF conversion, schema validation, and semantic comparison with the committed expected output.

## Troubleshooting

- **Python import failure:** reactivate the intended virtual environment and reinstall the package.
- **Executable not available:** use an absolute executable path in a custom configuration or load the required module before running.
- **Configured file missing:** verify `BFF_TOOLS_DATA`, assembly selection, architecture, and filesystem permissions.
- **SnpEff database missing:** verify the `snpeffdata` directory in the resolved configuration. `bff-tools` supplies it with `-dataDir` and disables network downloads.
- **Output directory exists:** choose a new `-o` path; runs do not overwrite previous results.

MongoDB clients are optional downstream tools and must be installed separately.

# bff-tools

`bff-tools` is the main command-line entry point of `beacon2-cbi-tools`. It validates Beacon metadata, converts genomic files into BFF `genomicVariations`, and loads BFF collections into MongoDB.

## Synopsis

```text
bff-tools <mode> [arguments] [options]
```

Modes:

- `vcf`: convert a VCF or VCF.gz file into BFF.
- `tsv`: convert a SNP-array TSV file into BFF.
- `validate`: validate XLSX or JSON metadata and write BFF JSON collections.
- `load`: load BFF collections into MongoDB.
- `full`: run `vcf` or `tsv` plus `load`.

## Common workflows

- Convert a VCF file: `bff-tools vcf -i input.vcf.gz -p params.yaml`
- Convert a SNP-array TSV file: `bff-tools tsv -i sample.tsv -p params.yaml`
- Validate metadata: `bff-tools validate -i metadata.xlsx -o outdir`
- Load BFF collections: `bff-tools load -p params.yaml`
- Convert and load in one run: `bff-tools full -i input.vcf.gz -p params.yaml`

## Required inputs

### `vcf` and `tsv`

- `-i`, `--input`: input VCF, VCF.gz, or TSV file
- `-p`, `--param`: optional YAML parameter file
- `-c`, `--config`: optional configuration file
- `-t`, `--threads`: optional thread count
- `-projectdir-override`: optional output project directory

### `load`

- `-p`, `--param`: YAML parameter file describing the BFF files to load
- `-c`, `--config`: optional configuration file

### `full`

- same inputs as `vcf` or `tsv`, plus the BFF metadata files referenced in the parameter file

### `validate`

- `-i`, `--input`: one or more XLSX or JSON metadata files
- `-s`, `--schema-dir`: directory containing dereferenced JSON schemas
- `-o`, `--out-dir`: output directory for validated collections
- `-gv`: include the `genomicVariations` sheet or collection
- `-ignore-validation`: write output even if schema validation reports errors
- `-gv-vcf`: experimental mode for reading `genomicVariations` from a Beacon VCF export

Generic options:

- `-h`, `--help`: brief help
- `-man`: full manual
- `-v`: version
- `-debug <level>`: debugging output from 1 to 5
- `-verbose`: verbose mode
- `-nc`, `--no-color`: disable colors
- `-ne`, `--no-emoji`: disable emoji output

## Notes

- `bff-tools` creates an independent project directory for each run and treats your input data as read-only.
- For `vcf`, `tsv`, and `full`, using `-t 1` is often the safest choice. Larger workloads are usually better split across files or chromosomes.
- If `annotate: false` is used in the parameter file, `bff-tools` expects the input VCF to already contain the required annotation fields.

## Minimal parameter file examples

### `vcf`

```yaml
genome: hs37
annotate: true
bff2html: false
```

### `tsv`

```yaml
genome: b37
annotate: true
sampleid: sample_01
```

### `load`

```yaml
bff:
  metadatadir: .
  analyses: analyses.json
  biosamples: biosamples.json
  cohorts: cohorts.json
  datasets: datasets.json
  individuals: individuals.json
  runs: runs.json
  genomicVariationsVcf: my_project/vcf/genomicVariationsVcf.json.gz
projectdir: my_project
```

### `full`

```yaml
genome: hs37
annotate: true
bff:
  metadatadir: .
  analyses: analyses.json
  runs: runs.json
projectdir: my_project
```

## Examples

```bash
bin/bff-tools vcf -i input.vcf.gz
bin/bff-tools vcf -i input.vcf.gz -p params.yaml -projectdir-override beacon_exome_01
bin/bff-tools tsv -i input.tsv -p params.yaml
bin/bff-tools load -p params.yaml
bin/bff-tools full -i input.vcf.gz -p params.yaml -t 1
bin/bff-tools validate -i metadata.xlsx -o outdir
bin/bff-tools validate -i metadata.xlsx --gv --schema-dir deref_schemas --out-dir outdir
```

## Citation

If you use these tools in published work, please cite:

Rueda, M, Ariosa R. "Beacon v2 Reference Implementation: a toolkit to enable federated sharing of genomic and phenotypic data". _Bioinformatics_, btac568, <https://doi.org/10.1093/bioinformatics/btac568>

## Author

Written by Manuel Rueda, PhD. CNAG Biomedical Informatics: <https://www.cnag.eu>

## License

See [LICENSE](../LICENSE).

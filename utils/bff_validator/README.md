# bff-validator

`bff-validator` validates Beacon v2 metadata and writes it as BFF JSON collections.

This README documents the standalone utility in `utils/bff_validator`. In normal `beacon2-cbi-tools` usage, the same validation workflow is usually run through `bff-tools validate`, which wraps this component as part of the main toolkit.

## Synopsis

```text
bff-validator -i <file.xlsx|*.json> [options]
```

Main options:

- `-i`, `--input`: XLSX file or JSON collection files
- `-s`, `--schema-dir`: directory with dereferenced JSON schemas
- `-o`, `--out-dir`: output directory for generated BFF files
- `-gv`: include `genomicVariations`
- `-ignore-validation`: write output even if validation reports errors
- `-gv-vcf`: experimental mode for reading `genomicVariations.json` from a Beacon VCF export

Generic options:

- `-h`, `--help`
- `-man`
- `-debug <level>`
- `-verbose`
- `-nc`, `--no-color`
- `-ne`, `--no-emoji`

## Inputs

You can validate either:

- a multi-sheet XLSX metadata workbook
- a set of uncompressed BFF JSON files such as `analyses.json`, `biosamples.json`, and `individuals.json`

The schema directory must contain dereferenced Beacon JSON schemas.

## Examples

```bash
./bff-validator -i file.xlsx
./bff-validator -i file.xlsx -o my_bff_outdir
./bff-validator -i my_bff_in_dir/*.json -s deref_schemas -o my_bff_out_dir
./bff-validator -i file.xlsx --gv --schema-dir deref_schemas --out-dir my_bff_out_dir
bff-tools validate -i file.xlsx -o my_bff_outdir
```

## Install

If you are using the full `beacon2-cbi-tools` installation, no extra step is required. In that case, the recommended entry point is usually:

```bash
bff-tools validate -i file.xlsx -o my_bff_outdir
```

Use `bff-validator` directly only if you specifically want to run the standalone utility.

If you want this utility on its own:

```bash
sudo apt-get install cpanminus
cpanm --notest --installdeps .
pip install xlsx2csv
```

You can also install Perl modules into `~/perl5` if you prefer a local Perl environment.

## Tips for the XLSX template

- start from the template in `CINECA_synthetic_cohort_EUROPE_UK1`
- dot notation represents nested objects
- underscore notation represents arrays
- Unicode input is supported

If you already have CSV sheets, they can be merged into one XLSX file with the included `csv2xlsx` helper.

## Troubleshooting

If validation fails because of malformed JSON-like values in a cell, check brackets and braces first. `--ignore-validation` can be useful for debugging intermediate output in the directory passed to `-o`.

## Citation

If you use these tools in published work, please cite:

Rueda, M, Ariosa R. "Beacon v2 Reference Implementation: a toolkit to enable federated sharing of genomic and phenotypic data". _Bioinformatics_, btac568, <https://doi.org/10.1093/bioinformatics/btac568>

## Author

Written by Manuel Rueda, PhD. CNAG Biomedical Informatics: <https://www.cnag.eu>

## License

See [LICENSE](../../LICENSE).

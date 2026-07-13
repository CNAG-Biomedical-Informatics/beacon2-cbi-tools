# Beacon v2 models to XLSX

This repository-only developer utility regenerates the metadata workbook from
the seven dereferenced Beacon v2 schemas shipped with Beacon v2 CBI Tools. It is
not installed by the Python wheel or copied into the container images.

Run it from any directory after installing the project dependencies:

```bash
utils/_models2xlsx/defaultSchema2xlsx.sh
```

By default it writes `Beacon-v2-Models_template.xlsx` and the intermediate CSV
headers inside this directory. Use `--output`, `--csv-dir`, or `--no-csv` to
change that behavior:

```bash
utils/_models2xlsx/defaultSchema2xlsx.sh \
  --output /tmp/Beacon-v2-Models_template.xlsx \
  --no-csv
```

The source schemas default to `src/bff_tools/schemas`. An alternate directory
of dereferenced schemas can be supplied with `--schema-dir`.

The historical Perl parser is retained under `test/` as a parity oracle. The
automated tests compare its headers with the Python generator when its Perl
dependencies are available.

The workbook in `src/bff_tools/resources` remains the canonical, curated copy
distributed with the package and may contain fields selected manually for the
supported workflow. Do not overwrite it automatically. Review the generated
headers and run the validator tests before deliberately replacing that file.

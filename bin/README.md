# `bff-tools`

`bin/bff-tools` is a source-checkout shim for the packaged `bff-tools` command. It adds `src/` to `PYTHONPATH` and invokes the same Python CLI installed by `pip`.

```bash
bin/bff-tools --help
bin/bff-tools validate --help
bin/bff-tools vcf --help
bin/bff-tools tsv --help
bin/bff-tools install-resources --help
bin/bff-tools test --help
```

The public workflows are:

- `validate`: validate XLSX or JSON metadata and write BFF collections;
- `vcf`: convert VCF input into BFF `genomicVariations`;
- `tsv`: convert supported SNP-array text input through VCF into BFF.
- `install-resources`: download, verify, assemble, and extract the annotation bundle.
- `test`: run the packaged full-annotation and BFF-parity acceptance test.

Conversion parameters can be supplied in YAML with `-p`, directly on the command line, or through defaults. CLI values take precedence. Annotation is enabled by default. Use `--no-annotate` only for VCF input that already has a compatible SnpEff `ANN` header and annotations; TSV input always requires annotation.

See the [CLI documentation](../docs-site/docs/reference/cli.md) for options and examples.

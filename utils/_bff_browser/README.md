# Deprecated BFF Browser

The Flask application formerly stored here is retired. This directory remains
temporarily so existing references fail with a migration message instead of a
missing path. It will be removed in the next major release.

The replacement is the standalone **BFF GenomicVariations Browser** generated
directly by `bff-tools`. It requires neither Flask nor MongoDB.

## Generate a report

Enable browser output in the parameter file:

```yaml
bff2html: true
```

Then run the VCF or TSV workflow normally:

```bash
bin/bff-tools vcf -i input.vcf.gz -p param.yaml
```

The generated report is written to:

```text
<projectdir>/browser/<job-id>.html
```

Open that HTML file directly in a modern browser. The report embeds its data and
styles, so it can be moved or shared as one file.

## Direct renderer

The renderer can also be called without running the full pipeline:

```bash
PYTHONPATH=src python3 -m bff_tools.browser \
  --input genomicVariationsVcf.json.gz \
  --panel-dir browser/data \
  --project-id my-project \
  --job-id my-run \
  --output bff-browser.html
```

Do not add new implementation code or assets to this directory. The active
renderer and its bundled assets live under `src/bff_tools/`.

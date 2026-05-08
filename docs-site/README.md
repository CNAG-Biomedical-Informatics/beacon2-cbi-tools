# Docs Site

This directory contains the Docusaurus documentation site for `beacon2-cbi-tools`.

## Run locally

This site requires Node.js `20+`.

```bash
cd docs-site
npm ci
npm start
```

Create a production build:

```bash
npm run build
```

## External Markdown

The installation and example pages intentionally import Markdown from the repository-level `docker/`, `apptainer/`, `non-containerized/`, and `examples/` directories. Keep those files as the source of truth when updating installation instructions.

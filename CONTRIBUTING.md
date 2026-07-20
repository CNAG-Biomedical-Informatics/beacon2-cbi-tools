# Contributing

Beacon v2 CBI Tools welcomes focused bug reports, documentation corrections, interoperability findings, and tested code contributions.

## Before Opening an Issue

Search the existing issues and check the [documentation](https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/), especially the FAQ. Include the installed version, command, operating environment, relevant configuration with secrets removed, and the smallest input that reproduces the problem. Do not attach identifiable clinical or genomic data.

## Development

Use Python 3.10 or newer in an isolated environment:

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest --cov=bff_tools --cov-report=term-missing --cov-fail-under=95
```

Build the documentation with:

```bash
cd docs-site
npm install
npm run build
```

Tests must cover behavioral changes. Converter changes should include focused mapping cases and preserve semantic parity with the versioned references. Do not commit large annotation databases, full-cohort fixtures, generated browser reports, credentials, or local paths.

Keep changes scoped and update `CHANGELOG.md` only for user-visible behavior. Pull requests should explain the input affected, expected BFF behavior, compatibility implications, and verification performed.

Edit `README.md` directly, and keep its version and coverage badges current when either value changes.

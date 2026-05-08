# Utilities

In addition to `bff-tools`, the project includes a few optional utilities for browsing data and managing repeated jobs.

## Which one should I use?

| Tool | Use it when | Data source |
|---|---|---|
| `bff-browser` | You want to browse static BFF output without a database | local JSON or generated HTML |
| `bff-portal` | You want live queries over BFF data stored in MongoDB | MongoDB |
| `bff-queue` | You want to run and monitor many ingestion jobs on a workstation | local command queue |

## `bff-browser`

`bff-browser` is a lightweight web UI for browsing static BFF output such as `genomicVariations` and `individuals`.

Use it when:

- you want a simple local viewer
- you do not want to depend on MongoDB
- you want to inspect generated HTML or JSON output

For installation and usage details, see:

- [utils/bff_browser/README.md](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/utils/bff_browser)

## `bff-portal`

`bff-portal` provides a small API and web interface for querying BFF collections stored in MongoDB.

Use it when:

- your data is already in MongoDB
- you want live filtering and lookups
- you want a lightweight browser for database-backed BFF data

For installation and usage details, see:

- [utils/bff_portal/README.md](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/utils/bff_portal)

## `bff-queue`

`bff-queue` helps you submit and monitor many `bff-tools` jobs on a workstation or small server.

Use it when:

- you have many VCF or TSV jobs to process
- you want something more structured than shell loops
- you do not have a full HPC scheduler available

For installation and usage details, see:

- [utils/bff_queue/README.md](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/utils/bff_queue)

## Relationship to `bff-tools`

These utilities are optional. The main data-preparation workflow still goes through `bff-tools`:

1. validate metadata
2. convert genomic input
3. load BFF collections into MongoDB

Use the utilities only when you need browsing, lightweight querying, or job orchestration around that core workflow.

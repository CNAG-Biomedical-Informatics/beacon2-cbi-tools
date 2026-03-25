# Utilities

This directory contains small tools that complement `bff-tools`.

## Which one should I use?

| Tool | Use it when | Data source |
|---|---|---|
| [`bff-browser`](bff_browser/README.md) | You want to browse static BFF files without a database | local JSON or generated HTML |
| [`bff-portal`](bff_portal/README.md) | You want live queries over BFF data stored in MongoDB | MongoDB |
| [`bff-queue`](bff_queue/README.md) | You want to run and monitor many ingestion jobs on a workstation | local command queue |

## Short descriptions

### `bff-browser`

A lightweight web UI for browsing `genomicVariations` and `individuals` outside MongoDB.

### `bff-portal`

A small API and web interface for querying BFF collections stored in MongoDB.

### `bff-queue`

A queue wrapper based on Minion for launching and monitoring repeated CLI jobs.

For installation and usage details, open the README of the specific utility.

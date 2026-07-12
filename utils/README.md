# Utilities

This directory contains small tools that complement `bff-tools`.

## Which one should I use?

| Tool | Use it when | Data source |
|---|---|---|
| [`bff-portal`](bff_portal/README.md) | You want live queries over BFF data stored in MongoDB | MongoDB |
| [`bff-queue`](bff_queue/README.md) | You want to run and monitor many ingestion jobs on a workstation | local command queue |

## Short descriptions

### `bff-portal`

A small API and web interface for querying BFF collections stored in MongoDB.

### `bff-queue`

A queue wrapper based on Minion for launching and monitoring repeated CLI jobs.

For installation and usage details, open the README of the specific utility.

## Deprecated

The former Flask `bff-browser` is retained temporarily as
[`_bff_browser`](_bff_browser/README.md). Static browser reports are now
generated directly by `bff-tools` with `bff2html: true`.

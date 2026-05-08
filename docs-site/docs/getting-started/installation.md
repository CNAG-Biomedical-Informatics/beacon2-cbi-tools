---
title: Installation
---

# Installation

Choose the runtime model that matches your environment.

## Recommendation

Use **Docker** for a first local or server deployment. Use **Apptainer** on HPC systems where Docker is not available. Use the **non-containerized** path only when you explicitly need to manage Python, Perl, and system dependencies yourself.

| Path | Best for | Notes |
|---|---|---|
| [Docker](docker) | Workstations, servers, reproducible local deployments | Easiest path when Docker is available |
| [Apptainer](apptainer) | HPC systems and environments without Docker daemon access | Uses the same container image through Apptainer or Singularity |
| [Non-containerized](non-containerized) | Hosts where you want direct control over Python, Perl, and system dependencies | Most flexible, but requires more local dependency management |

All installation modes use the same core idea: prepare the large external reference data once, then point `bff-tools` to that data.

## Preflight Checklist

- Confirm that you have at least 200 GB of disk space for the full external data setup.
- Decide which reference genome your input uses before running genomic conversion.
- If you plan to use `load` or `full`, make sure MongoDB and `mongosh` are available.
- If you only want to validate metadata or inspect command behavior, start with the bundled test data first.

## After Installation

Check that the command is visible from your chosen runtime:

```bash
bin/bff-tools --help
```

After installation, continue with the [Quick Start](quick-start.md).

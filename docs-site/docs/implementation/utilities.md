---
title: Optional Utilities
---

# Optional Utilities

These are useful add-ons, but they are not required to run the main `bff-tools` workflow.

| Utility | Language | Purpose |
|---|---|---|
| `utils/bff_browser/app.py` | ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) | Lightweight local browser for static BFF output |
| `utils/bff_portal/backend/api.pl` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Backend API for querying BFF data stored in MongoDB |
| `utils/bff_portal/frontend/app.pl` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Web frontend for the MongoDB-backed BFF portal |
| `utils/bff_queue/bff-queue` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Queue helper for launching and monitoring repeated jobs |
| `utils/bff_queue/minion_ui.pl` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Web UI for queue monitoring |
| `utils/_models2xlsx/defaultSchema2xlsx.sh` | ![Shell](https://img.shields.io/badge/Shell-4EAA25?logo=gnubash&logoColor=white) | Helper for generating XLSX templates from Beacon model schemas |
| `utils/_models2xlsx/csv2xlsx` | ![Perl](https://img.shields.io/badge/Perl-39457E?logo=perl&logoColor=white) | Converts CSV schema tables into XLSX output |

## When To Use Them

- Use `bff_browser` when you want to inspect static BFF output without MongoDB.
- Use `bff_portal` when your data is already loaded in MongoDB and you want a lightweight query interface.
- Use `bff_queue` when you need to run repeated jobs on a workstation or small server.
- Use `_models2xlsx` only when maintaining or regenerating schema-derived XLSX templates.

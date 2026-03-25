# bff-portal

`bff-portal` is a small API and web interface for querying BFF collections stored in MongoDB. It is useful for quick inspection, live filtering, and simple cross-collection lookups.

## Requirements

- BFF data stored in MongoDB
- Perl dependencies:

```bash
cpanm --notest Mojolicious MongoDB
```

## What it provides

- a backend API for direct collection queries
- a lightweight frontend UI
- support for simple cross-collection queries
- pagination with `limit` and `skip`

This API is intentionally simple and does not aim to implement the full Beacon v2 API.

## Run the backend

Development:

```bash
morbo backend/api.pl
```

Production:

```bash
hypnotoad backend/api.pl
```

## Run the frontend

Development:

```bash
perl frontend/app.pl daemon -l http://0.0.0.0:8000
```

Production:

```bash
hypnotoad frontend/app.pl
```

Open the frontend at <http://localhost:8000> in development mode.

## Example API calls

Show databases:

```bash
curl http://localhost:3000/beacon/
```

Show a collection:

```bash
curl http://localhost:3000/beacon/analyses
```

Query by field:

```bash
curl http://localhost:3000/beacon/individuals/id/HG02600
curl http://localhost:3000/beacon/genomicVariations/molecularAttributes_geneIds/TP53
```

Query by two fields:

```bash
curl http://localhost:3000/beacon/genomicVariations/molecularAttributes_geneIds/ACE2/variantType/SNP
```

Paginate:

```bash
curl "http://localhost:3000/beacon/individuals?limit=20&skip=40"
```

Cross-collection examples:

```bash
curl "http://localhost:3000/beacon/cross/individuals/HG00096/genomicVariations?limit=5&skip=10"
curl "http://localhost:3000/beacon/cross/individuals/HG00096/analyses"
```

## Notes

- only `GET` requests are supported
- results are returned as raw JSON documents
- `genomicVariations` responses may be trimmed for performance

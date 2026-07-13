---
title: MongoDB Import
description: Import generated BFF collections into MongoDB with repeatable upserts and the legacy Beacon indexes.
---

`bff-tools` produces portable BFF files and does not install, configure, or run MongoDB. Sites that want a complete Beacon service can use a downstream implementation such as the [Beacon v2 Production Implementation](https://github.com/EGA-archive/beacon2-pi-api) or [bycon](https://codeberg.org/Progenetix/bycon/). Follow that project's data-loading guidance when it differs from the generic recipe below.

The examples require the [MongoDB Database Tools](https://www.mongodb.com/docs/database-tools/) and `mongosh`. They target the database named in the connection URI:

```bash
export MONGODB_URI='mongodb://root:example@localhost:27017/beacon?authSource=admin'
```

## Create Identity and Query Indexes

Create the indexes before importing so the upsert keys are efficient and unique. Save this as `create-bff-indexes.js`, then run `mongosh "$MONGODB_URI" --file create-bff-indexes.js`:

```javascript
const metadataCollections = [
  "analyses",
  "biosamples",
  "cohorts",
  "datasets",
  "individuals",
  "runs",
];

for (const name of metadataCollections) {
  const collection = db.getCollection(name);
  collection.createIndex(
    {id: 1},
    {name: `identity_${name}`, unique: true},
  );
  collection.createIndex(
    {"$**": 1},
    {name: `single_field_${name}`},
  );
  collection.createIndex(
    {"$**": "text"},
    {name: `text_${name}`},
  );
}

const variants = db.getCollection("genomicVariations");
variants.createIndex(
  {variantInternalId: 1, "_info.datasetId": 1},
  {name: "identity_genomicVariations", unique: true},
);
variants.createIndex(
  {"$**": 1},
  {name: "single_field_genomicVariations"},
);
variants.createIndex(
  {"$**": "text"},
  {name: "text_genomicVariations"},
);
```

The two wildcard indexes reproduce the indexes created by the former `bff-tools` MongoDB loader. They support queries over arbitrary BFF fields and full-text search, but can take substantial time and storage for large variant collections. Prefer narrower workload-specific indexes when the Beacon query patterns are known.

Calling [`createIndex()`](https://www.mongodb.com/docs/manual/reference/method/db.collection.createindex/) again with the same keys and options is idempotent: MongoDB returns the existing index instead of rebuilding it. Creating a same-named index with different keys or options is an error.

## Import Metadata

Each metadata file is a JSON array. Remove collections that are not present in the export:

```bash
for collection in analyses biosamples cohorts datasets individuals runs; do
  mongoimport \
    --uri "$MONGODB_URI" \
    --collection "$collection" \
    --file "bff/$collection.json" \
    --jsonArray \
    --mode=upsert \
    --upsertFields=id \
    --stopOnError
done
```

## Import Genomic Variations

For new runs, `--jsonl` produces a directly streamable `genomicVariationsVcf.jsonl.gz`:

```bash
bff-tools vcf -i cohort.vcf.gz --genome hg38 --dataset-id cohort-1 \
  --jsonl -c config.yaml

gzip -dc cohort-bff/vcf/genomicVariationsVcf.jsonl.gz \
  | mongoimport \
      --uri "$MONGODB_URI" \
      --collection genomicVariations \
      --mode=upsert \
      --upsertFields='variantInternalId,_info.datasetId' \
      --stopOnError
```

The default `genomicVariationsVcf.json.gz` remains a standard JSON array with one compact record per physical line. Strip its array delimiters and trailing commas while decompressing so `mongoimport` can stream it:

```bash
gzip -dc cohort-bff/vcf/genomicVariationsVcf.json.gz \
  | sed -e '1d' -e '$d' -e 's/,$//' \
  | mongoimport \
      --uri "$MONGODB_URI" \
      --collection genomicVariations \
      --mode=upsert \
      --upsertFields='variantInternalId,_info.datasetId' \
      --stopOnError
```

[`--mode=upsert`](https://www.mongodb.com/docs/database-tools/mongoimport/mongoimport-examples/#replace-matching-documents-during-import) replaces a document matching the selected identity fields and inserts it otherwise. With stable BFF identifiers, rerunning the same imports is therefore idempotent and does not create duplicate records. An upsert does not remove database documents that are absent from a newer input file; use a fresh database or an explicit reconciliation step when deletions must be reflected.

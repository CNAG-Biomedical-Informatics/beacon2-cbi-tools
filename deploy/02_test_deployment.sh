#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
DATA_DIR=${BFF_ANNOTATION_DATA:-}
DOWNLOAD_DIR=""

usage() {
    cat <<'EOF'
Usage:
  BFF_ANNOTATION_DATA=/absolute/path/to/data deploy/02_test_deployment.sh
  deploy/02_test_deployment.sh --download /directory/with/at-least-200GB-free

The first form reuses an extracted annotation bundle. The second downloads,
verifies, combines, and extracts the maintained bundle before testing it.
EOF
}

if [[ ${1:-} == "--download" ]]; then
    DOWNLOAD_DIR=${2:-}
    if [[ -z "$DOWNLOAD_DIR" ]]; then
        usage
        exit 2
    fi
    mkdir -p "$DOWNLOAD_DIR"
    python3 -m pip install gdown
    python3 "$ROOT/deploy/01_download_external_data.py" --out-dir "$DOWNLOAD_DIR"
    (
        cd "$DOWNLOAD_DIR"
        md5sum -c data.tar.gz.md5
        cat data.tar.gz.part-?? > data.tar.gz
        tar -xzf data.tar.gz
    )
    DATA_DIR="$DOWNLOAD_DIR/data"
elif [[ $# -gt 0 ]]; then
    usage
    exit 2
fi

if [[ -z "$DATA_DIR" || ! -d "$DATA_DIR" ]]; then
    usage
    exit 2
fi

for command in java python3; do
    command -v "$command" >/dev/null || {
        echo "Error: required command not found: $command" >&2
        exit 1
    }
done

WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
CONFIG="$WORK_DIR/config.yaml"
PROJECT="$WORK_DIR/annotation-integration"

python3 - "$ROOT/bin/config.yaml" "$CONFIG" "$DATA_DIR" <<'PY'
from pathlib import Path
import sys
import yaml

source, destination, data_dir = map(Path, sys.argv[1:])
config = yaml.safe_load(source.read_text(encoding="utf-8"))
config["base"] = str(data_dir.resolve())
destination.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
PY

for SNPEFF_CONFIG in \
    "$DATA_DIR/soft/snpEff/snpEff.config" \
    "$DATA_DIR/soft/NGSutils/snpEff_v5.0/snpEff.config"; do
    if [[ -f "$SNPEFF_CONFIG" ]]; then
        sed -i "s|^data.dir = .*|data.dir = $DATA_DIR/databases/snpeff/v5.0|" "$SNPEFF_CONFIG"
    fi
done

echo "Running full bcftools, SnpEff, dbNSFP, ClinVar, and COSMIC integration"
"$ROOT/bin/bff-tools" vcf \
    -i "$ROOT/testdata/vcf/test_1000G.vcf.gz" \
    -p "$ROOT/testdata/vcf/param.yaml" \
    -c "$CONFIG" \
    --annotate \
    --no-browser \
    -o "$PROJECT" \
    --no-emoji \
    --no-color

ACTUAL="$PROJECT/vcf/genomicVariationsVcf.json.gz"
EXPECTED="$ROOT/testdata/vcf/ref_beacon_166403275914916/vcf/genomicVariationsVcf.json.gz"

"$ROOT/bin/bff-tools" validate -i "$ACTUAL" --gv-vcf --no-emoji --no-color
PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 "$ROOT/tools/compare_bff_outputs.py" "$EXPECTED" "$ACTUAL"

echo "Full annotation integration passed"

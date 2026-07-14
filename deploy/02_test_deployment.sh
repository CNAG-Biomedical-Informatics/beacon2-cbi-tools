#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
# Keep the former integration-test-only name as a compatibility fallback.
DATA_DIR=${BFF_TOOLS_DATA:-${BFF_ANNOTATION_DATA:-}}
DOWNLOAD_DIR=""

usage() {
    cat <<'EOF'
Usage:
  BFF_TOOLS_DATA=/absolute/path/to/data deploy/02_test_deployment.sh
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
PROJECT="$WORK_DIR/annotation-integration"

echo "Running full bcftools, SnpEff, dbNSFP, ClinVar, and COSMIC integration"
BFF_TOOLS_DATA="$DATA_DIR" "$ROOT/bin/bff-tools" vcf \
    -i "$ROOT/testdata/vcf/test_1000G.vcf.gz" \
    -p "$ROOT/testdata/vcf/param.yaml" \
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

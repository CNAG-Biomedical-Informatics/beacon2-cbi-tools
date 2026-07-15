#!/usr/bin/env bash

set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
version=$(tr -d "[:space:]" < "$root/VERSION")
coverage=${COVERAGE:-97}

if [[ ! $coverage =~ ^[0-9]+$ ]] || (( coverage < 0 || coverage > 100 )); then
    echo "COVERAGE must be an integer from 0 to 100" >&2
    exit 1
fi

version_badge=${version//-/--}
sed \
    -e "s/@VERSION_BADGE@/$version_badge/g" \
    -e "s/@COVERAGE@/$coverage/g" \
    "$root/README.md.in" > "$root/README.md"

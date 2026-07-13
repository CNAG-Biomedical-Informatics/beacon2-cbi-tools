#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bff_tools.parity import compare_bff_files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare streamed BFF genomic-variation files semantically"
    )
    parser.add_argument("expected", type=Path)
    parser.add_argument("actual", type=Path)
    args = parser.parse_args()
    result = compare_bff_files(args.expected, args.actual)
    if not result.equal:
        print(f"First semantic difference: record {result.first_difference}")
        print(f"JSON path: {result.path}")
        print(f"Expected: {json.dumps(result.expected, ensure_ascii=False)[:1000]}")
        print(f"Actual: {json.dumps(result.actual, ensure_ascii=False)[:1000]}")
        return 1
    print(f"Semantic parity passed for {result.records} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

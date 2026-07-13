#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import io
import json
from pathlib import Path
from typing import Callable


Record = dict[str, object]


def parse_info(value: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in value.split(";"):
        key, separator, field_value = item.partition("=")
        parsed[key] = field_value if separator else "true"
    return parsed


def populated_prefix(info: dict[str, str], prefix: str) -> bool:
    return any(
        key.startswith(prefix) and value not in {"", "."}
        for key, value in info.items()
    )


def genotype_values(parts: list[str]) -> list[str]:
    if len(parts) < 10:
        return []
    fields = parts[8].split(":")
    if "GT" not in fields:
        return []
    index = fields.index("GT")
    values = []
    for sample in parts[9:]:
        sample_parts = sample.split(":")
        values.append(sample_parts[index] if index < len(sample_parts) else ".")
    return values


def build_record(parts: list[str]) -> Record:
    info = parse_info(parts[7])
    genotypes = genotype_values(parts)
    ann = info.get("ANN", "")
    reference = parts[3]
    alternates = parts[4].split(",")
    return {
        "chrom": parts[0],
        "position": int(parts[1]),
        "id": parts[2],
        "reference": reference,
        "alternates": alternates,
        "filter": parts[6],
        "info": info,
        "ann": ann,
        "genotypes": genotypes,
        "is_indel": any(len(reference) != len(alt) for alt in alternates),
        "is_symbolic": any(
            alt.startswith("<") or "[" in alt or "]" in alt for alt in alternates
        ),
    }


def criteria() -> list[tuple[str, Callable[[Record], bool]]]:
    return [
        ("clinvar_pathogenic", lambda row: "pathogenic" in str(row["info"]).lower()),
        ("clinvar", lambda row: populated_prefix(row["info"], "CLINVAR_")),
        ("cosmic", lambda row: populated_prefix(row["info"], "COSMIC_")),
        (
            "dense_dbnsfp",
            lambda row: sum(
                value not in {"", "."} for value in row["info"].values()
            )
            >= 40,
        ),
        ("ann_high", lambda row: "|HIGH|" in row["ann"]),
        ("ann_moderate", lambda row: "|MODERATE|" in row["ann"]),
        ("ann_low", lambda row: "|LOW|" in row["ann"]),
        ("ann_modifier", lambda row: "|MODIFIER|" in row["ann"]),
        ("multiple_transcripts", lambda row: str(row["ann"]).count(",") >= 3),
        ("indel", lambda row: bool(row["is_indel"])),
        ("symbolic", lambda row: bool(row["is_symbolic"])),
        (
            "missing_genotype",
            lambda row: any(value in {".", "./.", ".|."} for value in row["genotypes"]),
        ),
        (
            "homozygous_alternate",
            lambda row: any(value in {"1/1", "1|1"} for value in row["genotypes"]),
        ),
    ]


def open_deterministic_gzip(path: Path) -> io.TextIOWrapper:
    raw = path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    return io.TextIOWrapper(compressed, encoding="utf-8", newline="")


def extract(
    input_path: Path,
    output_path: Path,
    manifest_path: Path,
    *,
    baseline_records: int,
) -> None:
    wanted = criteria()
    matched: set[str] = set()
    selected_criteria: list[dict[str, object]] = []
    sample_count = 0
    written_records = 0
    symbolic_records = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(input_path, "rt", encoding="utf-8", errors="strict") as handle, open_deterministic_gzip(output_path) as output:
        record_number = 0
        for line in handle:
            if line.startswith("#"):
                output.write(line)
                if line.startswith("#CHROM"):
                    sample_count = max(0, len(line.rstrip("\n").split("\t")) - 9)
                continue
            record_number += 1
            parts = line.rstrip("\n").split("\t")
            record = build_record(parts)
            matched_criterion = None
            for name, predicate in wanted:
                if name in matched or not predicate(record):
                    continue
                matched_criterion = name
                matched.add(name)
                selected_criteria.append(
                    {
                        "criterion": name,
                        "recordNumber": record_number,
                        "variant": (
                            f"{record['chrom']}:{record['position']}:"
                            f"{record['reference']}:{','.join(record['alternates'])}"
                        ),
                    }
                )
                break

            if record_number <= baseline_records or matched_criterion is not None:
                output.write(line)
                written_records += 1
                symbolic_records += int(bool(record["is_symbolic"]))

            if record_number >= baseline_records and len(matched) == len(wanted):
                break

    missing = [name for name, _ in wanted if name not in matched]
    if missing:
        raise RuntimeError(f"Source VCF does not satisfy fixture criteria: {', '.join(missing)}")

    manifest = {
        "baselineRecords": baseline_records,
        "description": "Compact records extracted from the fully annotated CINECA chr22 VCF",
        "fixtureRecords": written_records,
        "currentPerlExpectedBffRecords": written_records - symbolic_records,
        "notes": "The current Perl converter does not emit the selected symbolic copy-number alleles.",
        "samples": sample_count,
        "source": input_path.name,
        "symbolicRecords": symbolic_records,
        "targetedRecords": selected_criteria,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--baseline-records", type=int, default=5000)
    args = parser.parse_args()
    if args.baseline_records < 1:
        parser.error("--baseline-records must be positive")
    extract(
        args.input,
        args.output,
        args.manifest,
        baseline_records=args.baseline_records,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

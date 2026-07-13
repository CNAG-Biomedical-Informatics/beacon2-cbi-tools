from __future__ import annotations

import argparse
import gzip
import html
import json
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Iterable

try:
    import orjson as _orjson
except ImportError:  # The standard library codec remains fully supported.
    _orjson = None


ASSET_DIR = Path(__file__).with_name("browser_assets")
TEMPLATE_FILE = ASSET_DIR / "report.html"
VENDOR_DIR = ASSET_DIR / "vendor"
TABULATOR_CSS = VENDOR_DIR / "tabulator-6.5.0.min.css"
TABULATOR_JS = VENDOR_DIR / "tabulator-6.5.0.min.js"
REPORT_DATA_MARKER = "__REPORT_DATA__"
ROWS_MARKER = "__BFF_TOOLS_STREAMED_ROWS__"
LARGE_REPORT_ROWS = 50_000
LARGE_REPORT_BYTES = 100 * 1024 * 1024

COLUMNS = [
    ("variantInternalId", "Variant"),
    ("assemblyId", "Assembly"),
    ("refseqId", "Reference sequence"),
    ("position", "Position"),
    ("referenceBases", "Ref"),
    ("alternateBases", "Alt"),
    ("QUAL", "QUAL"),
    ("FILTER", "FILTER"),
    ("variantType", "Type"),
    ("genomicHGVSId", "HGVS"),
    ("geneIds", "Genes"),
    ("molecularEffects", "Molecular effects"),
    ("aminoacidChanges", "Amino acid changes"),
    ("annotationImpact", "Impact"),
    ("conditionId", "Conditions"),
    ("dbSNP", "dbSNP"),
    ("ClinVar", "ClinVar"),
    ("clinicalRelevance", "Clinical relevance"),
    ("biosampleId", "Biosamples"),
]


class BrowserError(RuntimeError):
    pass


def _decode_json(value: bytes) -> Any:
    if _orjson is not None:
        return _orjson.loads(value)
    return json.loads(value)


def _encode_json(value: Any) -> bytes:
    if _orjson is not None:
        return _orjson.dumps(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def iter_bff_variants(path: Path) -> Iterator[dict[str, Any]]:
    process: subprocess.Popen[bytes] | None = None
    try:
        jsonl = path.name.endswith((".jsonl", ".jsonl.gz"))
        opener = gzip.open if path.suffix == ".gz" else Path.open
        with opener(path, "rb") as handle:
            first_token = handle.read(4096).lstrip()[:1]
            if jsonl and first_token not in (b"", b"{"):
                raise BrowserError(f"BFF input <{path}> must contain JSON Lines objects")
            if not jsonl and first_token != b"[":
                raise BrowserError(f"BFF input <{path}> must contain a JSON array")

        command = "zgrep" if path.suffix == ".gz" else "grep"
        process = subprocess.Popen(
            [command, "-F", "-w", "-e", "HIGH", "-e", "MODERATE", "--", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdout is not None
        for raw in process.stdout:
            encoded = raw.strip()
            if encoded.endswith(b","):
                encoded = encoded[:-1].rstrip()
            item = _decode_json(encoded)
            if not isinstance(item, dict):
                raise BrowserError(
                    f"BFF input <{path}> must use one JSON object per line"
                )
            yield item

        assert process.stderr is not None
        stderr = process.stderr.read().decode("utf-8", errors="replace").strip()
        returncode = process.wait()
        if returncode not in (0, 1):
            detail = stderr or f"{command} exited with status {returncode}"
            raise BrowserError(f"Cannot filter BFF input <{path}>: {detail}")
    except OSError as exc:
        raise BrowserError(f"Cannot read BFF input <{path}>: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise BrowserError(f"Cannot parse BFF input <{path}>: {exc}") from exc
    finally:
        if process is not None:
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
            if process.poll() is None:
                process.terminate()
            process.wait()


def load_gene_panels(panel_dir: Path) -> dict[str, set[str]]:
    if not panel_dir.is_dir():
        raise BrowserError(f"Gene panel directory does not exist: <{panel_dir}>")

    panels: dict[str, set[str]] = {}
    for panel_file in sorted(panel_dir.glob("*.lst")):
        genes = {
            line.strip()
            for line in panel_file.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        panels[panel_file.stem] = genes
    if not panels:
        raise BrowserError(f"No .lst gene panels found in <{panel_dir}>")
    return panels


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _join(values: Iterable[Any]) -> str:
    result: list[str] = []
    for value in values:
        text = str(value).strip() if value is not None else ""
        if text and text not in result:
            result.append(text)
    return ", ".join(result)


def _gene_candidates(values: Iterable[Any]) -> set[str]:
    candidates: set[str] = set()
    for value in values:
        text = str(value).strip() if value is not None else ""
        if not text:
            continue
        for token in re.split(r"[,;/|\s]+", text):
            if not token:
                continue
            candidates.add(token)
            candidates.update(part for part in token.split("-") if part)
    return candidates


def _clinical_interpretations(variant: dict[str, Any]) -> list[dict[str, Any]]:
    level = variant.get("variantLevelData")
    if not isinstance(level, dict):
        return []
    return [item for item in _list(level.get("clinicalInterpretations")) if isinstance(item, dict)]


def _external_ids(variant: dict[str, Any], prefix: str) -> list[str]:
    identifiers = variant.get("identifiers")
    if not isinstance(identifiers, dict):
        return []
    result: list[str] = []
    for item in _list(identifiers.get("variantAlternativeIds")):
        if not isinstance(item, dict):
            continue
        value = str(item.get("id", ""))
        if value.startswith(prefix + ":"):
            result.extend(part.strip() for part in value.removeprefix(prefix + ":").split(",") if part.strip())
    return result


def variant_to_row(variant: dict[str, Any]) -> dict[str, Any]:
    position = variant.get("_position") if isinstance(variant.get("_position"), dict) else {}
    variation = variant.get("variation") if isinstance(variant.get("variation"), dict) else {}
    location = variation.get("location") if isinstance(variation.get("location"), dict) else {}
    interval = location.get("interval") if isinstance(location.get("interval"), dict) else {}
    start = interval.get("start") if isinstance(interval.get("start"), dict) else {}
    quality = variant.get("variantQuality") if isinstance(variant.get("variantQuality"), dict) else {}
    molecular = variant.get("molecularAttributes") if isinstance(variant.get("molecularAttributes"), dict) else {}
    identifiers = variant.get("identifiers") if isinstance(variant.get("identifiers"), dict) else {}

    effects = [
        item.get("label", item.get("id", ""))
        for item in _list(molecular.get("molecularEffects"))
        if isinstance(item, dict)
    ]
    interpretations = _clinical_interpretations(variant)
    conditions: list[str] = []
    primary_condition = ""
    relevance = []
    for item in interpretations:
        effect = item.get("effect") if isinstance(item.get("effect"), dict) else {}
        label = effect.get("label") or effect.get("id")
        identifier = effect.get("id")
        if label and identifier and label != identifier:
            condition = f"{label} ({identifier})"
        elif label:
            condition = str(label)
        else:
            condition = ""
        if condition and condition not in conditions:
            conditions.append(condition)
            if not primary_condition:
                primary_condition = str(label)
        if item.get("clinicalRelevance"):
            relevance.append(item["clinicalRelevance"])

    biosamples = []
    for item in _list(variant.get("caseLevelData")):
        if not isinstance(item, dict):
            continue
        sample_id = str(item.get("biosampleId", "")).strip()
        zygosity = item.get("zygosity") if isinstance(item.get("zygosity"), dict) else {}
        genotype = str(zygosity.get("label", "")).strip()
        depth = item.get("depth")
        if depth is None:
            depth = item.get("DP")
        detail = genotype + (f":{depth}" if depth not in (None, "") else "")
        biosamples.append(f"{sample_id} ({detail})" if sample_id and detail else sample_id or detail)

    genes = _list(molecular.get("geneIds"))
    impacts = _list(molecular.get("annotationImpact"))
    row = {
        "variantInternalId": variant.get("variantInternalId", ""),
        "assemblyId": position.get("assemblyId", ""),
        "refseqId": position.get("refseqId", ""),
        "position": start.get("value", position.get("startInteger", "")),
        "referenceBases": variation.get("referenceBases", ""),
        "alternateBases": variation.get("alternateBases", ""),
        "QUAL": quality.get("QUAL", ""),
        "FILTER": quality.get("FILTER", ""),
        "variantType": variation.get("variantType", ""),
        "genomicHGVSId": identifiers.get("genomicHGVSId", ""),
        "geneIds": _join(genes),
        "molecularEffects": _join(effects),
        "aminoacidChanges": _join(_list(molecular.get("aminoacidChanges"))),
        "annotationImpact": _join(impacts),
        "conditionId": _join(conditions),
        "dbSNP": _join(_external_ids(variant, "dbSNP")),
        "ClinVar": _join(_external_ids(variant, "ClinVar")),
        "clinicalRelevance": _join(relevance),
        "biosampleId": _join(biosamples),
        "_genes": sorted(_gene_candidates(genes)),
        "_conditionCount": len(conditions),
        "_primaryCondition": primary_condition,
    }
    row["_pathogenic"] = "pathogenic" in row["clinicalRelevance"].lower()
    row["_homAlt"] = bool(re.search(r"(?:^|[^0-9])1[/|]1(?:[^0-9]|$)", row["biosampleId"]))
    return row


def iter_report_rows(
    variants: Iterable[dict[str, Any]],
    panels: dict[str, set[str]],
) -> Iterator[dict[str, Any]]:
    for variant in variants:
        molecular = (
            variant.get("molecularAttributes")
            if isinstance(variant.get("molecularAttributes"), dict)
            else {}
        )
        impacts = {
            str(impact).strip().upper()
            for impact in _list(molecular.get("annotationImpact"))
            if str(impact).strip()
        }
        if not impacts.intersection({"HIGH", "MODERATE"}):
            continue
        row_genes = _gene_candidates(_list(molecular.get("geneIds")))
        matched = [name for name, genes in panels.items() if row_genes.intersection(genes)]
        if not matched:
            continue

        # Build biosample-heavy display fields only for variants retained in the report.
        row = variant_to_row(variant)
        row.pop("_genes")
        row["_panels"] = matched
        yield row


def _report_payload(
    *,
    rows: Any,
    panels: dict[str, set[str]],
    panel_counts: dict[str, int],
    project_id: str,
    job_id: str,
    source_name: str,
    variants: int,
    pathogenic: int,
    hom_alt: int,
    warning: str | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "variants": variants,
        "panels": sum(1 for count in panel_counts.values() if count),
        "pathogenic": pathogenic,
        "homAlt": hom_alt,
    }
    if warning:
        summary["warning"] = warning

    return {
        "projectId": project_id,
        "jobId": job_id,
        "source": source_name,
        "columns": [{"key": key, "label": label} for key, label in COLUMNS],
        "rows": rows,
        "panels": panel_counts,
        "panelGenes": {name: len(genes) for name, genes in panels.items()},
        "summary": summary,
    }


def build_report_payload(
    variants: Iterable[dict[str, Any]],
    panels: dict[str, set[str]],
    *,
    project_id: str,
    job_id: str,
    source_name: str,
) -> dict[str, Any]:
    selected = list(iter_report_rows(variants, panels))
    panel_counts = {name: 0 for name in panels}
    for row in selected:
        for name in row["_panels"]:
            panel_counts[name] += 1
    return _report_payload(
        rows=selected,
        panels=panels,
        panel_counts=panel_counts,
        project_id=project_id,
        job_id=job_id,
        source_name=source_name,
        variants=len(selected),
        pathogenic=sum(1 for row in selected if row["_pathogenic"]),
        hom_alt=sum(1 for row in selected if row["_homAlt"]),
    )


def _json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def _render_report_frame(payload: dict[str, Any]) -> str:
    try:
        template = TEMPLATE_FILE.read_text(encoding="utf-8")
        tabulator_css = TABULATOR_CSS.read_text(encoding="utf-8")
        tabulator_js = TABULATOR_JS.read_text(encoding="utf-8")
    except OSError as exc:
        raise BrowserError(f"Cannot read browser template assets: {exc}") from exc
    return (
        template.replace("__TABULATOR_CSS__", tabulator_css)
        .replace("__TABULATOR_JS__", tabulator_js.replace("</script", "<\\/script"))
        .replace("__PROJECT_ID__", html.escape(str(payload["projectId"])))
        .replace("__JOB_ID__", html.escape(str(payload["jobId"])))
        .replace("__SOURCE_FILE__", html.escape(str(payload["source"])))
    )


def render_report(payload: dict[str, Any]) -> str:
    return _render_report_frame(payload).replace(REPORT_DATA_MARKER, _json_for_script(payload))


def _large_report_warning(variants: int, row_bytes: int) -> str | None:
    if variants < LARGE_REPORT_ROWS and row_bytes < LARGE_REPORT_BYTES:
        return None
    size_mib = row_bytes / (1024 * 1024)
    return (
        f"The standalone browser contains {variants:,} panel-matched variants "
        f"({size_mib:.1f} MiB of embedded row data) and may require substantial "
        "browser memory. Use narrower gene panels or disable bff2html for very "
        "large cohorts."
    )


def generate_browser_report(
    input_path: Path,
    panel_dir: Path,
    output_path: Path,
    *,
    project_id: str,
    job_id: str,
) -> dict[str, Any]:
    panels = load_gene_panels(panel_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel_counts = {name: 0 for name in panels}
    variants = pathogenic = hom_alt = 0

    try:
        with tempfile.TemporaryFile(mode="w+b", dir=output_path.parent) as rows_file:
            rows = iter_report_rows(
                iter_bff_variants(input_path),
                panels,
            )
            for row in rows:
                if variants:
                    rows_file.write(b",")
                rows_file.write(_encode_json(row).replace(b"</", b"<\\/"))
                variants += 1
                pathogenic += int(row["_pathogenic"])
                hom_alt += int(row["_homAlt"])
                for name in row["_panels"]:
                    panel_counts[name] += 1

            row_bytes = rows_file.tell()
            warning = _large_report_warning(variants, row_bytes)
            payload = _report_payload(
                rows=ROWS_MARKER,
                panels=panels,
                panel_counts=panel_counts,
                project_id=project_id,
                job_id=job_id,
                source_name=input_path.name,
                variants=variants,
                pathogenic=pathogenic,
                hom_alt=hom_alt,
                warning=warning,
            )
            report_json = _json_for_script(payload)
            quoted_rows_marker = _json_for_script(ROWS_MARKER)
            json_prefix, json_suffix = report_json.split(quoted_rows_marker, 1)
            html_prefix, html_suffix = _render_report_frame(payload).split(
                REPORT_DATA_MARKER, 1
            )

            rows_file.seek(0)
            with output_path.open("wb") as output:
                output.write(html_prefix.encode("utf-8"))
                output.write(json_prefix.encode("utf-8"))
                output.write(b"[")
                shutil.copyfileobj(rows_file, output, length=1024 * 1024)
                output.write(b"]")
                output.write(json_suffix.encode("utf-8"))
                output.write(html_suffix.encode("utf-8"))
    except OSError as exc:
        raise BrowserError(f"Cannot write browser report <{output_path}>: {exc}") from exc

    return payload["summary"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a standalone BFF Tools Browser report")
    parser.add_argument("-i", "--input", required=True, type=Path)
    parser.add_argument("--panel-dir", required=True, type=Path)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("-o", "--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        generate_browser_report(
            args.input,
            args.panel_dir,
            args.output,
            project_id=args.project_id,
            job_id=args.job_id,
        )
    except BrowserError as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

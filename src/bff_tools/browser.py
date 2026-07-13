from __future__ import annotations

import argparse
import gzip
import html
import json
import re
from pathlib import Path
from typing import Any, Iterable


ROOT_DIR = Path(__file__).resolve().parents[2]
ASSET_DIR = Path(__file__).with_name("browser_assets")
TEMPLATE_FILE = ASSET_DIR / "report.html"
VENDOR_DIR = ASSET_DIR / "vendor"
TABULATOR_CSS = VENDOR_DIR / "tabulator-6.5.0.min.css"
TABULATOR_JS = VENDOR_DIR / "tabulator-6.5.0.min.js"

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


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def load_bff_variants(path: Path) -> list[dict[str, Any]]:
    try:
        with _open_text(path) as handle:
            payload = json.load(handle)
    except OSError as exc:
        raise BrowserError(f"Cannot read BFF input <{path}>: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise BrowserError(f"Cannot parse BFF input <{path}>: {exc}") from exc

    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise BrowserError(f"BFF input <{path}> must contain a top-level JSON array of objects")
    return payload


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
    conditions = []
    relevance = []
    for item in interpretations:
        effect = item.get("effect") if isinstance(item.get("effect"), dict) else {}
        label = effect.get("label") or effect.get("id")
        identifier = effect.get("id")
        if label and identifier and label != identifier:
            conditions.append(f"{label} ({identifier})")
        elif label:
            conditions.append(label)
        if item.get("clinicalRelevance"):
            relevance.append(item["clinicalRelevance"])

    biosamples = []
    for item in _list(variant.get("caseLevelData")):
        if not isinstance(item, dict):
            continue
        sample_id = str(item.get("biosampleId", "")).strip()
        zygosity = item.get("zygosity") if isinstance(item.get("zygosity"), dict) else {}
        genotype = str(zygosity.get("label", "")).strip()
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
    }
    row["_pathogenic"] = "pathogenic" in row["clinicalRelevance"].lower()
    row["_homAlt"] = bool(re.search(r"(?:^|[^0-9])1[/|]1(?:[^0-9]|$)", row["biosampleId"]))
    return row


def build_report_payload(
    variants: Iterable[dict[str, Any]],
    panels: dict[str, set[str]],
    *,
    project_id: str,
    job_id: str,
    source_name: str,
) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    panel_rows = {name: [] for name in panels}
    for variant in variants:
        row = variant_to_row(variant)
        impacts = {part.strip().upper() for part in row["annotationImpact"].split(",")}
        if not impacts.intersection({"HIGH", "MODERATE"}):
            continue
        row_genes = set(row.pop("_genes"))
        matched = [name for name, genes in panels.items() if row_genes.intersection(genes)]
        if not matched:
            continue
        row["_panels"] = matched
        selected.append(row)
        for name in matched:
            panel_rows[name].append(row)

    return {
        "projectId": project_id,
        "jobId": job_id,
        "source": source_name,
        "columns": [{"key": key, "label": label} for key, label in COLUMNS],
        "rows": selected,
        "panels": {name: len(rows) for name, rows in panel_rows.items()},
        "panelGenes": {name: len(genes) for name, genes in panels.items()},
        "summary": {
            "variants": len(selected),
            "panels": sum(1 for rows in panel_rows.values() if rows),
            "pathogenic": sum(1 for row in selected if row["_pathogenic"]),
            "homAlt": sum(1 for row in selected if row["_homAlt"]),
        },
    }


def _json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_report(payload: dict[str, Any]) -> str:
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
        .replace("__REPORT_DATA__", _json_for_script(payload))
    )


def generate_browser_report(
    input_path: Path,
    panel_dir: Path,
    output_path: Path,
    *,
    project_id: str,
    job_id: str,
) -> dict[str, Any]:
    variants = load_bff_variants(input_path)
    panels = load_gene_panels(panel_dir)
    payload = build_report_payload(
        variants,
        panels,
        project_id=project_id,
        job_id=job_id,
        source_name=input_path.name,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(payload), encoding="utf-8")
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

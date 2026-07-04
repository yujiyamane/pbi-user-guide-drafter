import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pbip_loader import load_pbip
from report_parser import parse_report
from model_parser import parse_model
from bookmark_parser import parse_bookmarks

SKIP_WORDS = {"ID", "IS", "IN", "TO", "OF", "OR", "AND", "NOT", "NO", "ON", "AT", "BE", "DO", "GO", "IT", "SO", "UP", "BY", "AS"}
KPI_TYPES = {"card", "multiRowCard", "kpi"}


def _extract_acronyms(model_raw: dict) -> list:
    seen = {}
    for table in model_raw["tables"]:
        name = table["name"]
        for token in re.split(r"[_\s]+", name):
            if re.match(r"^[A-Z]{2,}$", token) and token not in SKIP_WORDS:
                if token not in seen:
                    seen[token] = f"table: {name}"
        for col in table.get("columns", []):
            for token in re.split(r"[_\s]+", col["name"]):
                if re.match(r"^[A-Z]{2,}$", token) and token not in SKIP_WORDS:
                    if token not in seen:
                        seen[token] = f"column: {name}.{col['name']}"
        for mea in table.get("measures", []):
            for token in re.split(r"[_\s]+", mea["name"]):
                if re.match(r"^[A-Z]{2,}$", token) and token not in SKIP_WORDS:
                    if token not in seen:
                        seen[token] = f"measure: {name}.{mea['name']}"
    return [{"acronym": k, "found_in": v} for k, v in seen.items()]


def _extract_kpi_visuals(report_raw: dict) -> dict:
    result = {}
    for page in report_raw["pages"]:
        kpis = [
            {"title": v.get("title", ""), "fields": v.get("fields", []), "visualType": v.get("visualType", "")}
            for v in page["visuals"]
            if v.get("visualType", "") in KPI_TYPES and not v.get("isHidden", False)
        ]
        result[page["displayName"]] = kpis
    return result


def _normalize_visual(v: dict) -> dict:
    fields = []
    for f in v.get("fields", []):
        if isinstance(f, dict):
            fields.append(f.get("display", ""))
        else:
            fields.append(str(f))
    return {
        "visual_id": v["id"],
        "visualType": v.get("visualType", ""),
        "title": v.get("title", ""),
        "fields": fields,
        "filters": [],
        "position": v.get("position", {}),
    }


def _normalize_page(page: dict, order: int) -> dict:
    return {
        "displayName": page["displayName"],
        "page_id": page["id"],
        "order": order,
        "filters": [],
        "visuals": [_normalize_visual(v) for v in page["visuals"] if not v.get("isHidden")],
    }


def _normalize_table(t: dict) -> dict:
    return {
        "name": t["name"],
        "columns": [
            {
                "name": c["name"],
                "dataType": c.get("dataType", ""),
                "sourceColumn": c.get("sourceColumn", c["name"]),
                "isHidden": c.get("isHidden", False),
            }
            for c in t.get("columns", [])
        ],
        "measures": [
            {
                "name": m["name"],
                "expression": m.get("expression", ""),
                "description": "",
                "formatString": m.get("formatString", ""),
            }
            for m in t.get("measures", [])
        ],
    }


def _normalize_relationship(r: dict) -> dict:
    return {
        "fromTable": r.get("from_table", ""),
        "fromColumn": r.get("from_column", ""),
        "toTable": r.get("to_table", ""),
        "toColumn": r.get("to_column", ""),
        "cardinality": "manyToOne",
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python parse_pbip.py <path_to.pbip>", file=sys.stderr)
        sys.exit(1)

    pbip_path = Path(sys.argv[1])

    if not pbip_path.exists():
        print(f"Error: File not found: {pbip_path}", file=sys.stderr)
        print("Fix: Provide the full path to a valid .pbip file", file=sys.stderr)
        sys.exit(1)

    print("Loading PBIP...", file=sys.stderr)
    paths = load_pbip(pbip_path)

    print("Parsing report...", file=sys.stderr)
    report_raw = parse_report(paths["report_path"])

    print("Parsing semantic model...", file=sys.stderr)
    model_raw = parse_model(paths["model_path"])

    print("Parsing bookmarks...", file=sys.stderr)
    bookmarks = parse_bookmarks(paths["report_path"])

    report = {
        "format": report_raw["format"],
        "pages": [_normalize_page(p, i) for i, p in enumerate(report_raw["pages"])],
    }

    model = {
        "format": model_raw["format"],
        "tables": [_normalize_table(t) for t in model_raw["tables"]],
        "relationships": [_normalize_relationship(r) for r in model_raw.get("relationships", [])],
    }

    sources = model_raw.get("sources", [])
    acronyms = _extract_acronyms(model_raw)
    kpi_visuals = _extract_kpi_visuals(report_raw)

    result = {
        "name": pbip_path.stem,
        "pbip_path": str(pbip_path),
        "report": report,
        "model": model,
        "bookmarks": bookmarks,
        "sources": sources,
        "acronyms": acronyms,
        "kpi_visuals": kpi_visuals,
    }

    print("Done.", file=sys.stderr)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

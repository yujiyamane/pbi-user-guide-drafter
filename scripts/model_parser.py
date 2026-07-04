import json
import re
from pathlib import Path


def _parse_tmdl_table(tmdl_text: str, table_name: str) -> dict:
    measures = []
    columns = []
    lines = tmdl_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        measure_match = re.match(r"^\s+measure\s+(.+?)\s*=\s*(.*)", line)
        if measure_match:
            name = measure_match.group(1).strip().strip("'")
            expr_start = measure_match.group(2).strip()
            expr_lines = [expr_start] if expr_start else []
            fmt = ""
            j = i + 1
            while j < len(lines):
                next_stripped = lines[j].strip()
                if next_stripped.startswith("formatString:"):
                    fmt = next_stripped.split(":", 1)[1].strip()
                    j += 1
                    continue
                indent = len(lines[j]) - len(lines[j].lstrip())
                cur_indent = len(line) - len(line.lstrip())
                if indent <= cur_indent and lines[j].strip() and not lines[j].strip().startswith("//"):
                    if re.match(r"^\s+(measure|column|partition|annotation|ref)\s", lines[j]):
                        break
                    if re.match(r"^\s+(measure|column|partition|annotation|ref)\b", lines[j]):
                        break
                if next_stripped.startswith(("measure ", "column ", "partition ", "annotation ", "lineageTag:")):
                    break
                if expr_start or next_stripped:
                    if not next_stripped.startswith(("lineageTag:", "annotation ", "formatString:")):
                        expr_lines.append(next_stripped)
                j += 1
            measures.append({
                "name": name,
                "expression": " ".join(expr_lines).strip(),
                "formatString": fmt,
            })
            i = j
            continue

        col_match = re.match(r"^\s+column\s+'?(.+?)'?\s*$", line)
        if col_match:
            col_name = col_match.group(1).strip()
            data_type = ""
            is_hidden = False
            fmt = ""
            j = i + 1
            while j < len(lines):
                ns = lines[j].strip()
                if ns.startswith("dataType:"):
                    data_type = ns.split(":", 1)[1].strip()
                elif ns == "isHidden":
                    is_hidden = True
                elif ns.startswith("formatString:"):
                    fmt = ns.split(":", 1)[1].strip()
                elif re.match(r"^\s+(measure|column|partition|annotation)\s", lines[j]):
                    break
                elif ns.startswith(("measure ", "column ", "partition ")):
                    break
                j += 1
            columns.append({
                "name": col_name,
                "dataType": data_type,
                "formatString": fmt,
                "isHidden": is_hidden,
            })
            i = j
            continue

        i += 1

    return {"name": table_name, "measures": measures, "columns": columns}


def _parse_tmdl_relationships(tmdl_text: str) -> list:
    relationships = []
    for block in re.split(r"relationship\s+\S+", tmdl_text)[1:]:
        from_match = re.search(r"fromColumn:\s+(.+)", block)
        to_match = re.search(r"toColumn:\s+(.+)", block)
        if from_match and to_match:
            from_col = from_match.group(1).strip().strip("'")
            to_col = to_match.group(1).strip().strip("'")
            parts_from = from_col.split(".")
            parts_to = to_col.split(".")
            relationships.append({
                "from_table": parts_from[0].strip("'"),
                "from_column": parts_from[1].strip("'") if len(parts_from) > 1 else from_col,
                "to_table": parts_to[0].strip("'"),
                "to_column": parts_to[1].strip("'") if len(parts_to) > 1 else to_col,
            })
    return relationships


def _parse_sources_from_tmdl(tmdl_text: str, table_name: str) -> dict | None:
    partition_match = re.search(r"^\s+partition\s+.+?\s*=\s*(\S+)", tmdl_text, re.MULTILINE)
    if not partition_match:
        return None
    partition_type = partition_match.group(1).strip()
    if partition_type != "m":
        return {"table": table_name, "type": partition_type, "query_snippet": ""}
    source_match = re.search(r"^\s+source\s*=\s*\n(.*)", tmdl_text, re.MULTILINE | re.DOTALL)
    if not source_match:
        return {"table": table_name, "type": partition_type, "query_snippet": ""}
    raw = source_match.group(1)
    lines = raw.splitlines()
    source_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("annotation ", "lineageTag:")):
            break
        source_lines.append(stripped)
    snippet = " ".join(source_lines).strip()[:200]
    return {"table": table_name, "type": partition_type, "query_snippet": snippet}


def _parse_tmdl(model_path: Path) -> dict:
    tables_dir = model_path / "definition" / "tables"
    tables = []
    sources = []
    for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
        text = tmdl_file.read_text(encoding="utf-8-sig")
        name_match = re.match(r"^table\s+'?(.+?)'?\s*$", text.strip().splitlines()[0])
        table_name = name_match.group(1) if name_match else tmdl_file.stem
        tables.append(_parse_tmdl_table(text, table_name))
        source_info = _parse_sources_from_tmdl(text, table_name)
        if source_info is not None:
            sources.append(source_info)

    rel_file = model_path / "definition" / "relationships.tmdl"
    relationships = []
    if rel_file.exists():
        relationships = _parse_tmdl_relationships(rel_file.read_text(encoding="utf-8-sig"))

    return {"format": "TMDL", "tables": tables, "relationships": relationships, "sources": sources}


def _parse_tmsl(model_path: Path) -> dict:
    data = json.loads((model_path / "model.bim").read_text(encoding="utf-8-sig"))
    model = data.get("model", data)
    tables = []
    for t in model.get("tables", []):
        measures = [
            {
                "name": m["name"],
                "expression": m.get("expression", ""),
                "formatString": m.get("formatString", ""),
            }
            for m in t.get("measures", [])
        ]
        columns = [
            {
                "name": c["name"],
                "dataType": c.get("dataType", ""),
                "formatString": c.get("formatString", ""),
                "isHidden": c.get("isHidden", False),
            }
            for c in t.get("columns", [])
        ]
        tables.append({"name": t["name"], "measures": measures, "columns": columns})

    relationships = []
    for r in model.get("relationships", []):
        relationships.append({
            "from_table": r.get("fromTable", ""),
            "from_column": r.get("fromColumn", ""),
            "to_table": r.get("toTable", ""),
            "to_column": r.get("toColumn", ""),
        })

    return {"format": "TMSL", "tables": tables, "relationships": relationships}


def parse_model(model_path: Path) -> dict:
    model_path = Path(model_path)
    if (model_path / "definition").is_dir():
        return _parse_tmdl(model_path)
    if (model_path / "model.bim").exists():
        return _parse_tmsl(model_path)
    raise ValueError(f"Unrecognised model format at: {model_path}")

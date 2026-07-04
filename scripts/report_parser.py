import json
from pathlib import Path


def _extract_title(visual_data: dict) -> str:
    try:
        title_obj = visual_data["visualContainerObjects"]["title"][0]
        return title_obj["properties"]["text"]["expr"]["Literal"]["Value"].strip("'")
    except (KeyError, IndexError, TypeError):
        return ""


def _extract_fields(query_state: dict) -> list:
    fields = []
    for role, role_data in query_state.items():
        for proj in role_data.get("projections", []):
            display = proj.get("displayName") or proj.get("nativeQueryRef") or proj.get("queryRef", "")
            fields.append({"role": role, "display": display})
    return fields


def _parse_visual(visual_path: Path) -> dict:
    data = json.loads(visual_path.read_text(encoding="utf-8-sig"))
    v = data.get("visual", {})
    query_state = v.get("query", {}).get("queryState", {})
    return {
        "id": data["name"],
        "visualType": v.get("visualType", ""),
        "title": _extract_title(v),
        "position": data.get("position", {}),
        "fields": _extract_fields(query_state),
        "isHidden": data.get("isHidden", False),
    }


def _parse_page_pbir(page_dir: Path) -> dict:
    page_data = json.loads((page_dir / "page.json").read_text(encoding="utf-8-sig"))
    visuals_dir = page_dir / "visuals"
    visuals = []
    if visuals_dir.is_dir():
        for v_dir in sorted(visuals_dir.iterdir()):
            vf = v_dir / "visual.json"
            if vf.exists():
                visuals.append(_parse_visual(vf))
    return {
        "id": page_data["name"],
        "displayName": page_data.get("displayName", page_data["name"]),
        "width": page_data.get("width", 1280),
        "height": page_data.get("height", 720),
        "visuals": visuals,
    }


def _parse_pbir(report_path: Path) -> dict:
    pages_meta = json.loads(
        (report_path / "definition" / "pages" / "pages.json").read_text(encoding="utf-8-sig")
    )
    page_order = pages_meta.get("pageOrder", [])
    pages_dir = report_path / "definition" / "pages"
    page_map = {}
    for page_dir in pages_dir.iterdir():
        if page_dir.is_dir() and (page_dir / "page.json").exists():
            parsed = _parse_page_pbir(page_dir)
            page_map[parsed["id"]] = parsed
    pages = [page_map[pid] for pid in page_order if pid in page_map]
    for pid, page in page_map.items():
        if pid not in page_order:
            pages.append(page)
    return {"format": "PBIR", "pages": pages}


def _parse_legacy(report_path: Path) -> dict:
    data = json.loads((report_path / "report.json").read_text(encoding="utf-8-sig"))
    pages = []
    for section in data.get("sections", []):
        visuals = []
        for vc in section.get("visualContainers", []):
            config = json.loads(vc.get("config", "{}"))
            v = config.get("singleVisual", {})
            visuals.append({
                "id": vc.get("name", ""),
                "visualType": v.get("visualType", ""),
                "title": "",
                "position": {"x": vc.get("x", 0), "y": vc.get("y", 0),
                              "width": vc.get("width", 0), "height": vc.get("height", 0)},
                "fields": [],
                "isHidden": vc.get("hidden", False),
            })
        pages.append({
            "id": section.get("name", ""),
            "displayName": section.get("displayName", section.get("name", "")),
            "width": section.get("width", 1280),
            "height": section.get("height", 720),
            "visuals": visuals,
        })
    return {"format": "PBIR-Legacy", "pages": pages}


def parse_report(report_path: Path) -> dict:
    report_path = Path(report_path)
    if (report_path / "definition").is_dir():
        return _parse_pbir(report_path)
    if (report_path / "report.json").exists():
        return _parse_legacy(report_path)
    raise ValueError(f"Unrecognised report format at: {report_path}")

import json
from pathlib import Path


def parse_bookmarks(report_path: Path) -> list:
    report_path = Path(report_path)
    bookmarks_dir = report_path / "definition" / "bookmarks"
    if not bookmarks_dir.is_dir():
        return []

    meta_file = bookmarks_dir / "bookmarks.json"
    if not meta_file.exists():
        return []

    meta = json.loads(meta_file.read_text(encoding="utf-8-sig"))
    bookmarks = []
    for item in meta.get("bookmarks", []):
        bm_id = item.get("name", "")
        bm_file = bookmarks_dir / f"{bm_id}.bookmark.json"
        display_name = item.get("displayName", bm_id)
        target_page = ""
        if bm_file.exists():
            bm_data = json.loads(bm_file.read_text(encoding="utf-8-sig"))
            target_page = bm_data.get("explorationState", {}).get("activeSection", "")
        bookmarks.append({"id": bm_id, "displayName": display_name, "targetPage": target_page})
    return bookmarks

from pathlib import Path
from pbip_loader import load_pbip
from bookmark_parser import parse_bookmarks

HR = Path("C:/Users/Admin/Documents/Life/projects/pbi-dashboard-factory/output/HR_Dashboard")
PBIP = HR / "HR_Dashboard.pbip"


def test_parse_bookmarks_returns_list():
    paths = load_pbip(PBIP)
    result = parse_bookmarks(paths["report_path"])
    assert isinstance(result, list)


def test_parse_bookmarks_no_error_when_missing():
    result = parse_bookmarks(Path("C:/nonexistent/path"))
    assert result == []

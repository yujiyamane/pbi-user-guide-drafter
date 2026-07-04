import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "scripts"
PBIP = Path("C:/Users/Admin/Documents/Life/projects/pbi-dashboard-factory/output/HR_Dashboard/HR_Dashboard.pbip")


def _get_data():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "parse_pbip.py"), str(PBIP)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    return json.loads(result.stdout)


def test_output_has_sources_field():
    data = _get_data()
    assert "sources" in data
    assert isinstance(data["sources"], list)


def test_sources_has_table_names():
    data = _get_data()
    assert len(data["sources"]) > 0
    assert all("table" in s for s in data["sources"])
    assert all(isinstance(s["table"], str) and s["table"] for s in data["sources"])


def test_sources_has_query_snippets():
    data = _get_data()
    m_sources = [s for s in data["sources"] if s.get("type") == "m"]
    assert len(m_sources) > 0
    assert all(isinstance(s["query_snippet"], str) and s["query_snippet"] for s in m_sources)


def test_output_has_acronyms_field():
    data = _get_data()
    assert "acronyms" in data
    assert isinstance(data["acronyms"], list)


def test_acronyms_structure():
    data = _get_data()
    assert len(data["acronyms"]) > 0
    for item in data["acronyms"]:
        assert "acronym" in item
        assert "found_in" in item


def test_acronyms_extracts_uppercase_tokens():
    data = _get_data()
    acronym_set = {item["acronym"] for item in data["acronyms"]}
    known = {"DAX", "CNT", "FY"}
    assert len(known & acronym_set) > 0, f"Expected at least one of {known} in {acronym_set}"


def test_output_has_kpi_visuals_field():
    data = _get_data()
    assert "kpi_visuals" in data
    assert isinstance(data["kpi_visuals"], dict)


def test_kpi_visuals_keyed_by_page_name():
    data = _get_data()
    page_names = {p["displayName"] for p in data["report"]["pages"]}
    kpi_keys = set(data["kpi_visuals"].keys())
    assert kpi_keys == page_names, f"kpi_visuals keys {kpi_keys} != page names {page_names}"

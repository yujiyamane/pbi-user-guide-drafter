from pathlib import Path
from pbip_loader import load_pbip
from model_parser import parse_model

HR = Path("C:/Users/Admin/Documents/Life/projects/pbi-dashboard-factory/output/HR_Dashboard")
PBIP = HR / "HR_Dashboard.pbip"


def test_parse_model_returns_tmdl_format():
    paths = load_pbip(PBIP)
    result = parse_model(paths["model_path"])
    assert result["format"] == "TMDL"


def test_parse_model_returns_tables():
    paths = load_pbip(PBIP)
    result = parse_model(paths["model_path"])
    assert len(result["tables"]) > 0


def test_parse_model_table_names():
    paths = load_pbip(PBIP)
    result = parse_model(paths["model_path"])
    names = [t["name"] for t in result["tables"]]
    assert "Fact" in names
    assert "Date" in names


def test_parse_model_tables_have_columns_and_measures():
    paths = load_pbip(PBIP)
    result = parse_model(paths["model_path"])
    for t in result["tables"]:
        assert "columns" in t
        assert "measures" in t
        assert isinstance(t["columns"], list)
        assert isinstance(t["measures"], list)


def test_parse_model_fact_has_measures():
    paths = load_pbip(PBIP)
    result = parse_model(paths["model_path"])
    fact = next(t for t in result["tables"] if t["name"] == "Fact")
    assert len(fact["measures"]) > 0


def test_parse_model_measures_have_expression():
    paths = load_pbip(PBIP)
    result = parse_model(paths["model_path"])
    for t in result["tables"]:
        for m in t["measures"]:
            assert "name" in m
            assert "expression" in m


def test_parse_model_returns_relationships():
    paths = load_pbip(PBIP)
    result = parse_model(paths["model_path"])
    assert "relationships" in result
    assert isinstance(result["relationships"], list)

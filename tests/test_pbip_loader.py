import pytest
from pathlib import Path
from pbip_loader import load_pbip

HR = Path("C:/Users/Admin/Documents/Life/projects/pbi-dashboard-factory/output/HR_Dashboard")
PBIP = HR / "HR_Dashboard.pbip"


def test_load_pbip_returns_name():
    result = load_pbip(PBIP)
    assert result["name"] == "HR_Dashboard"


def test_load_pbip_returns_report_path():
    result = load_pbip(PBIP)
    assert result["report_path"] == HR / "HR_Dashboard.Report"


def test_load_pbip_returns_model_path():
    result = load_pbip(PBIP)
    assert result["model_path"] == HR / "HR_Dashboard.SemanticModel"


def test_load_pbip_report_folder_exists():
    result = load_pbip(PBIP)
    assert result["report_path"].is_dir()


def test_load_pbip_model_folder_exists():
    result = load_pbip(PBIP)
    assert result["model_path"].is_dir()


def test_load_pbip_raises_on_invalid_path():
    with pytest.raises(FileNotFoundError):
        load_pbip(Path("nonexistent.pbip"))

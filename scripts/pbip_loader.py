import json
from pathlib import Path


def load_pbip(pbip_path: Path) -> dict:
    pbip_path = Path(pbip_path)
    if not pbip_path.exists():
        raise FileNotFoundError(f"PBIP file not found: {pbip_path}")

    data = json.loads(pbip_path.read_text(encoding="utf-8-sig"))
    report_rel = data["artifacts"][0]["report"]["path"]
    report_path = (pbip_path.parent / report_rel).resolve()

    pbir = json.loads((report_path / "definition.pbir").read_text(encoding="utf-8-sig"))
    model_rel = pbir["datasetReference"]["byPath"]["path"]
    model_path = (report_path / model_rel).resolve()

    if not report_path.is_dir():
        raise FileNotFoundError(f"Report folder not found: {report_path}")
    if not model_path.is_dir():
        raise FileNotFoundError(f"Semantic model folder not found: {model_path}")

    return {"report_path": report_path, "model_path": model_path, "name": pbip_path.stem}

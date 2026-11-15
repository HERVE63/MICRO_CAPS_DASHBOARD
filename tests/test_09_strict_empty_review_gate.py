"""Test the strict 09 validator's fail-closed behavior with an empty review."""
import csv
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "SCRIPTS_ACTIFS" / "09_CONTROLE_REVUE_MCPA_IPS.py"

def test_09_rejects_empty_review(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("strict09_empty_review", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    review = tmp_path / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv"
    with review.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerow(module.COLONNES)
    monkeypatch.setattr(module, "ENTREE", review)
    monkeypatch.setattr(module, "SORTIE", tmp_path / "controle.csv")
    with pytest.raises(RuntimeError, match="Revue MCPA/IPS vide"):
        module.executer()
    assert not (tmp_path / "controle.csv").exists()

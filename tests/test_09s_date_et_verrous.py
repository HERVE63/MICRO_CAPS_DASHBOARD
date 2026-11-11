import importlib.util
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("adaptateur_09s", ROOT / "SCRIPTS_ACTIFS/09S_ADAPTATEUR_FICHES_MCPA_40.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_date_revue_actuelle_et_verrou_wwws():
    p = ROOT / "DOSSIERS_MCPA_IPS_40/01_IDN.json"
    dossier = json.loads(p.read_text(encoding="utf-8"))
    dossier["date_revue"] = date.today().isoformat()
    issues = module.validation_individuelle(dossier)
    assert not any(x.startswith("DATE_REVUE_INVALIDE") or x == "REVUE_FUTURE" for x in issues)
    assert "COMPLEMENT_MANQUANT:wwws" in issues

def test_date_source_future_bloquee():
    p = ROOT / "DOSSIERS_MCPA_IPS_40/01_IDN.json"
    dossier = json.loads(p.read_text(encoding="utf-8"))
    dossier["date_revue"] = "2026-11-10"
    cell = dossier["blocs"]["qualite"]
    key = next(k for k, v in cell.items() if v.get("valeur") is not None)
    cell[key]["date_source"] = "2026-11-11"
    issues = module.validation_individuelle(dossier)
    assert "SOURCE_POSTERIEURE_A_REVUE:qualite." + key in issues

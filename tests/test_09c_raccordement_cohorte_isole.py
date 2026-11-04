# -*- coding: utf-8 -*-
"""Tests reproductibles du raccordement 09C, sans accès réseau ni écriture historique."""
import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "SCRIPTS_ACTIFS" / "09C_AUDIT_RACCORDEMENT_TITULAIRES.py"


def _charger(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("audit_09c_isole", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "D", tmp_path)
    for name in ("ETAT_INITIAL_PORTEFEUILLE_GERE.csv", "COHORTE_MICRO_CAPS_T0.csv"):
        (tmp_path / name).write_bytes((ROOT / "DONNEES" / name).read_bytes())
    return module


def test_absence_de_preselection_ne_signifie_pas_absence_historique(tmp_path, monkeypatch):
    module = _charger(tmp_path, monkeypatch)
    (tmp_path / "CANDIDATS_PRETS_SSI.csv").write_text("Ticker\n", encoding="utf-8")
    result = module.executer()
    assert len(result) == 40
    assert result["Present_dans_cohorte_T0"].all()
    assert not result["Present_dans_chasse"].any()
    assert set(result["Statut_raccordement"]) == {"ABSENT_PRESELECTION_SSI"}
    assert set(result["Statut_donnees"]) == {"EN_ATTENTE_DATA"}
    assert not result["Identite_emetteur_certifiee"].any()
    assert (tmp_path / "AUDIT_RACCORDEMENT_40_TITULAIRES.csv").exists()


def test_ecart_t0_ne_produit_aucune_certification(tmp_path, monkeypatch):
    module = _charger(tmp_path, monkeypatch)
    p = tmp_path / "ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
    portefeuille = pd.read_csv(p, keep_default_na=False)
    original = portefeuille.loc[0, "Ticker"]
    portefeuille.loc[0, "Ticker"] = "TEST_TICKER_INCONNU"
    portefeuille.to_csv(p, index=False)
    (tmp_path / "CANDIDATS_PRETS_SSI.csv").write_text(
        "Ticker\nTEST_TICKER_INCONNU\n", encoding="utf-8"
    )
    result = module.executer()
    ligne = result.loc[result["Ticker"] == "TEST_TICKER_INCONNU"].iloc[0]
    assert ligne["Present_dans_chasse"]
    assert not ligne["Present_dans_cohorte_T0"]
    assert ligne["Statut_raccordement"] == "ECART_COHORTE_T0_A_VERIFIER"
    assert ligne["Statut_donnees"] == "EN_ATTENTE_DATA"
    assert not ligne["Identite_emetteur_certifiee"]
    assert original != "TEST_TICKER_INCONNU"

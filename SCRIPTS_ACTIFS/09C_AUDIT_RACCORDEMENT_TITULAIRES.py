# -*- coding: utf-8 -*-
"""Audit du raccordement des titulaires aux dossiers de chasse, sans notation."""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
D = BASE / "DONNEES"

def executer():
    p = pd.read_csv(D / "ETAT_INITIAL_PORTEFEUILLE_GERE.csv", dtype={"Ticker": str})
    c = pd.read_csv(D / "CANDIDATS_PRETS_SSI.csv", dtype={"Ticker": str})
    t0 = pd.read_csv(D / "COHORTE_MICRO_CAPS_T0.csv", dtype={"Ticker_cotation": str}, keep_default_na=False)
    assert len(p) == 40 and p["Ticker"].nunique() == 40
    assert c["Ticker"].notna().all()
    assert len(t0) == 40 and t0["Ticker_cotation"].nunique() == 40
    result = p[["ID_position", "Societe", "Ticker", "Devise"]].copy()
    result["Present_dans_chasse"] = result["Ticker"].isin(set(c["Ticker"]))
    # La cohorte T0 est une référence historique, pas une preuve de données actuelles.
    # Comparer les tickers de cotation (avec place), sans fusion approximative.
    result["Present_dans_cohorte_T0"] = result["Ticker"].isin(set(t0["Ticker_cotation"]))
    result["Source_cohorte_T0"] = "COHORTE_MICRO_CAPS_T0.csv"
    result["Identite_emetteur_certifiee"] = False
    result["Statut_donnees"] = "EN_ATTENTE_DATA"
    result["Source_titulaires"] = "ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
    result["Source_chasse"] = "CANDIDATS_PRETS_SSI.csv"
    result["Statut_raccordement"] = result["Present_dans_chasse"].map(
        {True: "PRESENT_EN_PRESELECTION_SSI_IDENTITE_A_VERIFIER", False: "ABSENT_PRESELECTION_SSI"}
    )
    # Ne jamais interpréter ABSENT_PRESELECTION_SSI comme données historiques absentes.
    result.loc[~result["Present_dans_cohorte_T0"], "Statut_raccordement"] = "ECART_COHORTE_T0_A_VERIFIER"
    out = D / "AUDIT_RACCORDEMENT_40_TITULAIRES.csv"
    result.to_csv(out, index=False)
    print(f"Titulaires={len(result)}, présents dans présélection SSI={int(result.Present_dans_chasse.sum())}, présents T0={int(result.Present_dans_cohorte_T0.sum())}")
    print(f"Audit: {out}")
    return result

if __name__ == "__main__":
    executer()

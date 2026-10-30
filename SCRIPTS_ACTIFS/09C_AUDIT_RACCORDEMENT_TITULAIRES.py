# -*- coding: utf-8 -*-
"""Audit du raccordement des titulaires aux dossiers de chasse, sans notation."""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
D = BASE / "DONNEES"

def executer():
    p = pd.read_csv(D / "ETAT_INITIAL_PORTEFEUILLE_GERE.csv", dtype={"Ticker": str})
    c = pd.read_csv(D / "CANDIDATS_PRETS_SSI.csv", dtype={"Ticker": str})
    assert len(p) == 40 and p["Ticker"].nunique() == 40
    assert c["Ticker"].notna().all()
    result = p[["ID_position", "Societe", "Ticker", "Devise"]].copy()
    result["Present_dans_chasse"] = result["Ticker"].isin(set(c["Ticker"]))
    result["Source_titulaires"] = "ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
    result["Source_chasse"] = "CANDIDATS_PRETS_SSI.csv"
    result["Statut_raccordement"] = result["Present_dans_chasse"].map(
        {True: "MATCH_TICKER_A_VERIFIER", False: "SOURCE_TITULAIRE_A_LOCALISER"}
    )
    out = D / "AUDIT_RACCORDEMENT_40_TITULAIRES.csv"
    result.to_csv(out, index=False)
    print(f"Titulaires={len(result)}, correspondances exactes={int(result.Present_dans_chasse.sum())}")
    print(f"Audit: {out}")
    return result

if __name__ == "__main__":
    executer()

# -*- coding: utf-8 -*-
"""
MICRO CAPS — 05D PRIX DES POSITIONS NOUVELLES

Rôle strict :
- valoriser uniquement les positions actives NEW_ issues du journal/replay 05C ;
- réutiliser exactement les moteurs de clôture 03A et FX 03B ;
- ne jamais modifier T0, le témoin, le journal ou l'état initial ;
- fail-closed à la moindre donnée manquante/incohérente.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import importlib.util
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "SCRIPTS_ACTIFS"
OUTPUT = BASE / "DONNEES/TEST_PRIX_POSITIONS_NOUVELLES_V3.csv"

def charger_module(nom, chemin):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

clotures = charger_module("mc_clotures_new", SRC / "03A_MOTEUR_CLOTURES_V3.py")
fxmod = charger_module("mc_fx_new", SRC / "03B_MOTEUR_FX_V3.py")

def executer(positions):
    if not isinstance(positions, pd.DataFrame):
        raise RuntimeError("05D exige le DataFrame positions produit par 05C.")

    actifs = positions[
        positions["Statut"].astype(str).str.upper().eq("ACTIF")
        & positions["ID_position"].astype(str).str.startswith("NEW_")
    ].copy()

    colonnes = [
        "ID_position","Societe","Ticker","Devise","Date_cloture",
        "Cours_retenu_devise","FX_vers_EUR","Cours_EUR_resolu",
        "Resolution_anomalie"
    ]

    if len(actifs) == 0:
        vide = pd.DataFrame(columns=colonnes)
        vide.to_csv(OUTPUT, index=False)
        return vide

    if actifs["ID_position"].duplicated().any():
        raise RuntimeError("05D : ID_position NEW_ dupliqué.")

    maintenant = datetime.now(ZoneInfo("UTC"))
    fx = fxmod.tous_les_fx(maintenant)
    lignes = []

    for _, r in actifs.iterrows():
        ticker = str(r["Ticker"]).strip()
        devise = str(r["Devise"]).strip().upper()
        if not ticker or ticker.lower() == "nan":
            raise RuntimeError(f"05D : ticker manquant pour {r['ID_position']}.")
        if not devise or devise.lower() == "nan":
            raise RuntimeError(f"05D : devise manquante pour {r['ID_position']}.")

        px = clotures.derniere_cloture_validee(ticker, maintenant)
        if devise not in fx:
            raise RuntimeError(f"05D : FX indisponible pour {devise}.")

        taux = float(fx[devise]["fx_vers_eur"])
        cours = float(px["cours_cloture"])
        if cours <= 0 or taux <= 0:
            raise RuntimeError(f"05D : cours/FX non positif pour {r['ID_position']}.")

        lignes.append({
            "ID_position": str(r["ID_position"]),
            "Societe": r["Societe"],
            "Ticker": ticker,
            "Devise": devise,
            "Date_cloture": str(px["date_session"]),
            "Cours_retenu_devise": cours,
            "FX_vers_EUR": taux,
            "Cours_EUR_resolu": cours * taux,
            "Resolution_anomalie": "AUCUNE"
        })

    df = pd.DataFrame(lignes, columns=colonnes)
    if len(df) != len(actifs) or df["ID_position"].nunique() != len(actifs):
        raise RuntimeError("05D : valorisation NEW_ incomplète/non unique.")

    tmp = OUTPUT.with_suffix(".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(OUTPUT)
    return df

if __name__ == "__main__":
    raise RuntimeError("05D doit être appelé par 05 avec les positions reconstruites par 05C.")

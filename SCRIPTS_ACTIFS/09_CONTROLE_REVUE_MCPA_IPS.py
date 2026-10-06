# -*- coding: utf-8 -*-
"""
MICRO CAPS — 09 COMITE HEBDOMADAIRE MCPA/IPS

Ce module ne note rien par déduction et n'exécute aucun arbitrage.
Il contrôle qu'une revue du mardi respecte le référentiel maître :
SSI d'admissibilité, MCPA Q/V/G/R/M/D, IC, CX, Delta, WWWS,
IPS, duel challenger/titulaire et décision documentée.

Toute donnée obligatoire manquante => revue NON VALIDEE (fail-closed).
Le journal d'arbitrages n'est jamais modifié ici.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
ENTREE = BASE / "DONNEES/REVUE_HEBDOMADAIRE_MCPA_IPS.csv"
SORTIE = BASE / "DONNEES/CONTROLE_REVUE_HEBDOMADAIRE_MCPA_IPS.csv"

COLONNES = [
    "Date_revue","Type","ID_position","Societe","Ticker","Devise",
    "SSI","Q","V","G","R","M","D","MCPA","IC","CX","Delta","WWWS",
    "Catalyseurs","Risques","Scenario_bear","Prob_bear",
    "Scenario_central","Prob_central","Scenario_bull","Prob_bull",
    "Role_IPS","Challengers_compares","Decision",
    "Condition_renforcement","Condition_allegement_sortie",
    "Sources","Date_sources","Statut_analyse"
]

DECISIONS = {
    "RENFORCER","CONSERVER","ALLEGER","ALLÉGER","VENDRE",
    "SONDE","INCUBATION","ATTENTE","SURVEILLER"
}

def executer():
    if not ENTREE.exists():
        raise RuntimeError(
            "Revue MCPA/IPS absente : aucune décision automatique autorisée."
        )
    df = pd.read_csv(ENTREE)
    absentes = [c for c in COLONNES if c not in df.columns]
    if absentes:
        raise RuntimeError("Colonnes revue absentes : " + ", ".join(absentes))
    if len(df) == 0:
        raise RuntimeError("Revue MCPA/IPS vide.")

    erreurs = []
    for i, r in df.iterrows():
        ref = str(r.get("Societe", f"ligne {i+1}"))
        for c in COLONNES:
            v = r[c]
            if pd.isna(v) or str(v).strip() == "":
                erreurs.append(f"{ref}: {c} manquant")
        try:
            q,v,g,ris,m,d = [float(r[x]) for x in ["Q","V","G","R","M","D"]]
            mcpa = float(r["MCPA"])
            if not (0<=q<=30 and 0<=v<=20 and 0<=g<=20 and 0<=ris<=10 and 0<=m<=10 and 0<=d<=10):
                erreurs.append(f"{ref}: sous-score MCPA hors bornes")
            if abs((q+v+g+ris+m+d)-mcpa) > 0.01:
                erreurs.append(f"{ref}: MCPA != somme Q/V/G/R/M/D")
            if not 0 <= float(r["IC"]) <= 5: erreurs.append(f"{ref}: IC hors bornes")
            if not 0 <= float(r["CX"]) <= 5: erreurs.append(f"{ref}: CX hors bornes")
            if not 0 <= float(r["SSI"]) <= 100: erreurs.append(f"{ref}: SSI hors bornes")
            if not 0 <= float(r["WWWS"]) <= 100: erreurs.append(f"{ref}: WWWS hors bornes")
            probs=sum(float(r[x]) for x in ["Prob_bear","Prob_central","Prob_bull"])
            if abs(probs-100.0) > 0.1:
                erreurs.append(f"{ref}: probabilités scénarios != 100")
        except Exception:
            erreurs.append(f"{ref}: valeur numérique invalide")

        if str(r["Decision"]).strip().upper() not in DECISIONS:
            erreurs.append(f"{ref}: décision non autorisée")
        if str(r["Type"]).strip().upper() not in {"TITULAIRE","CHALLENGER"}:
            erreurs.append(f"{ref}: Type doit être TITULAIRE ou CHALLENGER")

    controle = pd.DataFrame([{
        "Horodatage_UTC": datetime.now(ZoneInfo("UTC")).isoformat(),
        "Nb_lignes": len(df),
        "Statut": "OK" if not erreurs else "BLOQUE",
        "Nb_erreurs": len(erreurs),
        "Erreurs": " | ".join(erreurs)
    }])
    controle.to_csv(SORTIE, index=False)
    if erreurs:
        raise RuntimeError("Revue MCPA/IPS bloquée : " + " | ".join(erreurs[:20]))
    print(f"Revue MCPA/IPS contrôlée : {len(df)} lignes — OK")
    print("Aucun arbitrage exécuté automatiquement.")
    return df

if __name__ == "__main__":
    executer()

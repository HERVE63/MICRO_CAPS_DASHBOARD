# -*- coding: utf-8 -*-
"""Audit de complétude MICRO CAPS, strictement en lecture seule.

Ne valide jamais une expérience sur la seule réussite d'un workflow.
Les historiques officiels, CPI, ETF et coffres maîtres ne sont pas touchés.
"""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import sys

BASE = Path(__file__).resolve().parents[1]
D = BASE / "DONNEES"
ERREURS = []
ETAPES = {}

def lire_csv(p):
    if not p.is_file() or p.stat().st_size == 0:
        raise RuntimeError("SOURCE_ABSENTE_OU_VIDE:" + str(p.relative_to(BASE)))
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def controler(nom, fonction):
    try:
        valeur = fonction()
        ETAPES[nom] = {"statut": "OK", **valeur}
    except Exception as exc:
        msg = str(exc)
        ETAPES[nom] = {"statut": "BLOQUE", "motif": msg}
        ERREURS.append(nom + ": " + msg)

def chasse():
    lignes = lire_csv(D / "CHASSE_CANDIDATS.csv")
    colonnes = {"Ticker", "Date_detection", "Source_detection"}
    if not colonnes.issubset(lignes[0]):
        raise RuntimeError("SCHEMA_CHASSE_INCOMPLET")
    if any(not x["Ticker"].strip() or not x["Date_detection"].strip() for x in lignes):
        raise RuntimeError("IDENTITES_CHASSE_MANQUANTES")
    couples = [(x["Ticker"], x["Date_detection"]) for x in lignes]
    if len(set(couples)) != len(couples):
        raise RuntimeError("DOUBLONS_CHASSE")
    return {"detections": len(lignes), "tickers_distincts": len({x["Ticker"] for x in lignes})}

def qualification():
    # Controle les resultats courants produits par 07R, et non une archive
    # historique SEC susceptible de provenir d'une autre cohorte.
    dossiers = lire_csv(D / "DOSSIERS_SSI_A_QUALIFIER.csv")
    resultats = lire_csv(D / "RESULTATS_SSI.csv")
    if not dossiers and not resultats:
        return {"dossiers_prepares":0,"resultats_courants":0,"dossiers_qualifies":0,"admis_SSI":0,"en_attente":0,"etat":"AUCUN_NOUVEAU_CANDIDAT"}
    if not {"Ticker", "Statut_SSI"}.issubset(resultats[0]):
        raise RuntimeError("SCHEMA_SSI_COURANT_INCOMPLET")
    td = [r.get("Ticker", "").strip() for r in dossiers]
    tr = [r.get("Ticker", "").strip() for r in resultats]
    if len(td) != len(set(td)) or len(tr) != len(set(tr)):
        raise RuntimeError("DOUBLONS_SSI_COURANT")
    if set(td) != set(tr):
        raise RuntimeError("SSI_COURANT_NON_ALIGNE_DOSSIERS")
    admis = [r for r in resultats if r["Statut_SSI"] == "ADMIS_SSI"]
    qualifies = [r for r in resultats if r["Statut_SSI"] in ("ADMIS_SSI", "REFUSE_SSI")]
    info = {"dossiers_prepares": len(dossiers), "resultats_courants": len(resultats),
            "dossiers_qualifies": len(qualifies), "admis_SSI": len(admis),
            "en_attente": len(resultats) - len(qualifies)}
    # Une absence de preuves ne vaut jamais qualification.
    if not qualifies:
        info["etat"]="QUALIFICATION_EN_ATTENTE"
    return info

def revue():
    rows = lire_csv(D / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv")
    candidats = [r for r in rows if r.get("Type", "").upper() == "CHALLENGER"]
    titulaires = [r for r in rows if r.get("Type", "").upper() == "TITULAIRE"]
    if len(titulaires) != 40:
        raise RuntimeError("REVUE_TITULAIRES_INCOMPLETE:" + str(len(titulaires)))
    if not candidats:
        return {"titulaires":len(titulaires),"challengers":0,"etat":"AUCUN_CHALLENGER_QUALIFIE"}
    for r in candidats:
        if float(r["SSI"]) < 65 or float(r["MCPA"]) < 80:
            raise RuntimeError("CHALLENGER_SOUS_SEUIL:" + r["Ticker"])
        if r.get("Statut_analyse", "").upper() not in ("VALIDE", "VALIDEE"):
            raise RuntimeError("CHALLENGER_NON_VALIDE:" + r["Ticker"])
    return {"titulaires": len(titulaires), "challengers": len(candidats)}

def portefeuilles():
    lignes = lire_csv(D / "TEST_PORTEFEUILLES_V3.csv")
    qualite = lire_csv(D / "TEST_CONTROLE_QUALITE_V3.csv")
    benchmarks = lire_csv(D / "TEST_BENCHMARKS_V3.csv")
    if len(lignes) != 40 or len(qualite) != 40:
        raise RuntimeError("COHORTE_40_INCOMPLETE")
    if len({x["ID_ligne"] for x in lignes}) != 40:
        raise RuntimeError("IDENTIFIANTS_COHORTE_DUPLIQUES")
    if any(x["Statut_qualite"] != "OK" for x in qualite):
        raise RuntimeError("ANOMALIES_QUALITE_NON_RESOLUES")
    if len(benchmarks) != 3 or any(x["Statut"] != "OK" for x in benchmarks):
        raise RuntimeError("BENCHMARKS_INCOMPLETS")
    r = lignes[0]
    v_gere = float(r["Total_Gere_EUR"])
    v_temoin = float(r["Total_Temoin_EUR"])
    if abs(sum(float(x["Valeur_Gere_EUR"]) for x in lignes) + float(r["Cash_Gere_EUR"]) - v_gere) > .02:
        raise RuntimeError("VALORISATION_GERE_DIVERGENTE")
    if abs(sum(float(x["Valeur_Temoin_EUR"]) for x in lignes) - v_temoin) > .02:
        raise RuntimeError("VALORISATION_TEMOIN_DIVERGENTE")
    return {"lignes": 40, "benchmarks": 3, "date_cloture": r["Date_cloture"],
            "gere_EUR": round(v_gere, 2), "temoin_EUR": round(v_temoin, 2)}

def affichage():
    p = BASE / "index.html"
    if not p.exists():
        raise RuntimeError("DASHBOARD_ABSENT")
    s = p.read_text(encoding="utf-8")
    if 'name="viewport"' not in s or "40 VALEURS" not in s:
        raise RuntimeError("DASHBOARD_MOBILE_INCOMPLET")
    revue = lire_csv(D / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv")
    challengers = [r for r in revue if r.get("Type", "").upper() == "CHALLENGER"]
    if not challengers:
        raise RuntimeError("AUCUN_CHALLENGER_A_AFFICHER")
    if any(r["Ticker"] not in s for r in challengers[:20]):
        raise RuntimeError("CHALLENGER_NON_AFFICHE")
    return {"challengers_visibles": min(len(challengers), 20), "mobile_viewport": True}

def arbitrages():
    journal = lire_csv(D / "JOURNAL_ARBITRAGES_GERE.csv")
    for p in ("09B_DUEL_PROCHAIN_EURO.py", "10_EXECUTION_MENSUELLE.py", "05C_REPLAY_PORTEFEUILLE_GERE.py"):
        if not (BASE / "SCRIPTS_ACTIFS" / p).is_file():
            raise RuntimeError("MODULE_ARBITRAGE_ABSENT:" + p)
    if not journal:
        raise RuntimeError("ARBITRAGE_MENSUEL_NON_DEMONTRE_JOURNAL_VIDE")
    return {"operations": len(journal)}

def verifier():
    controler("chasse", chasse)
    controler("qualification_SSI", qualification)
    controler("revue_MCPA_IPS", revue)
    controler("portefeuilles_et_benchmarks", portefeuilles)
    controler("affichage_mobile_challengers", affichage)
    controler("arbitrages", arbitrages)
    bilan = {"date_UTC": datetime.now(timezone.utc).isoformat(),
             "sauvegarde_autorisee": not ERREURS,
             "etapes": ETAPES, "blocages": ERREURS,
             "perimetre": "lecture seule; CPI/ETF AV/historiques/coffres inchanges"}
    print(json.dumps(bilan, ensure_ascii=False, indent=2))
    return bilan

if __name__ == "__main__":
    bilan = verifier()
    sys.exit(0 if bilan["sauvegarde_autorisee"] else 1)

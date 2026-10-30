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
    p = D / "DOSSIERS_SSI_A_QUALIFIER.csv"
    dossiers = lire_csv(p)
    manifeste = sorted((BASE / "AUDITS/SCE_DISCOVERY_US").glob("*/MANIFESTE.json"))
    if not manifeste:
        raise RuntimeError("AUCUN_RESULTAT_SSI_ARCHIVE")
    mpath = manifeste[-1]
    m = json.loads(mpath.read_text(encoding="utf-8"))
    rpath = mpath.parent / "RESULTATS_SSI.csv"
    empreinte = hashlib.sha256(rpath.read_bytes()).hexdigest()
    if m.get("fichiers", {}).get("RESULTATS_SSI.csv") != empreinte:
        raise RuntimeError("RESULTATS_SSI_ARCHIVE_ALTERES")
    resultats = lire_csv(rpath)
    if len(resultats) != int(m["cotations_conservees"]):
        raise RuntimeError("COUVERTURE_SSI_DIVERGENTE")
    admis = [x for x in resultats if x.get("Statut_SSI") == "ADMIS_SSI"]
    complets = sum(x.get("Statut_SSI") in ("ADMIS_SSI", "REFUSE_SSI") for x in resultats)
    couverture = complets / len(resultats)
    info = {"dossiers_prepares": len(dossiers), "univers_SSI_US": len(resultats),
            "dossiers_complets": complets, "admis_SSI": len(admis),
            "couverture_pct": round(100 * couverture, 3),
            "manifest_source": str(mpath.relative_to(BASE))}
    if couverture < .5:
        raise RuntimeError("COUVERTURE_SSI_INSUFFISANTE:" + json.dumps(info, ensure_ascii=False))
    return info

def revue():
    rows = lire_csv(D / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv")
    candidats = [r for r in rows if r.get("Type", "").upper() == "CHALLENGER"]
    titulaires = [r for r in rows if r.get("Type", "").upper() == "TITULAIRE"]
    if len(titulaires) != 40:
        raise RuntimeError("REVUE_TITULAIRES_INCOMPLETE:" + str(len(titulaires)))
    if not candidats:
        raise RuntimeError("AUCUN_CHALLENGER_MCPA_DOCUMENTE")
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

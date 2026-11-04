#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pilote SEC des cinq titulaires US : captures brutes auditees, sans notes.

Reutilise le protocole SEC de 07T/07U/07Z (contact explicite, CIK, XBRL,
provenance, SHA256). Les captures ne certifient ni SCE, ni SSI, ni MCPA.
Ne modifie jamais DONNEES, HISTORIQUE, main ou les portefeuilles.
"""
import csv
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
POSITIONS = ROOT / "DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
ARCHIVES = ROOT / "AUDITS/SEC_PILOTE_US_5"
MAPPING = "https://www.sec.gov/files/company_tickers.json"
TAGS = {
    "Revenues": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "NetIncomeLoss": ("NetIncomeLoss",),
    "Assets": ("Assets",),
    "Cash": ("CashAndCashEquivalentsAtCarryingValue",),
}


class RedirectionsSEC(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        verifier_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def verifier_url(url):
    p = urlparse(url)
    if (p.scheme != "https" or p.hostname not in {"www.sec.gov", "data.sec.gov"}
            or p.username or p.password or p.port not in (None, 443)):
        raise ValueError("URL_HORS_SEC")
    return url


def lire_json(url, agent):
    verifier_url(url)
    req = urllib.request.Request(url, headers={
        "User-Agent": agent, "Accept": "application/json",
        "Accept-Encoding": "identity",
    })
    opener = urllib.request.build_opener(RedirectionsSEC())
    with opener.open(req, timeout=30) as resp:
        verifier_url(resp.geturl())
        brut = resp.read(20_000_001)
    if not brut or len(brut) > 20_000_000:
        raise ValueError("REPONSE_SEC_TAILLE_INVALIDE")
    obj = json.loads(brut)
    if not isinstance(obj, dict):
        raise ValueError("REPONSE_SEC_JSON_INVALIDE")
    return obj, brut


def ecrire(path, contenu):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(contenu)
    tmp.replace(path)


def executer(base=ROOT, fetcher=lire_json, pause=time.sleep, maintenant=None):
    agent = os.getenv("SEC_USER_AGENT", "").strip()
    if "@" not in agent or len(agent) < 8:
        raise RuntimeError("SEC_USER_AGENT_CONTACT_EXPLICITE_REQUIS")
    base = Path(base)
    horodatage = maintenant or datetime.now(timezone.utc)
    if horodatage.tzinfo is None or horodatage.utcoffset() is None:
        raise ValueError("HORODATAGE_UTC_REQUIS")
    with (base / "DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv").open(
            encoding="utf-8-sig", newline="") as f:
        positions = [r for r in csv.DictReader(f)
                     if r["ID_position"] in {"1", "2", "3", "4", "5"}]
    if (len(positions) != 5 or len({r["ID_position"] for r in positions}) != 5
            or len({r["Ticker"] for r in positions}) != 5
            or any(r["Devise"] != "USD" for r in positions)):
        raise RuntimeError("COHORTE_US_5_INCOHERENTE")
    dossier = base / "AUDITS/SEC_PILOTE_US_5" / horodatage.strftime("%Y%m%dT%H%M%S%fZ")
    dossier.mkdir(parents=True, exist_ok=False)
    sources = []
    erreurs = []
    def collecter(url):
        verifier_url(url)
        obj, brut = fetcher(url, agent)
        if not isinstance(obj, dict) or not isinstance(brut, bytes):
            raise ValueError("REPONSE_SEC_NON_VERIFIABLE")
        if json.loads(brut) != obj:
            raise ValueError("REPONSE_SEC_BRUT_DIVERGENT")
        digest = hashlib.sha256(brut).hexdigest()
        rel = "BRUTS/" + digest + ".json"
        ecrire(dossier / rel, brut)
        sources.append({
            "URL": url, "Date_collecte_UTC": horodatage.isoformat(),
            "SHA256": digest, "Fichier_brut": rel,
            "Statut": "SOURCE_BRUTE_A_VERIFIER",
        })
        pause(0.35)
        return obj

    try:
        mapping = collecter(MAPPING)
        index = {}
        for item in mapping.values():
            ticker = str(item.get("ticker", "")).strip().upper()
            if ticker:
                index.setdefault(ticker, []).append(item)
    except Exception as exc:
        index = {}
        erreurs.append("REGISTRE_SEC_" + type(exc).__name__)

    lignes = []
    for p in positions:
        ticker = p["Ticker"].strip().upper()
        row = {
            "ID_position": p["ID_position"], "Societe": p["Societe"],
            "Ticker": ticker, "CIK": "", "Nom_SEC": "",
            "Statut": "EN_ATTENTE_DATA_REGISTRE_SEC" if erreurs else "EN_ATTENTE_DATA_IDENTITE",
            "Concepts_XBRL": 0, "Revenues": 0, "NetIncomeLoss": 0,
            "Assets": 0, "Cash": 0, "Derniere_publication": "",
            "Disponibilite_publication_T0": "INCONNUE",
            "Score_SSI": "MANQUANTE", "Score_MCPA": "MANQUANTE",
            "Preuve_SCE_certifiee": "NON",
        }
        candidats = index.get(ticker, [])
        if len(candidats) == 1:
            item = candidats[0]
            cik = str(item.get("cik_str", "")).zfill(10)
            if len(cik) != 10 or not cik.isdigit():
                row["Statut"] = "EN_ATTENTE_DATA_CIK_INVALIDE"
            else:
                row["CIK"] = cik
                row["Nom_SEC"] = str(item.get("title", ""))
                try:
                    sub = collecter("https://data.sec.gov/submissions/CIK" + cik + ".json")
                    if (str(sub.get("cik", "")).zfill(10) != cik
                            or ticker not in [str(t).upper() for t in sub.get("tickers", [])]):
                        row["Statut"] = "EN_ATTENTE_DATA_IDENTITE_SEC_DIVERGENTE"
                    else:
                        rec = sub.get("filings", {}).get("recent", {})
                        dates = [d for d, form in zip(rec.get("filingDate", []),
                                                      rec.get("form", []))
                                 if form in ("10-K", "10-Q") and isinstance(d, str)
                                 and d <= horodatage.date().isoformat()]
                        if dates:
                            row["Derniere_publication"] = max(dates)
                            row["Disponibilite_publication_T0"] = (
                                "DISPONIBLE_AVANT_T0" if max(dates) < p["Date_entree"]
                                else "POSTERIEUR_OU_JOUR_T0")
                        facts = collecter(
                            "https://data.sec.gov/api/xbrl/companyfacts/CIK" + cik + ".json")
                        if str(facts.get("cik", "")).zfill(10) != cik:
                            row["Statut"] = "EN_ATTENTE_DATA_CIK_FACTS_DIVERGENT"
                        else:
                            gaap = facts.get("facts", {}).get("us-gaap", {})
                            if not isinstance(gaap, dict):
                                raise ValueError("XBRL_SCHEMA_INVALIDE")
                            row["Concepts_XBRL"] = len(gaap)
                            for nom, tags in TAGS.items():
                                row[nom] = int(any(tag in gaap and gaap[tag].get("units")
                                                   for tag in tags))
                            row["Statut"] = ("XBRL_BRUT_A_VERIFIER" if gaap
                                             else "EN_ATTENTE_DATA_XBRL_ABSENT")
                except Exception as exc:
                    row["Statut"] = ("EN_ATTENTE_DATA_SEC_HTTP_" + str(exc.code)
                                     if isinstance(exc, urllib.error.HTTPError)
                                     else "EN_ATTENTE_DATA_SEC_" + type(exc).__name__)
        elif not erreurs:
            row["Statut"] = "EN_ATTENTE_DATA_TICKER_ABSENT_OU_AMBIGU"
        lignes.append(row)

    colonnes = list(lignes[0])
    import io
    sortie = io.StringIO()
    writer = csv.DictWriter(sortie, fieldnames=colonnes, lineterminator="\n")
    writer.writeheader()
    writer.writerows(lignes)
    ecrire(dossier / "DIAGNOSTIC_SEC_US_5.csv", sortie.getvalue().encode("utf-8"))
    manifeste = {
        "Date_collecte_UTC": horodatage.isoformat(),
        "Univers": 5, "Lignes": len(lignes),
        "Captures_brutes": len(sources),
        "XBRL_brut_a_verifier": sum(r["Statut"] == "XBRL_BRUT_A_VERIFIER" for r in lignes),
        "Erreurs_registre": erreurs, "Sources": sources,
        "Notes_attribuees": 0, "Arbitrages": 0, "Identites_SCE_certifiees": 0,
        "Statut": "PILOTE_DIAGNOSTIQUE_NON_CERTIFIANT",
        "Fichiers_SHA256": {
            str(p.relative_to(dossier)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(dossier.rglob("*")) if p.is_file()
        },
    }
    ecrire(dossier / "MANIFESTE.json",
           (json.dumps(manifeste, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode())
    print("SEC_PILOTE_US_5", json.dumps({
        "lignes": len(lignes), "captures": len(sources),
        "xbrl_non_certifies": manifeste["XBRL_brut_a_verifier"],
        "scores": 0, "arbitrages": 0, "archive": str(dossier),
    }, ensure_ascii=False), flush=True)
    return manifeste


if __name__ == "__main__":
    executer()

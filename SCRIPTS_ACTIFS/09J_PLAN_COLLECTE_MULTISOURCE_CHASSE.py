#!/usr/bin/env python3
"""Build a read-only research queue for external candidates, without false issuer identity."""
import csv
import json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
D=BASE/"DONNEES"
SRC=D/"SORTIE_SCREENER_CANDIDATS.csv"
OUT=D/"PLAN_COLLECTE_MULTISOURCE_CHASSE.csv"
def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))
rows=read(SRC)
if not rows:
    raise RuntimeError("Chasse vide")
seen=set()
queue=[]
for r in rows:
    ticker=r["Ticker"].strip()
    date=r["Date_detection"].strip()
    key=(ticker,date)
    if not ticker or not date or key in seen:
        raise RuntimeError("Identifiant de detection absent ou duplique")
    seen.add(key)
    pays=r.get("Pays","").strip()
    devise=r.get("Devise","").strip().upper()
    # The trading venue/currency is NOT the issuer's incorporation country.
    # German secondary listings (e.g. .F/.SG) cannot establish an issuer identity.
    suffix=ticker.rsplit(".",1)[-1].upper() if "." in ticker else ""
    place_allemande=suffix in {"F","SG","DE","BE","MU","DU","HM"}
    if place_allemande:
        sources=("RAPPORTS_EMETTEUR","IDENTITE_EMETTEUR_ET_PLACE_PRIMAIRE","REGULATEUR_PAYS_EMETTEUR_A_VERIFIER","EODHD","YAHOO","ZONEBOURSE")
    elif suffix in {"TO","V","CN"} or pays.lower() == "canada":
        sources=("SEDAR_PLUS","RAPPORTS_EMETTEUR","TSX_TSXV","EODHD","YAHOO","ZONEBOURSE")
    elif suffix in {"L","LSE"} or pays.lower() in {"royaume-uni","united kingdom"}:
        sources=("COMPANIES_HOUSE","RNS_LSE","RAPPORTS_EMETTEUR","EODHD","YAHOO","ZONEBOURSE")
    elif suffix in {"PA","AS","BR","MI","MC","LS","ST","HE","OL","CO"}:
        sources=("REGULATEUR_NATIONAL","RAPPORTS_EMETTEUR","PLACE_COTATION","EODHD","YAHOO","ZONEBOURSE")
    elif devise=="USD" and not suffix:
        sources=("SEC_EDGAR_SI_EMETTEUR_US_VERIFIE","RAPPORTS_EMETTEUR","PLACE_COTATION","EODHD","YAHOO","ZONEBOURSE")
    else:
        sources=("IDENTITE_EMETTEUR_ET_PLACE_PRIMAIRE","REGULATEUR_NATIONAL_A_IDENTIFIER","RAPPORTS_EMETTEUR","EODHD","YAHOO","ZONEBOURSE")
    for i,source in enumerate(sources,1):
        queue.append({"Priorite":"APRES_REVUE_TITULAIRES","Date_detection":date,
                      "Societe":r.get("Societe",""),"Ticker":ticker,"Pays_cotation_declare":pays,
                      "Devise_cotation":devise,"Place_secondaire_potentielle":"OUI" if place_allemande else "A_VERIFIER",
                      "Pays_emetteur_verifie":"NON","Rang_source":i,"Source_cible":source,
                      "Identite_emetteur_verifiee":"NON","Preuves_financieres_validees":"NON",
                      "Statut":"A_COLLECTER_SANS_IMPUTATION"})
with OUT.open("w",encoding="utf-8",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=list(queue[0]))
    writer.writeheader()
    writer.writerows(queue)
print(json.dumps({"detections":len(rows),"pistes_sources":len(queue),"cotations_secondaires_allemandes":sum(r["Ticker"].rsplit(".",1)[-1].upper() in {"F","SG","DE","BE","MU","DU","HM"} for r in rows),"identites_certifiees":0,"scores_crees":0,"transactions":0},ensure_ascii=False))

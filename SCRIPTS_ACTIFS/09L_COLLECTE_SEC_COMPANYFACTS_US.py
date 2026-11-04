#!/usr/bin/env python3
"""Collect SEC companyfacts for previously discovered CIK leads, without imputing scores.

Requires SEC_USER_AGENT; CIK leads from 09K remain unverified. Retains raw SEC
responses and extracts explicitly labeled US-GAAP facts with accession/date/unit.
"""
import csv
import hashlib
import json
import os
import time
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
BASE=Path(__file__).resolve().parents[1]
D=BASE/"DONNEES"
SRC=D/"OBSERVATIONS_SEC_TITULAIRES_US.csv"
OUT=D/"FAITS_SEC_TITULAIRES_US.csv"
FIELDS=["ID_position","Ticker","CIK_piste","Concept","Unite","Valeur","Date_debut","Date_fin","Date_depot","Formulaire","Accession","Source_URL","SHA256_JSON","Statut_identite"]
CONCEPTS={"Revenues","RevenueFromContractWithCustomerExcludingAssessedTax","NetIncomeLoss","Assets","Liabilities","StockholdersEquity","OperatingIncomeLoss","NetCashProvidedByUsedInOperatingActivities","PaymentsToAcquirePropertyPlantAndEquipment"}
def get(url,agent):
    req=Request(url,headers={"User-Agent":agent,"Accept":"application/json","Accept-Encoding":"identity"})
    with urlopen(req,timeout=25) as r:
        raw=r.read(20_000_001)
    if len(raw)>20_000_000:raise RuntimeError("SEC response too large")
    return raw
def main():
    agent=os.environ.get("SEC_USER_AGENT","").strip()
    if "@" not in agent or len(agent)<12:raise RuntimeError("SEC_USER_AGENT required")
    if not SRC.exists():raise RuntimeError("Run 09K first")
    with SRC.open(encoding="utf-8-sig",newline="") as f: leads=list(csv.DictReader(f))
    if len({r["ID_position"] for r in leads})!=len(leads):raise RuntimeError("Duplicate positions")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder=BASE/"AUDITS"/"COLLECTE_SEC_COMPANYFACTS"/stamp
    folder.mkdir(parents=True,exist_ok=False)
    records=[];errors=[]
    for lead in leads:
        cik=lead["CIK_piste"].strip()
        if not (len(cik)==10 and cik.isdigit()):continue
        url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        try:
            raw=get(url,agent)
            data=json.loads(raw)
            if str(data.get("cik","")).zfill(10)!=cik:raise ValueError("CIK mismatch")
            sha=hashlib.sha256(raw).hexdigest()
            (folder/(cik+".json")).write_bytes(raw)
            for concept in sorted(CONCEPTS):
                item=data.get("facts",{}).get("us-gaap",{}).get(concept,{})
                for unit,values in item.get("units",{}).items():
                    # Keep the latest 5 filing observations per concept/unit; never mix periods.
                    valid=[v for v in values if v.get("form") in {"10-K","10-Q","20-F","40-F"} and v.get("filed") and v.get("end") and isinstance(v.get("val"),(int,float))]
                    for v in sorted(valid,key=lambda x:(x["filed"],x["end"]),reverse=True)[:5]:
                        records.append({"ID_position":lead["ID_position"],"Ticker":lead["Ticker"],"CIK_piste":cik,
                          "Concept":concept,"Unite":unit,"Valeur":v["val"],"Date_debut":v.get("start",""),
                          "Date_fin":v["end"],"Date_depot":v["filed"],"Formulaire":v["form"],
                          "Accession":v.get("accn",""),"Source_URL":url,"SHA256_JSON":sha,
                          "Statut_identite":"CIK_PISTE_NON_CERTIFIEE"})
        except (HTTPError,URLError,TimeoutError,ValueError,RuntimeError,json.JSONDecodeError) as exc:
            errors.append({"ticker":lead["Ticker"],"cik":cik,"error_type":type(exc).__name__})
        time.sleep(0.2)
    tmp=OUT.with_suffix(".tmp")
    with tmp.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(records)
    tmp.replace(OUT)
    (folder/"erreurs_sans_secrets.json").write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"lignes_faits_SEC":len(records),"titres_documentes":len({r["ID_position"] for r in records}),"erreurs":len(errors),"scores_crees":0,"operations":0},ensure_ascii=False))
if __name__=="__main__":main()

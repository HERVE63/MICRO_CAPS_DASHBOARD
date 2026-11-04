#!/usr/bin/env python3
"""SEC index discovery for external hunt, with explicit non-certification.

Never treats a Frankfurt secondary ticker or USD quotation as proof of a US issuer.
Only exact unique SEC ticker matches become CIK leads. No admission, score, or trade.
"""
import csv
import hashlib
import json
import os
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
BASE=Path(__file__).resolve().parents[1]
D=BASE/"DONNEES"
SRC=D/"SORTIE_SCREENER_CANDIDATS.csv"
OUT=D/"OBSERVATIONS_SEC_CHASSE_US.csv"
COLUMNS=["Date_detection","Societe_detectee","Ticker_detecte","CIK_piste","Nom_SEC","Statut_correspondance","Source_URL","SHA256_source","Date_collecte_UTC"]
def main():
    agent=os.getenv("SEC_USER_AGENT","").strip()
    if "@" not in agent or len(agent)<12:raise RuntimeError("SEC_USER_AGENT requis")
    with SRC.open(encoding="utf-8-sig",newline="") as f: candidates=list(csv.DictReader(f))
    url="https://www.sec.gov/files/company_tickers.json"
    with urlopen(Request(url,headers={"User-Agent":agent,"Accept":"application/json","Accept-Encoding":"identity"}),timeout=25) as r:
        raw=r.read(15_000_001)
    if len(raw)>15_000_000:raise RuntimeError("SEC index oversized")
    index=json.loads(raw)
    lookup={}
    for row in index.values():
        ticker=str(row.get("ticker","")).upper().strip()
        lookup.setdefault(ticker,[]).append(row)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder=BASE/"AUDITS"/"COLLECTE_SEC_CHASSE"/stamp
    folder.mkdir(parents=True,exist_ok=False)
    (folder/"company_tickers.json").write_bytes(raw)
    sha=hashlib.sha256(raw).hexdigest()
    rows=[]
    for c in candidates:
        ticker=c.get("Ticker","").strip().upper()
        # Only direct US-like tickers; never strip .F, .SG, .TO etc to force a match.
        if not ticker or "." in ticker:continue
        matches=lookup.get(ticker,[])
        if len(matches)!=1:continue
        m=matches[0]
        rows.append({"Date_detection":c.get("Date_detection",""),
          "Societe_detectee":c.get("Societe",""),"Ticker_detecte":ticker,
          "CIK_piste":str(m["cik_str"]).zfill(10),"Nom_SEC":m.get("title",""),
          "Statut_correspondance":"TICKER_EXACT_IDENTITE_NON_CERTIFIEE",
          "Source_URL":url,"SHA256_source":sha,"Date_collecte_UTC":datetime.now(timezone.utc).isoformat()})
    tmp=OUT.with_suffix(".tmp")
    with tmp.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS);writer.writeheader();writer.writerows(rows)
    tmp.replace(OUT)
    print(json.dumps({"detections":len(candidates),"pistes_CIK_chasse":len(rows),"identites_certifiees":0,"scores":0,"transactions":0},ensure_ascii=False))
if __name__=="__main__":main()

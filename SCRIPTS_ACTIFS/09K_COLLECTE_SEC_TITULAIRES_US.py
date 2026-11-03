#!/usr/bin/env python3
"""SEC EDGAR collector for US incumbents. Observations only; never scores or trades.

Requires SEC_USER_AGENT='Organization contact@example.com' per SEC fair-access rules.
Fail closed on ambiguous ticker/issuer mapping. Does not equate CIK with verified issuer.
"""
import csv
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
BASE=Path(__file__).resolve().parents[1]
D=BASE/"DONNEES"
OUT=D/"OBSERVATIONS_SEC_TITULAIRES_US.csv"
ARCH=BASE/"AUDITS"/"COLLECTE_SEC_TITULAIRES"
HEADERS=["ID_position","Societe_portefeuille","Ticker","CIK_piste","Nom_SEC","Statut_identite","HTTP_source","SHA256_reponse","Archive_reponse","Horodatage_UTC","Statut"]
def fetch(url,agent):
    request=Request(url,headers={"User-Agent":agent,"Accept":"application/json","Accept-Encoding":"identity"})
    with urlopen(request,timeout=25) as response:
        data=response.read(15_000_000)
        if len(data)>=15_000_000: raise RuntimeError("SEC payload too large")
        return data
def main():
    agent=os.environ.get("SEC_USER_AGENT","").strip()
    if "@" not in agent or len(agent)<12:
        raise RuntimeError("SEC_USER_AGENT must identify organization and contact email")
    with (D/"ETAT_INITIAL_PORTEFEUILLE_GERE.csv").open(encoding="utf-8-sig",newline="") as f:
        positions=list(csv.DictReader(f))
    if len(positions)!=40: raise RuntimeError("Expected 40 positions")
    # USD is a screening hint only: a USD listing is not proof of US incorporation.
    us=[r for r in positions if r["Devise"].strip().upper()=="USD" and "." not in r["Ticker"]]
    raw=fetch("https://www.sec.gov/files/company_tickers.json",agent)
    obj=json.loads(raw)
    lookup={}
    for value in obj.values():
        ticker=str(value.get("ticker","")).strip().upper()
        lookup.setdefault(ticker,[]).append(value)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder=ARCH/stamp
    folder.mkdir(parents=True,exist_ok=False)
    source=folder/"company_tickers.json"
    source.write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest()
    records=[]
    for p in us:
        ticker=p["Ticker"].strip().upper()
        matches=lookup.get(ticker,[])
        record=dict.fromkeys(HEADERS,"")
        record.update({"ID_position":p["ID_position"],"Societe_portefeuille":p["Societe"],
                       "Ticker":ticker,"HTTP_source":"https://www.sec.gov/files/company_tickers.json",
                       "SHA256_reponse":digest,"Archive_reponse":str(source.relative_to(BASE)),
                       "Horodatage_UTC":datetime.now(timezone.utc).isoformat(),
                       "Statut_identite":"NON_CERTIFIEE","Statut":"A_VERIFIER_PREUVES_PRIMAIRES"})
        if len(matches)==1:
            match=matches[0]
            record["CIK_piste"]=str(match["cik_str"]).zfill(10)
            record["Nom_SEC"]=match.get("title","")
        else:
            record["Statut"]="ABSENT_OU_AMBIGU_DANS_INDEX_SEC"
        records.append(record)
    tmp=OUT.with_suffix(".tmp")
    with tmp.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=HEADERS);writer.writeheader();writer.writerows(records)
    tmp.replace(OUT)
    print(json.dumps({"positions_US_cotees_a_documenter":len(us),"pistes_CIK_uniques":sum(bool(r["CIK_piste"]) for r in records),"identites_certifiees":0,"scores":0,"operations":0},ensure_ascii=False))
if __name__=="__main__":main()

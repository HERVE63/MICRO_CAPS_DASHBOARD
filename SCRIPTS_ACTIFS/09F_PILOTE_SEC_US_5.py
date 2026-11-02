#!/usr/bin/env python3
"""Pilote SEC EDGAR : cinq titulaires US, preuves XBRL sans notation automatique."""
import csv, json, os, time, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/"DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
out=ROOT/"AUDITS/DIAGNOSTIC_SEC_US_5.csv"
with src.open(encoding="utf-8",newline="") as f:
    positions=[p for p in csv.DictReader(f) if p["ID_position"] in {"1","2","3","4","5"}]
headers={"User-Agent":os.getenv("SEC_USER_AGENT","MicroCapsResearch research-contact@example.org"),"Accept":"application/json"}
def get(url):
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=30) as resp:
        return json.load(resp)
records=[]
try:
    mapping=get("https://www.sec.gov/files/company_tickers.json")
    by_ticker={}
    for item in mapping.values():
        by_ticker.setdefault(str(item["ticker"]).upper(),[]).append(item)
except Exception as exc:
    print("SEC_MAPPING_ERROR",type(exc).__name__)
    by_ticker={}
for p in positions:
    ticker=p["Ticker"].upper()
    row={"ID_position":p["ID_position"],"Societe":p["Societe"],"Ticker":ticker,"CIK":"","Nom_SEC":"","Statut":"NON_VERIFIE","Concepts_XBRL":0,"Revenues":0,"NetIncomeLoss":0,"Assets":0,"Cash":0,"Derniere_publication":""}
    matches=by_ticker.get(ticker,[])
    if len(matches)!=1:
        row["Statut"]="TICKER_ABSENT_OU_AMBIGU"
    else:
        item=matches[0];cik=str(item["cik_str"]).zfill(10)
        row["CIK"]=cik;row["Nom_SEC"]=item["title"]
        try:
            filing=get("https://data.sec.gov/submissions/CIK"+cik+".json")
            time.sleep(.2)
            if ticker not in [str(t).upper() for t in filing.get("tickers",[])]:
                row["Statut"]="IDENTITE_NON_CONFIRMEE"
            else:
                row["Statut"]="IDENTITE_TICKER_SEC_CONFIRMEE"
                recent=filing.get("filings",{}).get("recent",{})
                dates=[d for d,form in zip(recent.get("filingDate",[]),recent.get("form",[])) if form in ("10-K","10-Q")]
                row["Derniere_publication"]=max(dates) if dates else ""
                facts=get("https://data.sec.gov/api/xbrl/companyfacts/CIK"+cik+".json")
                gaap=facts.get("facts",{}).get("us-gaap",{})
                row["Concepts_XBRL"]=len(gaap)
                for name,tags in {"Revenues":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet"],"NetIncomeLoss":["NetIncomeLoss"],"Assets":["Assets"],"Cash":["CashAndCashEquivalentsAtCarryingValue"]}.items():
                    row[name]=int(any(tag in gaap and gaap[tag].get("units") for tag in tags))
                row["Statut"]="XBRL_TROUVE" if gaap else "XBRL_ABSENT"
        except urllib.error.HTTPError as e:
            row["Statut"]="SEC_HTTP_"+str(e.code)
        except Exception as e:
            row["Statut"]="SEC_ERREUR_"+type(e).__name__
    records.append(row)
    print("SEC_RESULTAT",ticker,row["Statut"],"CIK",row["CIK"],"CONCEPTS",row["Concepts_XBRL"])
    time.sleep(.3)
out.parent.mkdir(parents=True,exist_ok=True)
with out.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
print("SEC_BILAN",sum(r["Statut"]=="XBRL_TROUVE" for r in records),"/",len(records),"XBRL; SCORES=0; ARBITRAGES=0")

#!/usr/bin/env python3
"""Join actual 09N technical output with 09L SEC facts; report only evidence.
Never synthesize MCPA scores or write virtual trades.
"""
import csv,json
from pathlib import Path
D=Path(__file__).resolve().parents[1]/"DONNEES"
def read(name):
 p=D/name
 if not p.exists():return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
 holdings=read("ETAT_INITIAL_PORTEFEUILLE_GERE.csv")
 if len(holdings)!=40:raise RuntimeError("Expected exactly 40 incumbents")
 indicators={r["Ticker"]:r for r in read("INDICATEURS_YAHOO_40.csv")}
 coverage={r["Ticker"]:r for r in read("COUVERTURE_HISTORIQUES_YAHOO_40.csv")}
 eod={r["Ticker"]:r for r in read("COLLECTE_DIRECTE_40_TITULAIRES.csv")}
 facts=read("FAITS_SEC_TITULAIRES_US.csv")
 fact_tickers=set()
 for r in facts:
  for k in ("Ticker","ticker","TICKER"):
   if r.get(k):fact_tickers.add(r[k].strip().upper())
 out=[]
 for p in holdings:
  ticker=p["Ticker"]; i=indicators.get(ticker,{});c=coverage.get(ticker,{});e=eod.get(ticker,{})
  out.append({"ID_position":p["ID_position"],"Ticker":ticker,"Devise":p["Devise"],
    "Seances":c.get("Nb_seances",""),"Statut_historique":c.get("Statut","ABSENT"),
    "Statut_technique":i.get("Statut_indicateurs","ABSENT"),
    "MM200_disponible":bool(i.get("MM200")),"Momentum_1m_disponible":i.get("Momentum_1m","")!="",
    "Momentum_3m_disponible":i.get("Momentum_3m","")!="",
    "Momentum_6m_disponible":i.get("Momentum_6m","")!="",
    "Momentum_12m_disponible":i.get("Momentum_12m","")!="",
    "SEC_faits_presents":ticker.upper() in fact_tickers,
    "EODHD_statut_cours":e.get("Statut_cours","ABSENT"),
    "EODHD_date_cours":e.get("Date_cours",""),
    "EODHD_SHA256_EOD_JSON":e.get("SHA256_EOD_JSON",""),
    "EODHD_archive_EOD_JSON":e.get("Archive_EOD_JSON",""),
    "EODHD_statut_fondamentaux":e.get("Statut","ABSENT"),
    "MCPA_valide":"NON","Arbitrage_autorise":"NON"})
 target=D/"COUVERTURE_PREUVE_MCPA_40.csv"
 with target.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
 print(json.dumps({"titulaires":len(out),"techniques_complets":sum(r["Statut_technique"]=="OK" for r in out),"sec_tickers_avec_faits":sum(r["SEC_faits_presents"] for r in out),"cours_EODHD_observes":sum(r["EODHD_statut_cours"]=="COURS_FOURNISSEUR_NON_CERTIFIE" for r in out),"scores_MCPA_valides":0,"arbitrages_autorises":0},ensure_ascii=False))
if __name__=="__main__":main()

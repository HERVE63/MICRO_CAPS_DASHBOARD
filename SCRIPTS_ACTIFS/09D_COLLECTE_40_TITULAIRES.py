# -*- coding: utf-8 -*-
"""Collecte EODHD directe : aucune note calculée ou valeur manquante inventée."""
from pathlib import Path
import os
import requests
import pandas as pd
from datetime import datetime, timezone

BASE=Path(__file__).resolve().parents[1]
SRC=BASE/"DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
OUT=BASE/"DONNEES/COLLECTE_DIRECTE_40_TITULAIRES.csv"
API=os.environ.get("EODHD_API_TOKEN") or os.environ.get("EODHD_API_KEY")
def collecter():
    positions=pd.read_csv(SRC,dtype={"Ticker":str})
    if len(positions)!=40 or positions.Ticker.nunique()!=40:
        raise RuntimeError("Inventaire des 40 positions incoherent")
    records=[]
    for _,p in positions.iterrows():
        row={"ID_position":p.ID_position,"Societe":p.Societe,"Ticker":p.Ticker,
             "Devise":p.Devise,"Horodatage_UTC":datetime.now(timezone.utc).isoformat(),
             "Source":"EODHD fundamentals","Statut":"EN_ATTENTE_CLE" if not API else "ECHEC"}
        if API:
            try:
                # EODHD expects exchange suffixes different from Yahoo for many listings.
                # Never guess ticker conversions; preserve the requested identifier.
                response=requests.get("https://eodhd.com/api/fundamentals/"+str(p.Ticker),
                    params={"api_token":API,"fmt":"json"},timeout=25)
                response.raise_for_status()
                j=response.json()
                if not isinstance(j,dict) or "General" not in j:
                    row["Statut"]="REPONSE_NON_EXPLOITABLE"
                else:
                    g=j.get("General") or {}
                    h=j.get("Highlights") or {}
                    v=j.get("Valuation") or {}
                    f=j.get("Financials") or {}
                    b=(f.get("Balance_Sheet") or {}).get("quarterly") or {}
                    cf=(f.get("Cash_Flow") or {}).get("quarterly") or {}
                    row.update({"Statut":"DONNEES_RECUES",
                      "Code_EODHD":g.get("Code"),"Exchange_EODHD":g.get("Exchange"),
                      "MarketCapitalization":h.get("MarketCapitalization"),
                      "EBITDA":h.get("EBITDA"),"PERatio":v.get("TrailingPE"),
                      "RevenueTTM":h.get("RevenueTTM"),
                      "ProfitMargin":h.get("ProfitMargin"),
                      "QuarterlyEarningsGrowthYOY":h.get("QuarterlyEarningsGrowthYOY"),
                      "BalanceSheetPeriods":len(b),"CashFlowPeriods":len(cf)})
            except Exception as exc:
                row["Erreur"]=str(exc)[:200]
        records.append(row)
    OUT.parent.mkdir(exist_ok=True,parents=True)
    pd.DataFrame(records).to_csv(OUT,index=False)
    print(pd.DataFrame(records).Statut.value_counts().to_string())
    return records
if __name__=="__main__":
    collecter()

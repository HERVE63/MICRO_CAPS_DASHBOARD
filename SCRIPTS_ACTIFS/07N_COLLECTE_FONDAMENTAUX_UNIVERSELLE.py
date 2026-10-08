from pathlib import Path
from datetime import date
import pandas as pd
import yfinance as yf
B=Path(__file__).resolve().parent.parent
D=B/"DONNEES"
SRC=D/"UNIVERS_PRET_FILTRES_OBJECTIFS.csv"
OUT=D/"FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv"
AUD=D/"AUDIT_FONDAMENTAUX_CANDIDATS.csv"
def val(info,*keys):
    for k in keys:
        v=info.get(k)
        if v is not None: return v
    return None
def executer():
    u=pd.read_csv(SRC)
    u=u[u["Admissible_filtre_marche"].eq("OUI")].copy()
    rows=[]
    for i,t in enumerate(u["Ticker"].astype(str)):
        try:
            info=yf.Ticker(t).get_info()
        except Exception:
            info={}
        rows.append({"Date_scan":date.today().isoformat(),"Ticker":t,
          "CA_TTM":val(info,"totalRevenue"),"Croissance_CA":val(info,"revenueGrowth"),
          "Marge_brute":val(info,"grossMargins"),"EBITDA":val(info,"ebitda"),
          "FCF":val(info,"freeCashflow"),"Cash":val(info,"totalCash"),
          "Dette_totale":val(info,"totalDebt"),"Dette_nette":val(info,"netDebt"),
          "Actions":val(info,"sharesOutstanding"),"Insiders_pct":val(info,"heldPercentInsiders"),
          "Source_fondamentaux":"Yahoo Finance / yfinance get_info",
          "Statut_fondamentaux":"OK" if info else "MANQUANTE"})
        if (i+1)%100==0: print("collectes",i+1)
    o=pd.DataFrame(rows); o.to_csv(OUT,index=False)
    ok=(o["Statut_fondamentaux"]=="OK")
    pd.DataFrame([{"Nb_candidats":len(o),"Nb_source_OK":int(ok.sum()),"Nb_source_manquante":int((~ok).sum())}]).to_csv(AUD,index=False)
    print("Fondamentaux",len(o),"OK",int(ok.sum()),"MANQUANTE",int((~ok).sum()))
    return o
if __name__=="__main__": executer()

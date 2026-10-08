"""Enrichissement officiel SEC EDGAR: identite CIK et metadonnees de depots.
Aucune note SSI automatique. Respecte les identites ambigues et les echecs de source.
Variable SEC_USER_AGENT requise: 'Projet Contact contact@example.org'.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, os, time
from urllib.request import Request, urlopen
import pandas as pd

D=Path(__file__).resolve().parents[1]/"DONNEES"
SRC=D/"DOSSIERS_SSI_A_QUALIFIER.csv"
OUT=D/"PREUVES_SEC_EDGAR_SSI.csv"
AUD=D/"AUDIT_PREUVES_SEC_SSI.csv"
BASE="https://www.sec.gov"
DATA="https://data.sec.gov"
FORMES={"10-K","10-K/A","10-Q","10-Q/A","8-K","DEF 14A","4","3","5","20-F","6-K","40-F"}
def lire_json(url,agent):
 req=Request(url,headers={"User-Agent":agent,"Accept":"application/json","Accept-Encoding":"identity"})
 with urlopen(req,timeout=25) as resp: return json.load(resp)
def executer():
 agent=os.environ.get("SEC_USER_AGENT","").strip()
 if not agent or "@" not in agent: raise RuntimeError("SEC_USER_AGENT explicite avec contact requis")
 if not SRC.exists(): raise RuntimeError("Dossiers SSI absents")
 df=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 if df.empty or df["Ticker"].duplicated().any(): raise RuntimeError("Dossiers SSI vides ou tickers dupliques")
 reg=lire_json(BASE+"/files/company_tickers.json",agent)
 mapping={}
 for v in reg.values():
  ticker=str(v.get("ticker","")).upper().strip()
  if ticker: mapping.setdefault(ticker,set()).add(str(v["cik_str"]).zfill(10))
 rows=[]
 for _,r in df.iterrows():
  ticker=str(r["Ticker"]).strip()
  # Les suffixes .TO, .V, .L etc ne sont pas des identifiants SEC.
  candidats=mapping.get(ticker.upper(),set())
  item={"Ticker":ticker,"Societe":r.get("Societe",""),"Date_collecte_UTC":datetime.now(timezone.utc).isoformat(),
        "Source_registre":BASE+"/files/company_tickers.json",
        "CIK":"MANQUANTE","Statut_SEC":"NON_COUVERT","Depots": "[]","Nb_depots":0}
  if len(candidats)>1:
   item["Statut_SEC"]="IDENTITE_AMBIGUE"
  elif len(candidats)==1:
   cik=next(iter(candidats));item["CIK"]=cik
   url=DATA+"/submissions/CIK"+cik+".json"
   try:
    sub=lire_json(url,agent)
    nom=str(sub.get("name","")).strip()
    # Ne pas associer les preuves si l'identite emetteur reste a confirmer.
    item["Nom_SEC"]=nom;item["Source_depots"]=url
    recent=sub.get("filings",{}).get("recent",{})
    depots=[]
    for i,form in enumerate(recent.get("form",[])):
     if form not in FORMES: continue
     acc=recent.get("accessionNumber",[])
     dates=recent.get("filingDate",[])
     if i>=len(acc) or i>=len(dates): continue
     depots.append({"form":form,"date":dates[i],"accession":acc[i]})
     if len(depots)>=30: break
    item["Depots"]=json.dumps(depots,ensure_ascii=False)
    item["Nb_depots"]=len(depots)
    item["Statut_SEC"]="A_VERIFIER_IDENTITE_ET_CONTENU"
   except Exception as exc:
    item["Statut_SEC"]="ERREUR_SOURCE"
    item["Erreur"]=type(exc).__name__
   time.sleep(0.15)
  rows.append(item)
 out=pd.DataFrame(rows)
 OUT.parent.mkdir(parents=True,exist_ok=True)
 out.to_csv(OUT,index=False)
 counts=out["Statut_SEC"].value_counts().to_dict()
 pd.DataFrame([{"Dossiers":len(out),**counts,"Scores_SSI_calcules":0}]).to_csv(AUD,index=False)
 print("SEC EDGAR",counts)
 return out
if __name__=="__main__": executer()

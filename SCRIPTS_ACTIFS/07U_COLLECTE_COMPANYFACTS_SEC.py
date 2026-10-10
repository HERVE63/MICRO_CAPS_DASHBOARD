"""Collecte SEC companyfacts: faits XBRL avec unite, periode, depot et provenance.
Aucun score SSI automatique; identite CIK non verifiee reste non admissible.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, os, time
import pandas as pd
from urllib.request import Request, urlopen

D=Path(__file__).resolve().parents[1]/"DONNEES"
SRC=D/"PREUVES_SEC_EDGAR_SSI.csv"
OUT=D/"FAITS_FINANCIERS_SEC_SSI.csv"
AUD=D/"AUDIT_FAITS_FINANCIERS_SEC_SSI.csv"
TAGS={
 "Revenues":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet"],
 "Cash":["CashAndCashEquivalentsAtCarryingValue"],
 "Assets":["Assets"],
 "Liabilities":["Liabilities"],
 "OperatingIncome":["OperatingIncomeLoss"],
 "NetIncome":["NetIncomeLoss"],
 "OperatingCashFlow":["NetCashProvidedByUsedInOperatingActivities"],
 "Shares":["CommonStockSharesOutstanding"],
}
TAGS_IFRS={
 "Revenues":["Revenue"], "Cash":["CashAndCashEquivalents"],
 "Assets":["Assets"], "Liabilities":["Liabilities"],
 "OperatingIncome":["ProfitLossFromOperatingActivities"], "NetIncome":["ProfitLoss"],
 "OperatingCashFlow":["CashFlowsFromUsedInOperatingActivities"],
}
def lire_json(url,agent):
 req=Request(url,headers={"User-Agent":agent,"Accept":"application/json","Accept-Encoding":"identity"})
 with urlopen(req,timeout=25) as response: return json.load(response)
def executer():
 agent=os.environ.get("SEC_USER_AGENT","").strip()
 if "@" not in agent: raise RuntimeError("SEC_USER_AGENT avec contact requis")
 if not SRC.exists(): raise RuntimeError("PREUVES_SEC_EDGAR_SSI absent")
 d=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 if d.empty or d["Ticker"].duplicated().any(): raise RuntimeError("Source vide ou tickers dupliques")
 rows=[]; audits=[]
 for _,r in d.iterrows():
  ticker=r["Ticker"]; cik=r.get("CIK","")
  if r.get("Statut_SEC") not in ("A_VERIFIER_IDENTITE_ET_CONTENU","IDENTITE_VERIFIEE") or not cik.isdigit():
   audits.append({"Ticker":ticker,"Statut":"NON_COUVERT_OU_IDENTITE_AMBIGUE","Nb_faits":0})
   continue
  url="https://data.sec.gov/api/xbrl/companyfacts/CIK"+cik.zfill(10)+".json"
  try:
   obj=lire_json(url,agent)
   if str(obj.get("cik","")).zfill(10)!=cik.zfill(10):
    audits.append({"Ticker":ticker,"Statut":"CIK_INCOHERENT","Nb_faits":0});continue
   count=0
   for taxonomie,table in [("us-gaap",TAGS),("ifrs-full",TAGS_IFRS)]:
    facts=obj.get("facts",{}).get(taxonomie,{})
    for concept,aliases in table.items():
     for tag in aliases:
      node=facts.get(tag)
      if not node: continue
      for unit,values in node.get("units",{}).items():
       # Conserver les valeurs telles que deposees: pas de melange d'unites/periodes.
       for f in values:
        if f.get("form") not in ("10-K","10-Q","20-F","40-F"): continue
        if not f.get("filed") or not f.get("end") or "val" not in f: continue
        limite=os.getenv("MICRO_CAPS_AS_OF",datetime.now(timezone.utc).date().isoformat())
        try:
         depot=datetime.strptime(f["filed"],"%Y-%m-%d").date()
         fin=datetime.strptime(f["end"],"%Y-%m-%d").date()
        except (ValueError,TypeError):continue
        if f["filed"]>limite or fin>depot:continue
        rows.append({"Ticker":ticker,"CIK":cik,"Concept":concept,"Tag_SEC":tag,"Taxonomie_SEC":taxonomie,
         "Valeur":f["val"],"Unite":unit,"Debut_periode":f.get("start",""),
         "Fin_periode":f["end"],"Date_depot":f["filed"],
         "Formulaire":f["form"],"Accession":f.get("accn",""),
         "Exercice":f.get("fy",""),"Periode":f.get("fp",""),
         "Source_officielle":url,"Date_collecte_UTC":datetime.now(timezone.utc).isoformat(),
         "Statut_preuve":"A_VERIFIER_IDENTITE_ET_PERIODE"})
        count+=1
   audits.append({"Ticker":ticker,"Statut":"FAITS_BRUTS_A_VERIFIER" if count else "AUCUN_FAIT_US_GAAP_OU_IFRS","Nb_faits":count})
  except Exception as exc:
   audits.append({"Ticker":ticker,"Statut":"ERREUR_SOURCE_"+type(exc).__name__,"Nb_faits":0})
  time.sleep(0.15)
 columns=["Ticker","CIK","Concept","Tag_SEC","Taxonomie_SEC","Valeur","Unite","Debut_periode","Fin_periode","Date_depot","Formulaire","Accession","Exercice","Periode","Source_officielle","Date_collecte_UTC","Statut_preuve"]
 pd.DataFrame(rows,columns=columns).to_csv(OUT,index=False)
 pd.DataFrame(audits,columns=["Ticker","Statut","Nb_faits"]).to_csv(AUD,index=False)
 print("SEC companyfacts:",len(audits),"emetteurs",len(rows),"faits bruts; aucun SSI attribue")
 return rows
if __name__=="__main__": executer()

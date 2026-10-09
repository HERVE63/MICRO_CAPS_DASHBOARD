"""Index documentaire SEC gouvernance et dirigeants, sans estimation de participation.
Les formulaires 3/4/5 signalent des declarations; DEF 14A des documents
de gouvernance. Aucun pourcentage, achat net ou note B4/B5 n'est deduit.
"""
from pathlib import Path
import json, os
from datetime import datetime, timezone
import pandas as pd
D=Path(__file__).resolve().parents[1]/"DONNEES"
SRC=D/"PREUVES_SEC_EDGAR_SSI.csv"
OUT=D/"PISTES_GOUVERNANCE_SEC_SSI.csv"
AUD=D/"AUDIT_GOUVERNANCE_SEC_SSI.csv"
FORMES={"3":"B4","4":"B4","5":"B4","DEF 14A":"B4_B5","10-K":"B5","10-K/A":"B5","20-F":"B5","40-F":"B5"}
def executer():
 if not SRC.exists():raise RuntimeError("Index SEC absent")
 d=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 if d.empty or "Ticker" not in d or d["Ticker"].duplicated().any():
  raise RuntimeError("Index SEC invalide")
 rows=[];anomalies=0
 for _,r in d.iterrows():
  if r.get("Statut_SEC") not in ("A_VERIFIER_IDENTITE_ET_CONTENU","IDENTITE_VERIFIEE"):continue
  try: depots=json.loads(r.get("Depots","[]"))
  except (ValueError,TypeError): anomalies+=1;continue
  if not isinstance(depots,list):anomalies+=1;continue
  for f in depots:
   if not isinstance(f,dict) or f.get("form") not in FORMES:continue
   try:date_depot=datetime.strptime(f.get("date",""),"%Y-%m-%d").date()
   except (ValueError,TypeError):anomalies+=1;continue
   if f["date"]>os.getenv("MICRO_CAPS_AS_OF",datetime.now(timezone.utc).date().isoformat()):anomalies+=1;continue
   url=f.get("url_archive_officielle","")
   if not url.startswith("https://www.sec.gov/Archives/edgar/data/"):
    anomalies+=1;continue
   rows.append({"Ticker":r["Ticker"],"Societe":r.get("Societe",""),
    "CIK":r.get("CIK",""),"Bloc_SSI_cible":FORMES[f["form"]],
    "Formulaire":f["form"],"Date_depot":f.get("date",""),
    "Accession":f.get("accession",""),"URL_archive_officielle":url,
    "Statut_identite":"NON_VERIFIEE","Statut_contenu":"A_LIRE",
    "Participation_dirigeants_pct":"MANQUANTE","Variation_titres":"MANQUANTE",
    "Note_SSI_attribuee":"NON"})
 cols=["Ticker","Societe","CIK","Bloc_SSI_cible","Formulaire","Date_depot",
       "Accession","URL_archive_officielle","Statut_identite","Statut_contenu",
       "Participation_dirigeants_pct","Variation_titres","Note_SSI_attribuee"]
 pd.DataFrame(rows,columns=cols).to_csv(OUT,index=False)
 pd.DataFrame([{"Dossiers_SEC":len(d),"Pistes_gouvernance":len(rows),
  "Dossiers_avec_pistes":len({x["Ticker"] for x in rows}),
  "Anomalies":anomalies,"Notes_SSI_attribuees":0}]).to_csv(AUD,index=False)
 print("Gouvernance SEC:",len(rows),"pistes non verifiees")
 return rows
if __name__=="__main__":executer()

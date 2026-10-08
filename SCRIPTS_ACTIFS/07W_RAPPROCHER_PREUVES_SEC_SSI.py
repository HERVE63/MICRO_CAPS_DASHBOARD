"""Rapprochement documentaire SEC -> SSI, lecture seule, sans modifier les notes."""
from pathlib import Path
import pandas as pd
D=Path(__file__).resolve().parents[1]/"DONNEES"
DOS=D/"DOSSIERS_SSI_A_QUALIFIER.csv"
SEC=D/"PREUVES_SEC_EDGAR_SSI.csv"
FACT=D/"FAITS_SEC_COMPARABLES_SSI.csv"
OUT=D/"RAPPROCHEMENT_PREUVES_SEC_SSI.csv"
AUD=D/"AUDIT_RAPPROCHEMENT_SEC_SSI.csv"
BLOCS={"Cash":"B1","Assets":"B1","Liabilities":"B1","OperatingIncome":"B2","NetIncome":"B2","OperatingCashFlow":"B2","Revenues":"B3","Shares":"B5"}
def executer():
 for p in (DOS,SEC,FACT):
  if not p.exists():raise RuntimeError("Fichier requis absent: "+p.name)
 dossiers=pd.read_csv(DOS,dtype=str,keep_default_na=False)
 sec=pd.read_csv(SEC,dtype=str,keep_default_na=False)
 faits=pd.read_csv(FACT,dtype=str,keep_default_na=False)
 for name,df in (("dossiers",dossiers),("SEC",sec)):
  if "Ticker" not in df or df["Ticker"].duplicated().any():raise RuntimeError("Tickers invalides ou dupliques: "+name)
 if not {"Ticker","CIK","Concept","Source_officielle","Date_depot","Fin_periode","Valeur","Unite","Statut_comparabilite"}.issubset(faits.columns):
  raise RuntimeError("Schema faits SEC incomplet")
 reg=sec.set_index("Ticker")
 admis=set(dossiers["Ticker"])
 rows=[]
 for _,f in faits.iterrows():
  ticker=f["Ticker"]
  if ticker not in admis:continue
  identite=reg.loc[ticker] if ticker in reg.index else None
  if identite is None or str(identite.get("CIK",""))!=f["CIK"]:continue
  bloc=BLOCS.get(f["Concept"],"HORS_BLOCS")
  statut="A_VERIFIER_IDENTITE_ET_DOCUMENT"
  if identite.get("CIK_verifie","NON")=="OUI" and identite.get("Statut_SEC")=="IDENTITE_VERIFIEE":
   statut="A_VERIFIER_CONTENU_ET_PERIODE"
  rows.append({"Ticker":ticker,"Societe":dossiers.set_index("Ticker").loc[ticker].get("Societe",""),
   "CIK":f["CIK"],"Bloc_SSI_cible":bloc,"Concept":f["Concept"],"Valeur":f["Valeur"],
   "Unite":f["Unite"],"Fin_periode":f["Fin_periode"],"Date_depot":f["Date_depot"],
   "Source_officielle":f["Source_officielle"],"Statut_preuve":statut,
   "Statut_comparabilite":f["Statut_comparabilite"],"Note_SSI_attribuee":"NON"})
 cols=["Ticker","Societe","CIK","Bloc_SSI_cible","Concept","Valeur","Unite","Fin_periode","Date_depot","Source_officielle","Statut_preuve","Statut_comparabilite","Note_SSI_attribuee"]
 pd.DataFrame(rows,columns=cols).to_csv(OUT,index=False)
 pd.DataFrame([{"Dossiers_SSI":len(dossiers),"Faits_rapproches":len(rows),
  "Emetteurs_avec_faits":len({r["Ticker"] for r in rows}),"Notes_SSI_attribuees":0,
  "Statut":"PISTES_DOCUMENTAIRES_NON_VALIDEES"}]).to_csv(AUD,index=False)
 print("Rapprochement SEC SSI:",len(rows),"faits; zero score")
 return rows
if __name__=="__main__":executer()

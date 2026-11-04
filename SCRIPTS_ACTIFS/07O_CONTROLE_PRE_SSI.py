from pathlib import Path
import pandas as pd
B=Path(__file__).resolve().parent.parent; D=B/"DONNEES"
F=D/"FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv"; U=D/"UNIVERS_PRET_FILTRES_OBJECTIFS.csv"
OUT=D/"CANDIDATS_PRETS_SSI.csv"; HOLD=D/"CANDIDATS_SSI_DONNEES_MANQUANTES.csv"; AUD=D/"AUDIT_PRE_SSI.csv"
def executer():
 f=pd.read_csv(F) if F.exists() and F.stat().st_size else pd.DataFrame(columns=["Ticker"])
 u=pd.read_csv(U)
 if "Ticker" not in f.columns or "Ticker" not in u.columns:
  raise RuntimeError("Ticker absent dans les entrees pre-SSI")
 if f["Ticker"].duplicated().any() or u["Ticker"].duplicated().any():
  raise RuntimeError("Identifiants ticker dupliques avant pre-SSI")
 x=u[u["Admissible_filtre_marche"].eq("OUI")].merge(f,on="Ticker",how="left",suffixes=("","_fond"),validate="one_to_one")
 # Données indispensables observables pour ouvrir l'évaluation SSI; aucune note n'est imputée.
 req=["CA_TTM","Cash","Dette_totale","Actions","Insiders_pct"]
 for c in req:
  if c not in x.columns: x[c]=pd.NA
  x[c]=pd.to_numeric(x[c],errors="coerce")
 # Les champs facultatifs sont conserves vides, jamais inventes.
 for c in ["EBITDA","FCF","Croissance_CA","Marge_brute","Source_fondamentaux","Date_scan","Date_scan_fond"]:
  if c not in x.columns: x[c]=pd.NA
 x["Date_scan_fond"]=x["Date_scan_fond"].fillna(x["Date_scan"])
 complete=x[req].notna().all(axis=1)
 # Filtres d'élimination stricts uniquement quand les données permettent de les constater.
 no_activity=x["CA_TTM"].fillna(0).le(0) & x["CA_TTM"].notna()
 x["Statut_pre_SSI"]="PRET_SSI"
 x.loc[~complete,"Statut_pre_SSI"]="EN_ATTENTE_DATA"
 x.loc[complete & no_activity,"Statut_pre_SSI"]="ELIMINATION_ACTIVITE_NULLE"
 ready=x[x["Statut_pre_SSI"].eq("PRET_SSI")].copy()
 hold=x[~x["Statut_pre_SSI"].eq("PRET_SSI")].copy()
 ready.to_csv(OUT,index=False); hold.to_csv(HOLD,index=False)
 pd.DataFrame([{"Univers_marche_OK":len(x),"Prets_SSI":len(ready),"Donnees_manquantes":int((x["Statut_pre_SSI"]=="EN_ATTENTE_DATA").sum()),"Elimination_activite_nulle":int((x["Statut_pre_SSI"]=="ELIMINATION_ACTIVITE_NULLE").sum()),"SSI_calcule":"NON"}]).to_csv(AUD,index=False)
 print("prets SSI",len(ready),"retenus/manquants",len(hold))
 return ready
if __name__=="__main__": executer()

# production

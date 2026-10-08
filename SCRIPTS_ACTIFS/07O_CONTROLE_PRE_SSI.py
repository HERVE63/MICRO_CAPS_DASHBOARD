from pathlib import Path
import pandas as pd
B=Path(__file__).resolve().parent.parent; D=B/"DONNEES"
F=D/"FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv"; U=D/"UNIVERS_PRET_FILTRES_OBJECTIFS.csv"
OUT=D/"CANDIDATS_PRETS_SSI.csv"; HOLD=D/"CANDIDATS_SSI_DONNEES_MANQUANTES.csv"; AUD=D/"AUDIT_PRE_SSI.csv"
def executer():
 f=pd.read_csv(F); u=pd.read_csv(U)
 x=u[u["Admissible_filtre_marche"].eq("OUI")].merge(f,on="Ticker",how="left",suffixes=("","_fond"))
 # Données indispensables observables pour ouvrir l'évaluation SSI; aucune note n'est imputée.
 req=["CA_TTM","Cash","Dette_totale","Actions","Insiders_pct"]
 for c in req: x[c]=pd.to_numeric(x[c],errors="coerce")
 complete=x[req].notna().all(axis=1)
 # Filtres d'élimination stricts uniquement quand les données permettent de les constater.
 no_activity=x["CA_TTM"].fillna(0).le(0) & x["CA_TTM"].notna()
 x["Statut_pre_SSI"]="PRET_SSI"
 x.loc[~complete,"Statut_pre_SSI"]="DONNEES_INDISPENSABLES_MANQUANTES"
 x.loc[complete & no_activity,"Statut_pre_SSI"]="ELIMINATION_ACTIVITE_NULLE"
 ready=x[x["Statut_pre_SSI"].eq("PRET_SSI")].copy()
 hold=x[~x["Statut_pre_SSI"].eq("PRET_SSI")].copy()
 ready.to_csv(OUT,index=False); hold.to_csv(HOLD,index=False)
 pd.DataFrame([{"Univers_marche_OK":len(x),"Prets_SSI":len(ready),"Donnees_manquantes":int((x["Statut_pre_SSI"]=="DONNEES_INDISPENSABLES_MANQUANTES").sum()),"Elimination_activite_nulle":int((x["Statut_pre_SSI"]=="ELIMINATION_ACTIVITE_NULLE").sum()),"SSI_calcule":"NON"}]).to_csv(AUD,index=False)
 print("prets SSI",len(ready),"retenus/manquants",len(hold))
 return ready
if __name__=="__main__": executer()

# production

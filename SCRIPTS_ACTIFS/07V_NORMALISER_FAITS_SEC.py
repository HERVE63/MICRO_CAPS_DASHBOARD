"""Normalisation prudente des faits XBRL SEC, sans mélange de périodes ni score SSI.

Sélectionne des observations FY et Q1-Q4 seulement si frame SEC explicite,
unité homogène et dépôt daté. Les autres observations restent dans les faits bruts.
"""
from pathlib import Path
import re
import pandas as pd

D=Path(__file__).resolve().parents[1]/"DONNEES"
SRC=D/"FAITS_FINANCIERS_SEC_SSI.csv"
OUT=D/"FAITS_SEC_COMPARABLES_SSI.csv"
AUD=D/"AUDIT_COMPARABILITE_SEC_SSI.csv"
FRAME=re.compile(r"^CY[0-9]{4}(?:Q[1-4])?$")
FLUX={"Revenues","OperatingIncome","NetIncome","OperatingCashFlow"}
def executer():
 if not SRC.exists(): raise RuntimeError("Faits SEC absents")
 df=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 cols=["Ticker","CIK","Concept","Tag_SEC","Valeur","Unite","Debut_periode","Fin_periode","Date_depot","Formulaire","Accession","Exercice","Periode","Source_officielle","Date_collecte_UTC","Statut_preuve"]
 if any(c not in df for c in cols): raise RuntimeError("Schema XBRL incomplet")
 if df.empty:
  pd.DataFrame(columns=cols+["Cadence","Statut_comparabilite"]).to_csv(OUT,index=False)
  pd.DataFrame([{"Faits_bruts":0,"Faits_retenus":0,"Faits_ecartes":0}]).to_csv(AUD,index=False)
  return
 for c in ("Date_depot","Fin_periode"):
  df[c]=pd.to_datetime(df[c],errors="coerce")
 if df["Date_depot"].isna().any() or df["Fin_periode"].isna().any():
  raise RuntimeError("Dates SEC invalides: controle necessaire")
 df["Valeur_numerique"]=pd.to_numeric(df["Valeur"],errors="coerce")
 df["Cadence"]="A_VERIFIER"
 df["Statut_comparabilite"]="PERIODE_OU_UNITE_A_VERIFIER"
 # Les flux exigent un début de période et une durée proche du trimestre ou de l'année.
 deb=pd.to_datetime(df["Debut_periode"],errors="coerce")
 jours=(df["Fin_periode"]-deb).dt.days
 flux=df["Concept"].isin(FLUX)
 annuel=flux & jours.between(330,380)
 trimestriel=flux & jours.between(70,110)
 instant=~flux & df["Debut_periode"].eq("")
 df.loc[annuel,"Cadence"]="ANNUEL"
 df.loc[trimestriel,"Cadence"]="TRIMESTRIEL"
 df.loc[instant,"Cadence"]="INSTANTANE"
 # Ne jamais mélanger USD, shares et autres unités, ni déduire un trimestre d'un cumul.
 unite=(df["Unite"].eq("USD") & df["Concept"].ne("Shares")) | (df["Unite"].eq("shares") & df["Concept"].eq("Shares"))
 admissible=(annuel | trimestriel | instant) & unite & df["Valeur_numerique"].notna()
 df.loc[admissible,"Statut_comparabilite"]="FORMAT_PERIODE_PLAUSIBLE_A_VERIFIER"
 # Dépôts successifs: conserver la version la plus récente mais ne pas effacer les bruts.
 ok=df[admissible].copy()
 keys=["Ticker","CIK","Concept","Tag_SEC","Unite","Debut_periode","Fin_periode","Cadence"]
 ok=ok.sort_values(["Date_depot","Accession"]).drop_duplicates(keys,keep="last")
 ok["Date_depot"]=ok["Date_depot"].dt.strftime("%Y-%m-%d")
 ok["Fin_periode"]=ok["Fin_periode"].dt.strftime("%Y-%m-%d")
 ok.to_csv(OUT,index=False)
 pd.DataFrame([{"Faits_bruts":len(df),"Faits_retenus":len(ok),
  "Faits_ecartes":len(df)-len(ok),"Notes_SSI_attribuees":0,
  "Statut":"DONNEES_COMPARABLES_A_VERIFIER_AVANT_NOTATION"}]).to_csv(AUD,index=False)
 print("SEC comparabilite:",len(ok),"/",len(df),"faits conserves; SSI non calcule")
 return ok
if __name__=="__main__": executer()

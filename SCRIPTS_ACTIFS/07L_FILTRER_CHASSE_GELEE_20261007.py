import pandas as pd, subprocess, io
from pathlib import Path
D=Path("DONNEES"); REF="5fc2fdf"
def frozen(path):
 s=subprocess.check_output(["git","show",f"{REF}:{path}"],text=True)
 return pd.read_csv(io.StringIO(s),dtype=str).fillna("")
src=frozen("DONNEES/SORTIE_CHASSEUR_EXISTANT.csv")
mar=frozen("DONNEES/PRESELECTION_VARIABLES_MARCHE.csv")
reg=pd.read_csv(D/"REGISTRE_IDENTITE_MICRO_CAPS.csv",dtype=str).fillna("")
r=reg[["Ticker","Exchange","Etat_registre"]].drop_duplicates(["Ticker","Exchange"],keep="last")
x=src.merge(r,on=["Ticker","Exchange"],how="left")
x["Etat_registre"]=x["Etat_registre"].replace("","IDENTITE_NON_DOCUMENTEE")
bad=x.Etat_registre.eq("HORS_UNIVERS_IDENTITE_INSUFFISANTE") | x.Etat_registre.str.contains("SECONDAIRE",na=False)
ok=x[~bad].copy(); rej=x[bad].copy()
# Jointure des variables marche de LA MEME chasse gelee.
mcols=[c for c in mar.columns if c!="Ticker"]
ok=ok.merge(mar[["Ticker"]+mcols].drop_duplicates("Ticker",keep="last"),on="Ticker",how="left")
ok.to_csv(D/"UNIVERS_NETTOYE_CHASSE_2026-10-07.csv",index=False)
rej.to_csv(D/"REJETS_IDENTITE_CHASSE_2026-10-07.csv",index=False)
status="Statut_donnees_marche"
market_ok=int((ok[status]=="OK").sum()) if status in ok else 0
market_missing=len(ok)-market_ok
pd.DataFrame([{"Chasse_gelee":REF,"Detectes":len(src),"Admis_apres_identite":len(ok),"Rejets_identite":len(rej),"Donnees_marche_OK":market_ok,"Donnees_marche_manquantes":market_missing}]).to_csv(D/"SYNTHESE_FILTRAGE_CHASSE_GELEE.csv",index=False)
print("detectes",len(src),"admis",len(ok),"rejets",len(rej),"marche_ok",market_ok,"manquantes",market_missing)

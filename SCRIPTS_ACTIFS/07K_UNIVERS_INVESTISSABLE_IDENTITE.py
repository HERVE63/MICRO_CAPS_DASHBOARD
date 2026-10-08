import pandas as pd
from pathlib import Path
D=Path("DONNEES")
src=pd.read_csv(D/"SORTIE_CHASSEUR_EXISTANT.csv",dtype=str).fillna("")
reg=pd.read_csv(D/"REGISTRE_IDENTITE_MICRO_CAPS.csv",dtype=str).fillna("")
# Le registre ne doit jamais bloquer une nouvelle cotation non encore connue.
r=reg[["Ticker","Exchange","Etat_registre"]].drop_duplicates(["Ticker","Exchange"],keep="last")
x=src.merge(r,on=["Ticker","Exchange"],how="left")
x["Etat_registre"]=x["Etat_registre"].replace("","NOUVEAU_A_QUALIFIER")
# Exclusion stricte des identites insuffisantes et des cotations secondaires deja reconnues.
bad=x.Etat_registre.eq("HORS_UNIVERS_IDENTITE_INSUFFISANTE") | x.Etat_registre.str.contains("SECONDAIRE",na=False)
ok=x[~bad].copy()
rej=x[bad].copy()
ok.to_csv(D/"UNIVERS_INVESTISSABLE_MICRO_CAPS.csv",index=False)
rej.to_csv(D/"EXCLUS_IDENTITE_MICRO_CAPS.csv",index=False)
pd.DataFrame([{"Univers_detecte":len(x),"Univers_investissable_identite":len(ok),"Exclus_identite":len(rej),"Nouveaux_a_qualifier":int((ok.Etat_registre=="NOUVEAU_A_QUALIFIER").sum())}]).to_csv(D/"SYNTHESE_UNIVERS_INVESTISSABLE.csv",index=False)
print("detecte",len(x),"investissable",len(ok),"exclus",len(rej),"nouveaux",int((ok.Etat_registre=="NOUVEAU_A_QUALIFIER").sum()))

# validation production

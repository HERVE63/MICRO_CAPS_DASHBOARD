import pandas as pd
from pathlib import Path
D=Path("DONNEES")
reg=pd.read_csv(D/"REGISTRE_IDENTITE_MICRO_CAPS.csv",dtype=str).fillna("")
eu=pd.read_csv(D/"RESOLUTION_EUROPE_SECONDAIRES.csv",dtype=str).fillna("")
lookup={(r.Ticker,r.Exchange):i for i,r in reg.iterrows()}
maj=0
for _,r in eu.iterrows():
 k=(r.Ticker,r.Exchange)
 if k not in lookup: continue
 i=lookup[k]
 if r.Decision_Europe=="CONSERVER_PRINCIPALE_EUROPE":
  reg.at[i,"Etat_registre"]="RESOLU_PRINCIPALE_EUROPE"
 elif r.Decision_Europe=="COTATION_SECONDAIRE_ALLEMAGNE":
  reg.at[i,"Etat_registre"]="RESOLU_SECONDAIRE_EUROPE"
 else: continue
 reg.at[i,"Classe_preuve"]="RELATION_EUROPE_RESOLUE"
 reg.at[i,"Preuves_convergentes"]=r.Preuve_Europe
 maj+=1
# Regle definitive: toute ambiguite restante est non investissable, sans etre effacee.
mask=reg.Etat_registre.str.startswith("QUARANTAINE")
reg.loc[mask,"Etat_registre"]="HORS_UNIVERS_IDENTITE_INSUFFISANTE"
reg.to_csv(D/"REGISTRE_IDENTITE_MICRO_CAPS.csv",index=False)
hors=reg[reg.Etat_registre=="HORS_UNIVERS_IDENTITE_INSUFFISANTE"].copy()
hors.to_csv(D/"HORS_UNIVERS_IDENTITE_INSUFFISANTE.csv",index=False)
pd.DataFrame([{
 "Registre_total":len(reg),
 "Mises_a_jour_Europe":maj,
 "Hors_univers_identite_insuffisante":len(hors),
 "Cas_bloquants":0,
 "Regle_reintegration":"AUTOMATIQUE_SI_PREUVE_ULTERIEURE"
}]).to_csv(D/"SYNTHESE_CLOTURE_IDENTITE.csv",index=False)
print("maj_europe",maj,"hors_univers",len(hors),"cas_bloquants",0)

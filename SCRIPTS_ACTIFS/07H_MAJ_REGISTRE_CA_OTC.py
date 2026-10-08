import pandas as pd
from pathlib import Path
D=Path("DONNEES")
reg=pd.read_csv(D/"REGISTRE_IDENTITE_MICRO_CAPS.csv",dtype=str).fillna("")
ca=pd.read_csv(D/"RESOLUTION_CANADA_OTC.csv",dtype=str).fillna("")
lookup={(r.Ticker,r.Exchange):i for i,r in reg.iterrows()}
n=0
for _,r in ca.iterrows():
 k=(r.Ticker,r.Exchange)
 if k not in lookup: continue
 i=lookup[k]
 if r.Decision_CA_OTC=="CONSERVER_PRINCIPALE_CANADA": reg.at[i,"Etat_registre"]="RESOLU_PRINCIPALE_CANADA"
 elif r.Decision_CA_OTC=="COTATION_SECONDAIRE_OTC": reg.at[i,"Etat_registre"]="RESOLU_SECONDAIRE_OTC"
 else: continue
 reg.at[i,"Classe_preuve"]="RELATION_CA_OTC_RESOLUE"
 reg.at[i,"Preuves_convergentes"]=r.Preuve_CA_OTC
 n+=1
reg.to_csv(D/"REGISTRE_IDENTITE_MICRO_CAPS.csv",index=False)
q=reg[reg.Etat_registre.str.startswith("QUARANTAINE")]
q.to_csv(D/"QUARANTAINE_IDENTITE_MICRO_CAPS.csv",index=False)
pd.DataFrame([{"Registre_total":len(reg),"Mises_a_jour_CA_OTC":n,"Principales_Canada":(reg.Etat_registre=="RESOLU_PRINCIPALE_CANADA").sum(),"Secondaires_OTC":(reg.Etat_registre=="RESOLU_SECONDAIRE_OTC").sum(),"Quarantaine_probable":(reg.Etat_registre=="QUARANTAINE_PROBABLE").sum(),"Quarantaine_non_resolue":(reg.Etat_registre=="QUARANTAINE_NON_RESOLUE").sum(),"Quarantaine_totale":len(q)}]).to_csv(D/"SYNTHESE_REGISTRE_APRES_CANADA_OTC.csv",index=False)
print("mises_a_jour",n,"quarantaine",len(q))

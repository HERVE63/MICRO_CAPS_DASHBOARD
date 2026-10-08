import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
D=Path("DONNEES")
src=D/"RESOLUTION_AMBIGUS_PAR_PREUVES.csv"
reg=D/"REGISTRE_IDENTITE_MICRO_CAPS.csv"
q=D/"QUARANTAINE_IDENTITE_MICRO_CAPS.csv"
df=pd.read_csv(src,dtype=str).fillna("")
now=datetime.now(timezone.utc).isoformat()
# Identifiant stable interne: ISIN si disponible, sinon ticker+place. Jamais le nom seul.
df["Cle_registre"]=df.apply(lambda r: ("ISIN:"+r["ISIN"] if r.get("ISIN","") not in ("","-") else "LISTING:"+r["Ticker"]+"@"+r["Exchange"]),axis=1)
df["Date_derniere_verification"]=now
df["Etat_registre"]=df["Classe_preuve"].map({"CERTAIN":"RESOLU_CERTAIN","DISTINCT":"RESOLU_DISTINCT","PROBABLE":"QUARANTAINE_PROBABLE","NON_RESOLU":"QUARANTAINE_NON_RESOLUE"}).fillna("QUARANTAINE_NON_RESOLUE")
cols=["Cle_registre","Ticker","Societe","Pays","Devise","Exchange","FullExchangeName","ISIN","Cle_nom","Classe_preuve","Preuves_convergentes","Etat_registre","Date_derniere_verification"]
new=df[cols].copy()
if reg.exists():
    old=pd.read_csv(reg,dtype=str).fillna("")
    allr=pd.concat([old,new],ignore_index=True)
    allr=allr.drop_duplicates("Cle_registre",keep="last")
else: allr=new
allr.to_csv(reg,index=False)
allr[allr.Etat_registre.str.startswith("QUARANTAINE")].to_csv(q,index=False)
pd.DataFrame([{
 "Registre_total":len(allr),
 "Resolus_certains":int((allr.Etat_registre=="RESOLU_CERTAIN").sum()),
 "Resolus_distincts":int((allr.Etat_registre=="RESOLU_DISTINCT").sum()),
 "Quarantaine_probable":int((allr.Etat_registre=="QUARANTAINE_PROBABLE").sum()),
 "Quarantaine_non_resolue":int((allr.Etat_registre=="QUARANTAINE_NON_RESOLUE").sum())
}]).to_csv(D/"SYNTHESE_REGISTRE_IDENTITE.csv",index=False)
print(pd.read_csv(D/"SYNTHESE_REGISTRE_IDENTITE.csv").to_string(index=False))

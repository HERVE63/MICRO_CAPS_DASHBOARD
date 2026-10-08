import pandas as pd,re
from pathlib import Path
D=Path("DONNEES"); q=pd.read_csv(D/"QUARANTAINE_IDENTITE_MICRO_CAPS.csv",dtype=str).fillna("")
q=q[q.Etat_registre=="QUARANTAINE_NON_RESOLUE"].copy()
secondary={"FRA","STU","DUS","MUN","HAM"}
primary={"PAR","STO","OSL","HEL","MCE","EBS","AMS","LSE","MIL","CPH","BRU","LIS","GER"}
def instrument_hint(t):
 t=t.upper()
 if re.search(r"(-P[A-Z0-9]*|[-.]P[ABCD]$)",t): return "PREFERENCE"
 return ""
rows=[]
for name,g in q.groupby("Cle_nom"):
 if len(g)<2: continue
 gp=g[g.Exchange.isin(primary)]; gs=g[g.Exchange.isin(secondary)]
 # Une seule place europeenne primaire + une ou plusieurs places allemandes secondaires.
 # Exclure tout groupe comportant un indice explicite de classe/instrument different.
 hints=[instrument_hint(x) for x in g.Ticker]
 if len(gp)==1 and len(gs)>=1 and not any(hints):
  pt=gp.iloc[0].Ticker
  for _,r in g.iterrows():
   z=r.to_dict()
   if r.Exchange in primary:
    z.update({"Decision_Europe":"CONSERVER_PRINCIPALE_EUROPE","Ticker_principal":pt,"Preuve_Europe":"NOM_NORMALISE+UNIQUE_PLACE_PRIMAIRE+PLACE_ALLEMANDE_SECONDAIRE"})
   elif r.Exchange in secondary:
    z.update({"Decision_Europe":"COTATION_SECONDAIRE_ALLEMAGNE","Ticker_principal":pt,"Preuve_Europe":"NOM_NORMALISE+UNIQUE_PLACE_PRIMAIRE+PLACE_ALLEMANDE_SECONDAIRE"})
   else: continue
   rows.append(z)
out=pd.DataFrame(rows)
out.to_csv(D/"RESOLUTION_EUROPE_SECONDAIRES.csv",index=False)
if len(out):
 sec=out[out.Decision_Europe=="COTATION_SECONDAIRE_ALLEMAGNE"]
 fam=sec.Cle_nom.nunique()
else: sec=out; fam=0
pd.DataFrame([{"Familles_Europe_resolues":fam,"Cotations_secondaires_allemandes":len(sec),"Suppressions_physiques":0}]).to_csv(D/"SYNTHESE_RESOLUTION_EUROPE.csv",index=False)
print("familles",fam,"secondaires",len(sec))

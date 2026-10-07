import pandas as pd, re
from pathlib import Path
D=Path("DONNEES")
src=D/"IDENTITE_COTATIONS_MULTIPLES.csv"
df=pd.read_csv(src,dtype=str).fillna("")
# Ce module ne supprime rien. Il classe uniquement les cas restes ambigus.
def root_ticker(t):
    t=t.upper().strip()
    return re.sub(r"\.(DE|F|DU|MU|HM|SG|BE|PA|AS|BR|MI|MC|LS|ST|OL|HE|CO|SW|L|TO|V|CN)$","",t)
df["Racine_ticker"]=df["Ticker"].map(root_ticker)
df["Classe_preuve"]="NON_RESOLU"
df["Preuves_convergentes"]=""
# ISIN commun = identite du titre certaine.
for isin,g in df[(df.ISIN!="") & (df.ISIN!="-")].groupby("ISIN"):
    if len(g)>1:
        df.loc[g.index,"Classe_preuve"]="CERTAIN"
        df.loc[g.index,"Preuves_convergentes"]="ISIN_COMMUN"
# Pour les autres: meme nom normalise + meme racine ticker sur plusieurs places = probable,
# jamais suffisant pour supprimer automatiquement.
for key,g in df.groupby("Cle_nom"):
    if len(g)<2: continue
    unresolved=g[df.loc[g.index,"Classe_preuve"]=="NON_RESOLU"]
    if len(unresolved)<2: continue
    for rt,h in unresolved.groupby(unresolved["Ticker"].map(root_ticker)):
        if rt and len(h)>1 and h["Exchange"].nunique()>1:
            df.loc[h.index,"Classe_preuve"]="PROBABLE"
            df.loc[h.index,"Preuves_convergentes"]="NOM_NORMALISE+RACINE_TICKER+PLACES_DISTINCTES"
# DISTINCT n'est attribue que si preuve positive de titres differents: deux ISIN valides differents.
for key,g in df.groupby("Cle_nom"):
    vals=sorted(set(x for x in g.ISIN if x not in ("","-")))
    if len(vals)>1:
        idx=g[g.ISIN.isin(vals)].index
        df.loc[idx,"Classe_preuve"]="DISTINCT"
        df.loc[idx,"Preuves_convergentes"]="ISIN_DIFFERENTS"
out=D/"RESOLUTION_AMBIGUS_PAR_PREUVES.csv"; df.to_csv(out,index=False)
s=df["Classe_preuve"].value_counts().reindex(["CERTAIN","PROBABLE","DISTINCT","NON_RESOLU"],fill_value=0)
pd.DataFrame([{"CERTAIN":int(s.CERTAIN),"PROBABLE":int(s.PROBABLE),"DISTINCT":int(s.DISTINCT),"NON_RESOLU":int(s.NON_RESOLU),"Suppressions_automatiques":0}]).to_csv(D/"SYNTHESE_RESOLUTION_AMBIGUS.csv",index=False)
print(s.to_string()); print("Aucune suppression automatique.")

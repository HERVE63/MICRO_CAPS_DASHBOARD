import pandas as pd
from pathlib import Path
D=Path("DONNEES")
src=D/"RESOLUTION_AMBIGUS_PAR_PREUVES.csv"
df=pd.read_csv(src,dtype=str).fillna("")
can={"VAN","TOR","CNQ","NEO"}; otc={"OQX","OQB","OID","PNK"}
rows=[]
for name,g in df.groupby("Cle_nom"):
    if not name or len(g)<2: continue
    gc=g[g["Exchange"].isin(can)]
    go=g[g["Exchange"].isin(otc)]
    if len(gc)==1 and len(go)>=1:
        # Meme nom normalise + une seule cotation canadienne + OTC: relation emetteur tres forte.
        # On ne confond jamais ce test avec un ISIN identique; la preuve reste auditable.
        primary=gc.iloc[0]
        for idx,r in g.iterrows():
            z=r.to_dict()
            if r["Exchange"] in can:
                z.update({"Decision_CA_OTC":"CONSERVER_PRINCIPALE_CANADA","Ticker_principal":primary["Ticker"],
                          "Preuve_CA_OTC":"NOM_NORMALISE+UNIQUE_CANADA+OTC"})
            elif r["Exchange"] in otc:
                z.update({"Decision_CA_OTC":"COTATION_SECONDAIRE_OTC","Ticker_principal":primary["Ticker"],
                          "Preuve_CA_OTC":"NOM_NORMALISE+UNIQUE_CANADA+OTC"})
            else:
                z.update({"Decision_CA_OTC":"HORS_REGLE","Ticker_principal":"","Preuve_CA_OTC":""})
            rows.append(z)
out=pd.DataFrame(rows)
out.to_csv(D/"RESOLUTION_CANADA_OTC.csv",index=False)
pairs=out[out.Decision_CA_OTC=="COTATION_SECONDAIRE_OTC"]
summary=pd.DataFrame([{
 "Familles_CA_OTC_resolues":int(pairs["Cle_nom"].nunique()),
 "Cotations_OTC_secondaires":len(pairs),
 "Cotations_canadiennes_principales":int((out.Decision_CA_OTC=="CONSERVER_PRINCIPALE_CANADA").sum()),
 "Suppressions_physiques":0
}])
summary.to_csv(D/"SYNTHESE_RESOLUTION_CANADA_OTC.csv",index=False)
print(summary.to_string(index=False))

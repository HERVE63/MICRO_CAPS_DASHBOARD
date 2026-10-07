# -*- coding: utf-8 -*-
"""Enrichissement d'identite des groupes multi-cotations.
Objectif: obtenir ISIN + pays de l'emetteur + place Yahoo, puis identifier la cotation
principale seulement quand la preuve est suffisante. Fail-closed: ambigu = conserve.
"""
from pathlib import Path
import pandas as pd, time
import yfinance as yf

BASE=Path(__file__).resolve().parent.parent
SRC=BASE/"DONNEES"/"RESOLUTION_COTATIONS_MULTIPLES.csv"
OUT=BASE/"DONNEES"/"IDENTITE_COTATIONS_MULTIPLES.csv"
SYN=BASE/"DONNEES"/"SYNTHESE_IDENTITE_COTATIONS.csv"
df=pd.read_csv(SRC).fillna("")

rows=[]
for i,r in df.iterrows():
    t=str(r["Ticker"]).strip()
    isin=""; issuer_country=""; currency_info=""; exchange_info=""; err=""
    try:
        tk=yf.Ticker(t)
        try: isin=(tk.isin or "").strip()
        except Exception as e: err+="ISIN:"+type(e).__name__+";"
        # L'identite ISIN est la preuve primaire. Les appels lourds tk.info ne sont
        # pas faits ici: pays/place proviennent deja du scan, et les cas ambigus
        # restent conserves (fail-closed).
    except Exception as e: err+="TICKER:"+type(e).__name__+";"
    z=r.to_dict()
    z.update({"ISIN":isin,"Pays_emetteur":issuer_country,"Devise_info":currency_info,
              "Exchange_info":exchange_info,"Erreur_enrichissement":err})
    rows.append(z)
    if (i+1)%100==0: print(f"Enrichissement {i+1}/{len(df)}")
res=pd.DataFrame(rows)

# Marches domestiques acceptes pour choisir la cotation principale.
dom={
"United States":["NMS","NGM","NCM","NYQ","ASE"],
"Canada":["TOR","VAN","CNQ","NEO"],
"France":["PAR","ENX"],"Germany":["GER","FRA"],"Sweden":["STO"],
"Norway":["OSL"],"Finland":["HEL"],"Denmark":["CPH"],"Italy":["MIL"],
"Spain":["MCE","MAD"],"Belgium":["BRU"],"Netherlands":["AMS"],
"Portugal":["LIS"],"Switzerland":["EBS"],"United Kingdom":["LSE","AQS"]
}
# preferences inside a domestic market; used only within a same-ISIN group.
rank={"NMS":1,"NGM":1,"NCM":1,"NYQ":1,"ASE":1,"TOR":1,"VAN":1,"CNQ":1,"NEO":1,
      "PAR":1,"ENX":1,"GER":1,"STO":1,"OSL":1,"HEL":1,"CPH":1,"MIL":1,"MCE":1,
      "MAD":1,"BRU":1,"AMS":1,"LIS":1,"EBS":1,"LSE":1,"AQS":2,"FRA":2,
      "PNK":9,"OQB":8,"OQX":7,"OID":8,"STU":8,"MUN":8,"DUS":8,"HAM":8}
res["Decision"]="CONSERVER_AMBIGU"
res["Motif_decision"]="IDENTITE_INSUFFISANTE"
res["Groupe_ISIN"]=""

for isin,g in res[res["ISIN"].astype(str).str.len().ge(10)].groupby("ISIN"):
    if len(g)<2: continue
    idx=list(g.index); res.loc[idx,"Groupe_ISIN"]=isin
    # Le champ Pays du scan designe la zone de cotation, pas necessairement
    # le domicile. On ne l'utilise donc pas pour prouver le pays de l'emetteur.
    # Choix principal uniquement si une seule place de rang institutionnel 1 existe.
    country=""
    allowed=[]
    cand=g.copy()
    cand["r"]=cand["Exchange"].map(rank).fillna(50)
    cand=cand[cand["r"].lt(7)].copy()
    if len(cand)==0:
        res.loc[idx,"Motif_decision"]="MEME_ISIN_SANS_PLACE_PRINCIPALE_IDENTIFIABLE"
        continue
    best=cand[cand["r"].eq(cand["r"].min())]
    if len(best)!=1:
        res.loc[idx,"Motif_decision"]="MEME_ISIN_PLUSIEURS_PLACES_PRINCIPALES_POSSIBLES"
        continue
    keep=best.index[0]
    res.loc[idx,"Decision"]="REJET_COTATION_SECONDAIRE"
    res.loc[idx,"Motif_decision"]="MEME_ISIN_PLACE_SECONDAIRE"
    res.loc[keep,"Decision"]="CONSERVER_PRINCIPALE"
    res.loc[keep,"Motif_decision"]="MEME_ISIN_PLACE_PRINCIPALE_SELON_HIERARCHIE_FIGEE"

res.to_csv(OUT,index=False)
syn=pd.DataFrame([{
"Lignes_enrichies":len(res),
"Lignes_avec_ISIN":int(res["ISIN"].astype(str).str.len().ge(10).sum()),
"Groupes_ISIN_multi":int(res.loc[res["Groupe_ISIN"].ne(""),"Groupe_ISIN"].nunique()),
"Cotations_principales_identifiees":int((res["Decision"]=="CONSERVER_PRINCIPALE").sum()),
"Cotations_secondaires_identifiees":int((res["Decision"]=="REJET_COTATION_SECONDAIRE").sum()),
"Lignes_encore_ambigues":int((res["Decision"]=="CONSERVER_AMBIGU").sum())
}])
syn.to_csv(SYN,index=False)
print(syn.to_string(index=False))

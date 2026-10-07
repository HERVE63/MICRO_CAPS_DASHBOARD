# -*- coding: utf-8 -*-
"""Audit déterministe des cotations multiples MICRO CAPS.
Aucune suppression: classe les groupes de noms répétés et prépare les preuves.
"""
from pathlib import Path
import pandas as pd, re, unicodedata
BASE=Path(__file__).resolve().parent.parent
SRC=BASE/"DONNEES"/"UNIVERS_ACTIONS_MICRO_CAPS_ETAPE1.csv"
OUT=BASE/"DONNEES"/"RESOLUTION_COTATIONS_MULTIPLES.csv"
SUM=BASE/"DONNEES"/"SYNTHESE_COTATIONS_MULTIPLES.csv"

def norm(s):
    s=unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().upper()
    s=re.sub(r"[^A-Z0-9]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

df=pd.read_csv(SRC)
need=["Ticker","Societe","Pays","Devise","Exchange","FullExchangeName","QuoteType","UnderlyingSymbol"]
for c in need:
    if c not in df.columns: raise RuntimeError(f"Colonne manquante: {c}")
    df[c]=df[c].fillna("").astype(str).str.strip()
df["Cle_nom"]=df["Societe"].map(norm)
multi=df[df["Cle_nom"].ne("") & df.duplicated("Cle_nom",keep=False)].copy()
multi["Nb_lignes_groupe"]=multi.groupby("Cle_nom")["Ticker"].transform("size")
multi["Nb_pays_groupe"]=multi.groupby("Cle_nom")["Pays"].transform("nunique")
multi["Nb_places_groupe"]=multi.groupby("Cle_nom")["Exchange"].transform("nunique")
multi["Nb_devises_groupe"]=multi.groupby("Cle_nom")["Devise"].transform("nunique")
multi["Preuve_identifiant_stable"]="ABSENTE"
u=multi["UnderlyingSymbol"].str.strip()
has=u.ne("")
cnt=multi[has].groupby("Cle_nom")["UnderlyingSymbol"].transform("nunique")
multi.loc[has & cnt.eq(1),"Preuve_identifiant_stable"]="UNDERLYING_SYMBOL_COMMUN"
multi["Statut_resolution"]="PROBABLE_A_VERIFIER"
multi.loc[multi["Preuve_identifiant_stable"].eq("UNDERLYING_SYMBOL_COMMUN"),"Statut_resolution"]="IDENTITE_RENFORCEE_MAIS_PLACE_PRINCIPALE_A_DETERMINER"
cols=need+["Cle_nom","Nb_lignes_groupe","Nb_pays_groupe","Nb_places_groupe","Nb_devises_groupe","Preuve_identifiant_stable","Statut_resolution"]
multi[cols].sort_values(["Cle_nom","Ticker"]).to_csv(OUT,index=False)
s=pd.DataFrame([{
 "Lignes_suspectes":len(multi),
 "Groupes_suspects":multi["Cle_nom"].nunique(),
 "Groupes_avec_identifiant_stable":multi.loc[multi["Preuve_identifiant_stable"].eq("UNDERLYING_SYMBOL_COMMUN"),"Cle_nom"].nunique(),
 "Groupes_sans_identifiant_stable":multi.loc[multi["Preuve_identifiant_stable"].eq("ABSENTE"),"Cle_nom"].nunique(),
 "Suppressions_autorisees":0
}])
s.to_csv(SUM,index=False)
print(s.to_string(index=False))
print("Aucune cotation supprimee par cet audit.")

# -*- coding: utf-8 -*-
"""Premier filtrage objectif MICRO CAPS.
Ne supprime que les instruments explicitement non-actions.
Les places OTC/Francfort ne sont jamais exclues par leur seul nom.
Les doublons de nom sont signalés pour résolution ultérieure, sans choix arbitraire.
"""
from pathlib import Path
import pandas as pd
BASE=Path(__file__).resolve().parent.parent
SRC=BASE/"DONNEES"/"SORTIE_CHASSEUR_EXISTANT.csv"
OK=BASE/"DONNEES"/"UNIVERS_ACTIONS_MICRO_CAPS_ETAPE1.csv"
REJ=BASE/"DONNEES"/"REJETS_PRESELECTION_MICRO_CAPS.csv"
AMB=BASE/"DONNEES"/"COTATIONS_MULTIPLES_A_VERIFIER.csv"
df=pd.read_csv(SRC)
for c in ["Ticker","Societe","QuoteType","Exchange","FullExchangeName","Pays"]:
    if c not in df.columns: raise RuntimeError(f"Colonne manquante: {c}")
    df[c]=df[c].fillna("").astype(str).str.strip()
df["Motif_rejet"]=""
non_actions=df["QuoteType"].ne("EQUITY")
df.loc[non_actions,"Motif_rejet"]="INSTRUMENT_NON_ACTION:"+df.loc[non_actions,"QuoteType"]
rej=df[non_actions].copy()
ok=df[~non_actions].copy()
# Les noms répétés indiquent des cotations potentiellement multiples; aucune fusion automatique ici.
dup=ok[ok.duplicated("Societe",keep=False) & ok["Societe"].ne("")].copy()
dup["Statut_resolution"]="A_VERIFIER_COTATIONS_MULTIPLES"
ok.to_csv(OK,index=False)
rej.to_csv(REJ,index=False)
dup.to_csv(AMB,index=False)
print(f"Filtrage etape 1: entree={len(df)}; actions={len(ok)}; rejets_non_actions={len(rej)}; lignes_cotations_multiples_a_verifier={len(dup)}.")
print("REJETS_PAR_TYPE")
print(rej["QuoteType"].value_counts(dropna=False).to_string())

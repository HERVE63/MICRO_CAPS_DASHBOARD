# -*- coding: utf-8 -*-
"""Audit reproductible des listings du scan courant. Aucun candidat n'est exclu."""
from pathlib import Path
import pandas as pd
BASE=Path(__file__).resolve().parent.parent
SRC=BASE/"DONNEES"/"SORTIE_CHASSEUR_EXISTANT.csv"
OUT=BASE/"DONNEES"/"AUDIT_LISTINGS_MICRO_CAPS.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)
df=pd.read_csv(SRC)
req=["Ticker","Societe","Pays","Exchange","FullExchangeName","QuoteType"]
miss=[c for c in req if c not in df.columns]
if miss: raise RuntimeError(f"Colonnes manquantes: {miss}")
for c in req: df[c]=df[c].fillna("").astype(str).str.strip()
audit=(df.groupby(["Pays","Exchange","FullExchangeName","QuoteType"],dropna=False).size().reset_index(name="Nb_lignes").sort_values(["Nb_lignes","Pays"],ascending=[False,True]))
audit.to_csv(OUT,index=False)
print(f"Audit listings: {len(df)} lignes; {df['Ticker'].nunique()} tickers; {df['Societe'].nunique()} noms de societes.")
print("TOP_PLACES")
print(df.groupby(["Exchange","FullExchangeName"]).size().sort_values(ascending=False).head(25).to_string())
print("QUOTE_TYPES")
print(df["QuoteType"].value_counts(dropna=False).to_string())

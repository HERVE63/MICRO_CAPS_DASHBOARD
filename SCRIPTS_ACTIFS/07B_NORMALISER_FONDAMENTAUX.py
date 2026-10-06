from pathlib import Path
import pandas as pd

BASE=Path(__file__).resolve().parent.parent
RAW=BASE/"DONNEES"/"FONDAMENTAUX_COLLECTES.csv"
OUT=BASE/"DONNEES"/"UNIVERS_SCREENER_BRUT.csv"
AUDIT=BASE/"DONNEES"/"AUDIT_FONDAMENTAUX.csv"

COLS=[
"Date_scan","Societe","Ticker","Devise","Pays","Capitalisation","CA_TTM",
"Croissance_CA","Marge_brute","EBITDA_EBIT","FCF","Cash","Dette_nette",
"Dilution_3a","Insiders_pct","Valeur_insiders","Liquidite",
"Source_fondamentaux","Date_source"
]
NUM=[
"Capitalisation","CA_TTM","Croissance_CA","Marge_brute","EBITDA_EBIT",
"FCF","Cash","Dette_nette","Dilution_3a","Insiders_pct",
"Valeur_insiders","Liquidite"
]

def executer():
    if not RAW.exists():
        raise RuntimeError("Collecte fondamentale absente.")
    df=pd.read_csv(RAW)
    missing=[c for c in COLS if c not in df.columns]
    if missing:
        raise RuntimeError("Champs fondamentaux absents: "+", ".join(missing))
    if df.empty:
        raise RuntimeError("Collecte fondamentale vide.")

    df=df[COLS].copy()
    for c in NUM:
        df[c]=pd.to_numeric(df[c],errors="coerce")

    essentiels=[
        "Date_scan","Societe","Ticker","Devise","Pays",
        "Capitalisation","CA_TTM","Cash","Dette_nette","Liquidite",
        "Source_fondamentaux","Date_source"
    ]
    complet=df[essentiels].notna().all(axis=1)
    source_non_vide=df["Source_fondamentaux"].astype(str).str.strip().ne("")
    date_ok=pd.to_datetime(df["Date_source"],errors="coerce").notna()
    df["Statut_donnees"]="INCOMPLET"
    df.loc[complet & source_non_vide & date_ok,"Statut_donnees"]="OK"

    # Les champs non essentiels restent visibles comme manquants:
    # ils seront traites par SSI/MCPA, jamais imputes arbitrairement.
    df.to_csv(OUT,index=False)
    pd.DataFrame([{
        "Nb_collectes":len(df),
        "Nb_OK":int((df["Statut_donnees"]=="OK").sum()),
        "Nb_incomplets":int((df["Statut_donnees"]!="OK").sum())
    }]).to_csv(AUDIT,index=False)
    print("Fondamentaux controles :",len(df))
    print("Eligibles au screener :",int((df["Statut_donnees"]=="OK").sum()))
    return df

if __name__=="__main__":
    executer()

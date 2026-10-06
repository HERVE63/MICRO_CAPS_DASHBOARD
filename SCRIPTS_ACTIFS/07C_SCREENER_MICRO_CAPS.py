from pathlib import Path
import pandas as pd

BASE=Path(__file__).resolve().parent.parent
ENTREE=BASE/"DONNEES"/"UNIVERS_SCREENER_BRUT.csv"
SORTIE=BASE/"DONNEES"/"SORTIE_SCREENER_CANDIDATS.csv"
AUDIT=BASE/"DONNEES"/"AUDIT_SCREENER_MICRO_CAPS.csv"

REQUIS=[
"Date_scan","Societe","Ticker","Devise","Pays","Capitalisation","CA_TTM",
"Croissance_CA","Marge_brute","EBITDA_EBIT","FCF","Cash","Dette_nette",
"Dilution_3a","Insiders_pct","Valeur_insiders","Liquidite",
"Source_fondamentaux","Date_source","Statut_donnees"
]

def executer():
    if not ENTREE.exists():
        raise RuntimeError("Univers screener brut absent.")
    df=pd.read_csv(ENTREE)
    manque=[c for c in REQUIS if c not in df.columns]
    if manque:
        raise RuntimeError("Colonnes screener absentes: "+", ".join(manque))
    if df.empty:
        raise RuntimeError("Univers screener vide: aucune chasse possible.")

    # Le sas historique exige des donnees accessibles et une entreprise investissable.
    # Aucun seuil financier non archive n'est reconstruit ici.
    valides=df[df["Statut_donnees"].astype(str).str.upper().eq("OK")].copy()
    valides=valides.dropna(subset=[
        "Societe","Ticker","Devise","Pays","Source_fondamentaux","Date_source"
    ])
    if valides.empty:
        raise RuntimeError("Aucun candidat avec donnees completes et sourcees.")

    out=pd.DataFrame({
        "Date_detection":valides["Date_scan"],
        "Societe":valides["Societe"],
        "Ticker":valides["Ticker"],
        "Devise":valides["Devise"],
        "Pays":valides["Pays"],
        "Source_detection":valides["Source_fondamentaux"],
        "Date_source":valides["Date_source"],
        "These_initiale":"A EVALUER PAR SSI - aucune note automatique inventee",
        "Statut_chasse":"A_EVALUER_SSI"
    })
    out=out.drop_duplicates(subset=["Ticker"],keep="first")
    out.to_csv(SORTIE,index=False)

    pd.DataFrame([{
        "Nb_univers":len(df),"Nb_donnees_OK":len(valides),
        "Nb_transmis_SSI":len(out),
        "Regle":"pas de seuil financier reconstruit sans archive"
    }]).to_csv(AUDIT,index=False)
    print(f"Screener: {len(df)} -> {len(out)} candidat(s) transmis au SSI.")
    return out

if __name__=="__main__":
    executer()

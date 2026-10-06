from pathlib import Path
import pandas as pd

BASE=Path(__file__).resolve().parent.parent
ENTREE=BASE/"DONNEES"/"UNIVERS_SCREENER_BRUT.csv"
SORTIE=BASE/"DONNEES"/"SORTIE_SCREENER_CANDIDATS.csv"
AUDIT=BASE/"DONNEES"/"AUDIT_SCREENER_MICRO_CAPS.csv"
PARAM=BASE/"CONFIG"/"PARAMETRES_SCE_MICRO_CAPS.csv"

REQUIS=["Date_scan","Societe","Ticker","Devise","Pays","Capitalisation","CA_TTM",
"Croissance_CA","Marge_brute","EBITDA_EBIT","FCF","Cash","Dette_nette",
"Dilution_3a","Insiders_pct","Valeur_insiders","Liquidite",
"Source_fondamentaux","Date_source","Statut_donnees"]

def executer():
    if not ENTREE.exists(): raise RuntimeError("Univers screener brut absent.")
    if not PARAM.exists(): raise RuntimeError("Parametres SCE Micro Caps absents.")
    df=pd.read_csv(ENTREE)
    manque=[x for x in REQUIS if x not in df.columns]
    if manque: raise RuntimeError("Colonnes screener absentes: "+", ".join(manque))
    if df.empty: raise RuntimeError("Univers screener vide: aucune chasse possible.")
    p=pd.read_csv(PARAM)
    try:
        cap_min=float(p.loc[p["Parametre"]=="Capitalisation_min","Valeur"].iloc[0])*1_000_000
        cap_max=float(p.loc[p["Parametre"]=="Capitalisation_max","Valeur"].iloc[0])*1_000_000
    except Exception as e:
        raise RuntimeError("Parametres capitalisation invalides.") from e
    if cap_min!=50_000_000 or cap_max!=300_000_000:
        raise RuntimeError("Fenetre Micro Caps non validee: attendu 50-300 MEUR.")
    cap=pd.to_numeric(df["Capitalisation"],errors="coerce")
    valides=df[df["Statut_donnees"].astype(str).str.upper().eq("OK") & cap.ge(cap_min) & cap.le(cap_max)].copy()
    valides=valides.dropna(subset=["Societe","Ticker","Devise","Pays","Source_fondamentaux","Date_source"])
    if valides.empty: raise RuntimeError("Aucun candidat source dans la fenetre 50-300 MEUR.")
    out=pd.DataFrame({"Date_detection":valides["Date_scan"],"Societe":valides["Societe"],
    "Ticker":valides["Ticker"],"Devise":valides["Devise"],"Pays":valides["Pays"],
    "Source_detection":valides["Source_fondamentaux"],"Date_source":valides["Date_source"],
    "These_initiale":"A EVALUER PAR SSI - aucune note automatique inventee","Statut_chasse":"A_EVALUER_SSI"})
    out=out.drop_duplicates(subset=["Ticker"],keep="first")
    out.to_csv(SORTIE,index=False)
    pd.DataFrame([{"Nb_univers":len(df),"Nb_donnees_OK_50_300":len(valides),"Nb_transmis_SSI":len(out),
    "Regle":"Adaptation Micro Caps uniquement: capitalisation 50-300 MEUR"}]).to_csv(AUDIT,index=False)
    print(f"Screener Micro Caps: {len(df)} -> {len(out)} candidat(s) 50-300 MEUR.")
    return out

if __name__=="__main__": executer()

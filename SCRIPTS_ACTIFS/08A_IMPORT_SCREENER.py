from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
ENTREE = BASE / "DONNEES" / "SORTIE_SCREENER_CANDIDATS.csv"
CHASSE = BASE / "DONNEES" / "CHASSE_CANDIDATS.csv"
CONTROLE = BASE / "DONNEES" / "CONTROLE_IMPORT_SCREENER.csv"

REQUIS = [
    "Date_detection","Societe","Ticker","Devise","Pays",
    "Source_detection","Date_source","These_initiale","Statut_chasse"
]

def executer():
    if not ENTREE.exists():
        raise RuntimeError(
            "Sortie screener absente. Import bloque: aucune reconstruction implicite."
        )
    src = pd.read_csv(ENTREE)
    absents = [c for c in REQUIS if c not in src.columns]
    if absents:
        raise RuntimeError("Sortie screener incomplete : " + ", ".join(absents))
    if src.empty:
        raise RuntimeError("Sortie screener vide.")

    erreurs = []
    for i, r in src.iterrows():
        for c in REQUIS:
            if pd.isna(r[c]) or str(r[c]).strip() == "":
                erreurs.append(f"Ligne {i+1}: {c} manquant")
    if erreurs:
        raise RuntimeError("Import screener bloque : " + " | ".join(erreurs[:20]))

    ancien = pd.read_csv(CHASSE) if CHASSE.exists() else pd.DataFrame(columns=REQUIS)
    tout = pd.concat([ancien, src[REQUIS]], ignore_index=True)
    tout = tout.drop_duplicates(subset=["Ticker","Date_detection"], keep="first")
    tout.to_csv(CHASSE, index=False)

    pd.DataFrame([{
        "Nb_entree": len(src),
        "Nb_registre_apres_import": len(tout),
        "Statut": "OK"
    }]).to_csv(CONTROLE, index=False)
    print(f"Import screener : {len(src)} candidat(s); registre : {len(tout)}.")
    return tout

if __name__ == "__main__":
    executer()

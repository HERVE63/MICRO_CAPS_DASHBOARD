from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
ENTREE_NETTOYEE = BASE / "DONNEES" / "UNIVERS_INVESTISSABLE_MICRO_CAPS.csv"
ENTREE_BRUTE = BASE / "DONNEES" / "SORTIE_CHASSEUR_EXISTANT.csv"
PARAMS = BASE / "CONFIG" / "PARAMETRES_SCE_MICRO_CAPS.csv"
SORTIE = BASE / "DONNEES" / "SORTIE_SCREENER_CANDIDATS.csv"
CONTROLE = BASE / "DONNEES" / "CONTROLE_ADAPTATEUR_CHASSEUR_MICRO_CAPS.csv"

REQUIS = [
    "Date_detection","Societe","Ticker","Devise","Pays","Capitalisation_EUR",
    "Source_detection","Date_source","These_initiale","Statut_chasse"
]

def _parametres_capitalisation():
    if not PARAMS.exists():
        raise RuntimeError("Parametres Micro Caps absents.")
    p = pd.read_csv(PARAMS)
    if set(["Parametre","Valeur","Unite","Portee","Statut"]) - set(p.columns):
        raise RuntimeError("Schema PARAMETRES_SCE_MICRO_CAPS invalide.")
    q = p.set_index("Parametre")
    for nom in ("Capitalisation_min","Capitalisation_max"):
        if nom not in q.index:
            raise RuntimeError(f"Parametre absent : {nom}")
        r = q.loc[nom]
        if str(r["Unite"]).strip().upper() != "MEUR" or str(r["Portee"]).strip() != "MICRO_CAPS" or str(r["Statut"]).strip() != "VALIDE":
            raise RuntimeError(f"Parametre non valide : {nom}")
    mini = float(q.loc["Capitalisation_min","Valeur"]) * 1_000_000
    maxi = float(q.loc["Capitalisation_max","Valeur"]) * 1_000_000
    if mini <= 0 or maxi <= mini:
        raise RuntimeError("Bornes de capitalisation incoherentes.")
    return mini, maxi

def executer():
    ENTREE = ENTREE_NETTOYEE
    if not ENTREE.exists():
        raise RuntimeError("Sortie du chasseur existant absente.")
    src = pd.read_csv(ENTREE)
    absents = [c for c in REQUIS if c not in src.columns]
    if absents:
        raise RuntimeError("Sortie chasseur incomplete : " + ", ".join(absents))
    if src.empty:
        raise RuntimeError("Sortie du chasseur existant vide.")

    erreurs = []
    for i, r in src.iterrows():
        for c in REQUIS:
            if pd.isna(r[c]) or str(r[c]).strip() == "":
                erreurs.append(f"Ligne {i+1}: {c} manquant")
    if erreurs:
        raise RuntimeError("Adaptateur bloque : " + " | ".join(erreurs[:20]))

    cap = pd.to_numeric(src["Capitalisation_EUR"], errors="coerce")
    if cap.isna().any() or (cap <= 0).any():
        raise RuntimeError("Capitalisation_EUR absente, non numerique ou <= 0.")

    mini, maxi = _parametres_capitalisation()
    masque = cap.between(mini, maxi, inclusive="both")
    eligibles = src.loc[masque].copy()

    if eligibles.empty:
        raise RuntimeError("Aucun candidat du chasseur dans la fenetre Micro Caps 50-300 MEUR.")

    colonnes_sortie = [
        "Date_detection","Societe","Ticker","Devise","Pays",
        "Source_detection","Date_source","These_initiale","Statut_chasse"
    ]
    eligibles[colonnes_sortie].to_csv(SORTIE, index=False)

    pd.DataFrame([{
        "Nb_chasseur": len(src),
        "Nb_eligibles_50_300_MEUR": len(eligibles),
        "Capitalisation_min_EUR": mini,
        "Capitalisation_max_EUR": maxi,
        "Statut": "OK"
    }]).to_csv(CONTROLE, index=False)

    print(f"Adaptateur chasseur : {len(eligibles)}/{len(src)} candidat(s) dans 50-300 MEUR.")
    return eligibles

if __name__ == "__main__":
    executer()

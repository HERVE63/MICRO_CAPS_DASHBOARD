from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
CHASSE = BASE / "DONNEES" / "CHASSE_CANDIDATS.csv"
REVUE = BASE / "DONNEES" / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv"
OUTPUT = BASE / "DONNEES" / "CONTROLE_CHASSE_SSI.csv"

CHAMPS = [
    "Date_detection","Societe","Ticker","Devise","Pays",
    "Source_detection","Date_source","These_initiale","Statut_chasse"
]

def executer():
    if not CHASSE.exists():
        raise RuntimeError("Registre de chasse absent.")
    chasse = pd.read_csv(CHASSE)
    absents = [c for c in CHAMPS if c not in chasse.columns]
    if absents:
        raise RuntimeError("Colonnes chasse absentes : " + ", ".join(absents))

    erreurs = []
    if len(chasse):
        if chasse.duplicated(subset=["Ticker","Date_detection"]).any():
            erreurs.append("Doublon ticker/date dans la chasse.")
        for i, r in chasse.iterrows():
            for c in CHAMPS:
                if pd.isna(r[c]) or str(r[c]).strip() == "":
                    erreurs.append(f"Ligne {i+1}: {c} manquant.")

    revue = pd.read_csv(REVUE) if REVUE.exists() else pd.DataFrame()
    challengers = (
        revue[revue["Type"].astype(str).str.upper().eq("CHALLENGER")]
        if len(revue) and "Type" in revue.columns else pd.DataFrame()
    )

    # Aucun challenger ne peut entrer dans le comité sans trace de chasse.
    if len(challengers):
        tickers_chasse = set(chasse["Ticker"].astype(str).str.upper().str.strip())
        for _, r in challengers.iterrows():
            t = str(r["Ticker"]).upper().strip()
            if t not in tickers_chasse:
                erreurs.append(f"Challenger {t} absent du registre de chasse.")
            try:
                if float(r["SSI"]) < 65:
                    erreurs.append(f"Challenger {t}: SSI < 65, non admissible.")
            except Exception:
                erreurs.append(f"Challenger {t}: SSI invalide.")

    out = pd.DataFrame([{
        "Nb_candidats_chasse": len(chasse),
        "Nb_challengers_revue": len(challengers),
        "Statut": "OK" if not erreurs else "BLOQUE",
        "Nb_erreurs": len(erreurs),
        "Erreurs": " | ".join(erreurs)
    }])
    out.to_csv(OUTPUT, index=False)
    if erreurs:
        raise RuntimeError("Chasse/SSI bloquee : " + " | ".join(erreurs[:20]))
    print(f"Chasse controlee : {len(chasse)} candidat(s).")
    print(f"Challengers admis en revue : {len(challengers)}.")
    return out

if __name__ == "__main__":
    executer()

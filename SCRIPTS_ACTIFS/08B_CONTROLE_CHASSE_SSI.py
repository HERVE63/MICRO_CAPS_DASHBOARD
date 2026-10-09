from pathlib import Path
import pandas as pd
import importlib.util
from tempfile import TemporaryDirectory

BASE = Path(__file__).resolve().parent.parent
CHASSE = BASE / "DONNEES" / "CHASSE_CANDIDATS.csv"
REVUE = BASE / "DONNEES" / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv"
OUTPUT = BASE / "DONNEES" / "CONTROLE_CHASSE_SSI.csv"
RESULTATS = BASE / "DONNEES" / "RESULTATS_SSI.csv"

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
        if not RESULTATS.exists():
            erreurs.append("Resultats SSI documentes absents : challengers interdits.")
            resultats = pd.DataFrame()
        else:
            resultats = pd.read_csv(RESULTATS, dtype=str, keep_default_na=False)
            requis = {"Ticker","SSI","Statut_SSI"}
            if not requis.issubset(resultats.columns) or resultats["Ticker"].duplicated().any():
                erreurs.append("Registre SSI invalide ou tickers dupliques.")
                resultats = pd.DataFrame()
        # Revalidation sur les preuves actuelles : un CSV RESULTATS_SSI édité ne suffit pas.
        if len(resultats):
            spec=importlib.util.spec_from_file_location("validation_ssi_comite",BASE/"SCRIPTS_ACTIFS/07R_VALIDER_NOTES_SSI.py")
            m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            try:
                with TemporaryDirectory() as tmp:
                    m.OUT=Path(tmp)/"RESULTATS_SSI.csv";m.AUD=Path(tmp)/"AUDIT_SSI.csv"
                    actuel=m.executer().set_index("Ticker")
                for _,rssi in resultats[resultats.Statut_SSI.eq("ADMIS_SSI")].iterrows():
                    if rssi.Ticker not in actuel.index or actuel.loc[rssi.Ticker,"Statut_SSI"]!="ADMIS_SSI" or str(actuel.loc[rssi.Ticker,"SSI"])!=str(rssi.SSI):
                        erreurs.append("Admission SSI périmée/non vérifiée : "+rssi.Ticker)
            except Exception as exc:
                erreurs.append("Revalidation des preuves SSI bloquée : "+str(exc))
        admis = resultats.set_index("Ticker") if len(resultats) else pd.DataFrame()
        tickers_chasse = set(chasse["Ticker"].astype(str).str.upper().str.strip())
        for _, r in challengers.iterrows():
            t = str(r["Ticker"]).upper().strip()
            if t not in tickers_chasse:
                erreurs.append(f"Challenger {t} absent du registre de chasse.")
            if len(admis) == 0 or t not in admis.index:
                erreurs.append(f"Challenger {t}: absence de resultat SSI officiel.")
            else:
                s = admis.loc[t]
                if s["Statut_SSI"] != "ADMIS_SSI":
                    erreurs.append(f"Challenger {t}: non admis au registre SSI.")
                try:
                    if float(s["SSI"]) < 65 or abs(float(s["SSI"])-float(r["SSI"])) > 0.001:
                        erreurs.append(f"Challenger {t}: SSI divergent du registre officiel.")
                except (ValueError, TypeError):
                    erreurs.append(f"Challenger {t}: SSI officiel invalide.")
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

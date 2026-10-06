from pathlib import Path
import importlib.util
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SCRIPT = BASE / "SCRIPTS_ACTIFS" / "09_CONTROLE_REVUE_MCPA_IPS.py"
OUTPUT = BASE / "DONNEES" / "DUELS_PROCHAIN_EURO.csv"

def executer():
    spec = importlib.util.spec_from_file_location("controle_revue", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    df = module.executer().copy()

    titulaires = df[df["Type"].astype(str).str.upper() == "TITULAIRE"]
    challengers = df[df["Type"].astype(str).str.upper() == "CHALLENGER"]
    if titulaires.empty or challengers.empty:
        raise RuntimeError("Titulaires et challengers sont requis.")

    candidats = titulaires[
        titulaires["Decision"].astype(str).str.upper().isin(
            ["VENDRE", "ALLEGER", "ALLÉGER"]
        )
    ]

    rows = []
    for _, row in candidats.iterrows():
        comparaison = str(row["Challengers_compares"]).strip()
        if comparaison == "":
            raise RuntimeError("Comparaison challenger manquante.")
        rows.append({
            "ID_position_source": row["ID_position"],
            "Societe_source": row["Societe"],
            "Decision_source": row["Decision"],
            "MCPA_source": row["MCPA"],
            "IC_source": row["IC"],
            "CX_source": row["CX"],
            "Delta_source": row["Delta"],
            "Challengers_compares": comparaison,
            "Statut_duel": "A_VALIDER_AVANT_JOURNAL"
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT, index=False)
    print("Duels documentes :", len(out))
    print("Journal non modifie.")
    return out

if __name__ == "__main__":
    executer()

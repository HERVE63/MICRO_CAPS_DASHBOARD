from pathlib import Path
import importlib.util
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "SCRIPTS_ACTIFS"

def charger(nom):
    path = SRC / nom
    spec = importlib.util.spec_from_file_location(nom.replace(".py",""), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def executer():
    # Ordre obligatoire : screener, provenance/admissibilite, analyse, duel.\n    charger("07B_NORMALISER_FONDAMENTAUX.py").executer()\n    charger("07C_SCREENER_MICRO_CAPS.py").executer()\n    charger("08A_IMPORT_SCREENER.py").executer()\n    charger("08B_CONTROLE_CHASSE_SSI.py").executer()
    revue = charger("09_CONTROLE_REVUE_MCPA_IPS.py").executer()
    duels = charger("09B_DUEL_PROCHAIN_EURO.py").executer()

    synthese = pd.DataFrame([{
        "Nb_analyses": len(revue),
        "Nb_duels_sortants": len(duels),
        "Statut": "PRET_POUR_VALIDATION_HUMAINE",
        "Journal_modifie": "NON"
    }])
    out = BASE / "DONNEES" / "SYNTHESE_COMITE_HEBDOMADAIRE.csv"
    synthese.to_csv(out, index=False)
    print("Comite hebdomadaire controle.")
    print("Journal non modifie : validation humaine requise.")
    return synthese

if __name__ == "__main__":
    executer()

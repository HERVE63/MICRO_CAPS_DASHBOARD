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
    # Chaîne hebdomadaire MICRO CAPS.
    #
    # La découverte amont n'est PAS recalculée ici :
    # 08A importe la sortie du chasseur existant déposée dans
    # DONNEES/SORTIE_SCREENER_CANDIDATS.csv.
    #
    # Le comité applique ensuite les contrôles propres à MICRO CAPS :
    # provenance/admissibilité + SSI, revue MCPA/IPS, puis duel du prochain euro.
    # Les anciens modules expérimentaux 07B/07C ne font pas partie de ce chemin.
    charger("08A_IMPORT_SCREENER.py").executer()
    charger("08B_CONTROLE_CHASSE_SSI.py").executer()
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

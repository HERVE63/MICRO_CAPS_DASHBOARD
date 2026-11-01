"""09B : aucune allocation vers une destination non confrontee.

Fixtures entierement fictives. Test de la fonction pure : aucune collecte,
aucune note attribuee et aucune modification du journal virtuel/officiel.
"""
from pathlib import Path
import importlib.util

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "duel_exhaustif", ROOT / "SCRIPTS_ACTIFS/09B_DUEL_PROCHAIN_EURO.py")
DUEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DUEL)


def ligne(typ, ident, note, decision, compares="AUCUNE"):
    return {
        "Type": typ, "ID_position": ident, "Societe": "FICTION_" + ident,
        "MCPA": note, "Decision": decision, "Challengers_compares": compares,
    }


def refuser(rows, message):
    try:
        DUEL.calculer_duels(pd.DataFrame(rows))
    except RuntimeError as erreur:
        assert message.lower() in str(erreur).lower(), str(erreur)
        return
    raise AssertionError("09B a accepte une comparaison incomplete/invalide")


def test():
    source = ligne("TITULAIRE", "T1", 70, "VENDRE", "T2|C1")
    titulaire = ligne("TITULAIRE", "T2", 90, "RENFORCER")
    challenger = ligne("CHALLENGER", "C1", 95, "SONDE")
    valide = DUEL.calculer_duels(pd.DataFrame([source, titulaire, challenger]))
    assert len(valide) == 1
    assert valide.iloc[0]["ID_position_destination"] == "C1"
    assert valide.iloc[0]["Statut_duel"] == "ALLOCATION_DETERMINEE"

    # Un challenger mieux note mais non compare ne doit jamais recevoir
    # un euro sur la seule base d'une liste de revue partielle.
    refuser([source | {"Challengers_compares": "T2"}, titulaire, challenger],
            "comparaison incomplete")
    refuser([source | {"Challengers_compares": "C1"}, titulaire, challenger],
            "comparaison incomplete")
    refuser([source | {"Challengers_compares": "T2|C1|INCONNU"},
             titulaire, challenger], "ids inconnus")
    refuser([source | {"Challengers_compares": "COMMENTAIRE_LIBRE"},
             titulaire, challenger], "ids inconnus")
    refuser([source | {"ID_position": "T2"}, titulaire, challenger],
            "dupliques")
    refuser([source | {"ID_position": ""}, titulaire, challenger],
            "vides")
    refuser([source | {"Challengers_compares": "AUCUNE"},
             titulaire, challenger], "ids inconnus")

    # L'absence de destination admissible permet CASH, pas un achat invente.
    cash = DUEL.calculer_duels(pd.DataFrame([
        ligne("TITULAIRE", "T1", 70, "VENDRE", "AUCUNE"),
        ligne("TITULAIRE", "T2", 90, "CONSERVER"),
    ]))
    assert len(cash) == 1 and cash.iloc[0]["Statut_duel"] == "CASH"

    # Egalite => aucune rotation, meme lorsque la comparaison est exhaustive.
    egal = DUEL.calculer_duels(pd.DataFrame([
        ligne("TITULAIRE", "T1", 90, "VENDRE", "T2"),
        ligne("TITULAIRE", "T2", 90, "RENFORCER"),
    ]))
    assert len(egal) == 1 and egal.iloc[0]["Statut_duel"] == "CONSERVER"
    print("09B : comparaison exhaustive, refus destinations omises, CASH et egalite OK")


if __name__ == "__main__":
    test()

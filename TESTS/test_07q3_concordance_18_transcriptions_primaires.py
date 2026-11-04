"""07Q3 — réception croisée des 18 transcriptions déjà contrôlées sur deux sources primaires.

Réutilise les deux tests de tableaux HTML archivés et le raccordement 07Q3.
Aucune collecte, écriture, certification SCE, note ni transaction.
"""
from pathlib import Path
import csv

from test_icape_faits_financiers_primaire_hors_reseau import test as verifier_icape
from test_fermentalg_faits_financiers_primaire_hors_reseau import test as verifier_fermentalg

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "FAITS_FINANCIERS_ICAPE_S1_2026_NON_CERTIFIES.csv",
    "FAITS_FINANCIERS_FERMENTALG_S1_2026_NON_CERTIFIES.csv",
)


def lire(path):
    with path.open(encoding="utf-8-sig", newline="") as fichier:
        return list(csv.DictReader(fichier))


def cle(r):
    return (
        r["Ticker"], r["Identifiant_emetteur"], r["ID_document"],
        r.get("Tableau_IFRS", r.get("Tableau_source", "")),
        r.get("Ligne_IFRS", r.get("Ligne_source", "")),
        r["Periode_cloture"], r["Unite_source"], r["SHA256_source"],
    )


def test():
    # Les contrôles préexistants relisent les HTML archivés, leur manifeste
    # SHA256, les tableaux et les 18 cellules financières source par source.
    verifier_icape()
    verifier_fermentalg()
    originaux = []
    for nom in SOURCES:
        originaux.extend(lire(ROOT / "AUDITS/REPARATION" / nom))
    sorties = lire(ROOT / "DONNEES/OBSERVATIONS_FINANCIERES_SSI_NON_CERTIFIEES.csv")
    assert len(originaux) == len(sorties) == 18
    index = {cle(r): r for r in originaux}
    assert len(index) == 18, "Doublon de fait primaire"
    assert len({cle(r) for r in sorties}) == 18, "Doublon de raccordement"
    assert {cle(r) for r in sorties} == set(index), "Faits perdus ou ajoutés dans 07Q3"
    for ligne in sorties:
        source = index[cle(ligne)]
        for champ in ("Valeur_source", "Source_URL", "Date_publication_UTC",
                      "Date_collecte_UTC", "Note_SSI", "Note_MCPA"):
            assert ligne[champ] == source[champ], (ligne["Ticker"], champ)
        assert ligne["Archive_source"].startswith("AUDITS/SOURCES_OFFICIELLES/")
        assert ligne["Statut_raccordement"].startswith("EN_ATTENTE_DATA"), (
            "Identité SCE non certifiée : admission ou qualification interdite")
        assert ligne["Note_SSI"] == ligne["Note_MCPA"] == "MANQUANTE"
    couverture = lire(ROOT / "DONNEES/COUVERTURE_OBSERVATIONS_SSI_NON_CERTIFIEES.csv")
    assert len(couverture) == 14
    assert sum(int(x["Nombre_observations_pistes"]) for x in couverture) == 18
    assert all(x["Identite_SCE_certifiee"] == "NON"
               and x["Transcription_chiffres_verifiee"] == "NON"
               and x["Note_SSI"] == x["Note_MCPA"] == "MANQUANTE"
               for x in couverture)
    assert all(x["Nombre_observations_pistes"] == "0"
               for x in couverture if x["Bloc_SSI"] in ("B4", "B5", "B6", "B7"))
    audit = lire(ROOT / "DONNEES/AUDIT_RACCORDEMENT_FAITS_SSI.csv")
    assert len(audit) == 1 and audit[0]["Observations"] == "18"
    assert audit[0]["Scores_attribues"] == "0"
    print("07Q3: 18/18 cellules retrouvées dans deux archives SHA256 et "
          "dans le raccordement ; identité SCE non certifiée, "
          "0 note, 0 challenger, 0 arbitrage.")


if __name__ == "__main__":
    test()

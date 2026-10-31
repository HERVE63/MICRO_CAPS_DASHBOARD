"""Réutilisation vérifiable de l'archive Hofseth et reprise isolée Fermentalg.

Contrôle hors réseau : une ancienne collecte réussie ne doit pas être refaite,
une erreur HTTP 403 ne doit pas bloquer le reste de l'univers, et aucun
document collecté ne devient automatiquement une preuve SCE/SSI certifiée.
"""
from pathlib import Path
import csv
import hashlib
import json
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parents[1]
ARCH = BASE / "AUDITS/SOURCES_OFFICIELLES/20261010T132940591629Z"
CONFIG = BASE / "CONFIG/DOCUMENTS_OFFICIELS_A_COLLECTER.csv"
REPRISE = BASE / "AUDITS/REPARATION/REGISTRE_REPRISE_FERMENTALG_20261031.csv"
DOSSIERS = BASE / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv"
HOF_SHA = "46b6b8b1fd0e73a6a18f1320c5dd457bd8f35499a1eacae3a06ff471c41801c6"


def lire(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test():
    historique = lire(ARCH / "AUDIT_DOCUMENTS.csv")
    assert len(historique) == 2
    par_id = {r["ID_document"]: r for r in historique}
    assert set(par_id) == {"FERMENTALG_CP_S1_2026", "HOFSETH_BIOCARE_Q2_2026"}
    fermentalg_ancien = par_id["FERMENTALG_CP_S1_2026"]
    assert fermentalg_ancien["Statut"] == "BLOQUE_SOURCE"
    assert "403" in fermentalg_ancien["Motif"]
    assert not fermentalg_ancien["SHA256"] and not fermentalg_ancien["Fichier_brut"]
    hof = par_id["HOFSETH_BIOCARE_Q2_2026"]
    assert hof["Statut"] == "DOCUMENT_COLLECTE_A_VERIFIER"
    assert hof["SHA256"] == HOF_SHA
    brut = BASE / hof["Fichier_brut"]
    assert brut.resolve().parent == ARCH.resolve()
    assert brut.read_bytes().startswith(b"%PDF-")
    assert hashlib.sha256(brut.read_bytes()).hexdigest() == HOF_SHA
    assert all(r["Notes_attribuees"] == "0" for r in historique)
    manifeste = json.loads((ARCH / "MANIFESTE.json").read_text(encoding="utf-8"))
    assert manifeste["documents_configures"] == 2
    assert manifeste["documents_collectes"] == 1
    assert manifeste["sources_bloquees"] == 1
    assert manifeste["notes_attribuees"] == 0

    cfg = lire(CONFIG)
    reprise = lire(REPRISE)
    assert len(cfg) == 2 and len(reprise) == 1
    assert {r["ID_document"] for r in cfg} == set(par_id)
    assert reprise[0] == next(r for r in cfg if r["ID_document"] == "FERMENTALG_CP_S1_2026")
    fer = reprise[0]
    assert fer["Ticker"] == "1F6.F"
    assert fer["Identifiant_emetteur"] == "ISIN:FR0011271600"
    assert fer["Type_source"] == "PUBLICATION_EMETTEUR"
    assert fer["Statut_identite"] == "A_VERIFIER_COTATION_1F6_F"
    assert fer["Date_publication"] == "2026-10-06T16:00:00Z"
    assert fer["Source_date_publication"].startswith("https://www.webdisclosure.fr/press-release/fermentalg-")
    assert fer["Source_habilitation_domaine"].startswith("https://www.webdisclosure.fr/press-release/fermentalg-")
    assert urlparse(fer["Source_URL"]).hostname == fer["Domaine_autorise"] == "www.webdisclosure.fr"
    assert "/press-release/fermentalg-epa-falg-half-year-results-2026" in fer["Source_URL"]
    assert not any(c.startswith("Note_") for c in fer)

    dossiers = [r for r in lire(DOSSIERS) if r["Ticker"] in ("1F6.F", "HBQ.F")]
    assert len(dossiers) == 2
    for r in dossiers:
        assert r["SSI"] == "MANQUANTE"
        assert r["SCE_valide"] == "NON"
        assert r["Statut_SSI"].startswith("EN_ATTENTE_DATA")
        assert all(r["Note_" + b] == "MANQUANTE" for b in "B1 B2 B3 B4 B5 B6 B7".split())
    print("REUTILISATION_HOFSETH_SHA256_OK; FERMENTALG_PDF_403_HISTORIQUE; "
          "REPRISE_HTML_ISOLEE_SANS_SCORE; SSI=EN_ATTENTE_DATA")


if __name__ == "__main__":
    test()

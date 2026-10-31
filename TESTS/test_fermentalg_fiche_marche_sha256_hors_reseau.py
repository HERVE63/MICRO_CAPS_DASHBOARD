"""Contrôle hors réseau de la fiche Deutsche Börse : preuve de marché, pas identité SCE.

Usage : python -B TESTS/test_fermentalg_fiche_marche_sha256_hors_reseau.py [dossier_capture]
Sans argument, vérifie le registre seul ; avec dossier, vérifie les octets acquis.
"""
from pathlib import Path
from html.parser import HTMLParser
import csv
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "CONFIG/DOCUMENTS_MARCHE_FERMENTALG_A_COLLECTER.csv"
ID = "FERMENTALG_DEUTSCHE_BOERSE_FRANKFURT_1F6"
URL = "https://live.deutsche-boerse.com/equity/fermentalg-eo-04"
ISIN = "FR0011271600"


def lignes(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class Texte(HTMLParser):
    def __init__(self):
        super().__init__()
        self.morceaux = []

    def handle_data(self, data):
        self.morceaux.append(data)


def test(capture=None):
    rows = lignes(REG)
    assert len(rows) == 1, "Le registre de capture doit etre isole"
    r = rows[0]
    assert r["ID_document"] == ID
    assert r["Ticker"] == "1F6.F"
    assert r["Identifiant_emetteur"] == "ISIN:" + ISIN
    assert r["Source_URL"] == r["Source_habilitation_domaine"] == URL
    assert r["Domaine_autorise"] == "live.deutsche-boerse.com"
    assert r["Type_source"] == "DONNEE_MARCHE_IDENTITE"
    assert r["Date_publication"] == "" and r["Date_publication_inconnue"] == "OUI"
    assert r["Statut_identite"] == "A_VERIFIER_COTATION_1F6_F"
    assert not any(k.startswith("Note_") or k in ("SSI", "MCPA") for k in r)
    if capture is None:
        print("REGISTRE_FICHE_MARCHE_OK ; collecte non encore certifiee")
        return
    dossier = Path(capture).resolve()
    assert dossier.is_dir()
    assert dossier.parent == (ROOT / "AUDITS/SOURCES_OFFICIELLES").resolve()
    audits = lignes(dossier / "AUDIT_DOCUMENTS.csv")
    assert len(audits) == 1
    a = audits[0]
    assert a["ID_document"] == ID and a["Source_URL"] == URL
    assert a["Type_source"] == "DONNEE_MARCHE_IDENTITE"
    assert a["Statut"] == "DOCUMENT_COLLECTE_A_VERIFIER", a.get("Motif", "")
    assert a["Statut_identite"] == "A_VERIFIER_COTATION_1F6_F"
    assert a["Date_publication"] == ""
    assert a["Statut_date_publication"] == "INCONNUE_NE_PAS_UTILISER_RETROSPECTIVEMENT"
    assert a["Notes_attribuees"] == "0"
    manifeste = json.loads((dossier / "MANIFESTE.json").read_text(encoding="utf-8"))
    assert manifeste["documents_configures"] == manifeste["documents_collectes"] == 1
    assert manifeste["sources_bloquees"] == manifeste["notes_attribuees"] == 0
    assert manifeste["couverture_complete"] is False
    assert manifeste["publications_dates_inconnues"] == 1
    assert manifeste["registre_SHA256"] == hashlib.sha256(REG.read_bytes()).hexdigest()
    for name, digest in manifeste["fichiers"].items():
        assert hashlib.sha256((dossier / name).read_bytes()).hexdigest() == digest
    brut = (ROOT / a["Fichier_brut"]).resolve()
    assert brut.parent == dossier
    data = brut.read_bytes()
    assert hashlib.sha256(data).hexdigest() == a["SHA256"] == manifeste["fichiers"][brut.name]
    assert len(data) > 1000
    assert "html" in a["Type_contenu"].lower()
    parser = Texte()
    parser.feed(data.decode("utf-8", errors="replace"))
    texte = re.sub(r"\s+", " ", " ".join(parser.morceaux))
    assert "FERMENTALG" in texte.upper() and ISIN in texte
    assert re.search(r"\bSymbol\s*:\s*1F6\b", texte, re.IGNORECASE), "Symbole officiel absent"
    assert "Frankfurt" in texte, "Place Frankfurt non lisible"
    # La fiche identifie le symbole officiel 1F6, PAS le suffixe fournisseur .F.
    # Elle ne donne ni date de publication ni validation SCE/SSI/MCPA.
    print("FICHE_MARCHE_SHA256_OK ; symbole 1F6 et ISIN concordants ; "
          "suffixe 1F6.F non certifie ; SSI/MCPA=MANQUANTE")


if __name__ == "__main__":
    test(sys.argv[1] if len(sys.argv) > 1 else None)

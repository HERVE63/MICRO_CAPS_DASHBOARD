"""Contrôle hors réseau des faits Fermentalg sur HTML primaire réellement archivé.

Réutilise le parseur de tableaux du test ICAPE ; ne crée aucune preuve SCE,
note SSI/MCPA, valeur de FCF ni admission économique.
"""
from pathlib import Path
import csv
import hashlib
import json
from test_icape_faits_financiers_primaire_hors_reseau import tableaux

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "AUDITS/SOURCES_OFFICIELLES/20261031T120058499540Z"
FAITS = ROOT / "AUDITS/REPARATION/FAITS_FINANCIERS_FERMENTALG_S1_2026_NON_CERTIFIES.csv"
SHA = "e6b16e996a4e2eac0bf88e94bdc7c56082798f35bb467707fc1abdd8f61b2f55"
SOURCE_ID = "FERMENTALG_CP_S1_2026"
ATTENDUS = {
    ("RESULTAT_S1", "Revenue", "2026-06-30"): "7,416",
    ("RESULTAT_S1", "Revenue", "2025-06-30"): "7,605",
    ("RESULTAT_S1", "Operating income before share-based payments and non-recurring items", "2026-06-30"): "-4,270",
    ("RESULTAT_S1", "Operating income after share-based payments and non-recurring items", "2026-06-30"): "-4,395",
    ("RESULTAT_S1", "Net income attributable to the Group", "2026-06-30"): "-4,199",
    ("BILAN_S1", "Shareholders' equity", "2026-06-30"): "31,906",
    ("BILAN_S1", "Non-current financial liabilities", "2026-06-30"): "3,622",
    ("BILAN_S1", "Current financial liabilities", "2026-06-30"): "310",
    ("BILAN_S1", "Cash and cash equivalents", "2026-06-30"): "10,785",
}


def lire(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test():
    manifest = json.loads((CAPTURE / "MANIFESTE.json").read_text(encoding="utf-8"))
    assert manifest["documents_configures"] == manifest["documents_collectes"] == 1
    assert manifest["sources_bloquees"] == manifest["notes_attribuees"] == 0
    assert manifest["dossiers_univers"] == 1361
    audits = lire(CAPTURE / "AUDIT_DOCUMENTS.csv")
    assert len(audits) == 1
    a = audits[0]
    assert a["ID_document"] == SOURCE_ID
    assert a["Statut"] == "DOCUMENT_COLLECTE_A_VERIFIER"
    assert a["Statut_identite"] == "A_VERIFIER_COTATION_1F6_F"
    assert a["Statut_date_publication"] == "DATE_DECLAREE_A_VERIFIER"
    assert a["Date_publication"] == "2026-10-06T16:00:00Z"
    assert a["Notes_attribuees"] == "0" and a["SHA256"] == SHA
    path = ROOT / a["Fichier_brut"]
    assert path.resolve().parent == CAPTURE.resolve()
    brut = path.read_bytes()
    assert hashlib.sha256(brut).hexdigest() == SHA == manifest["fichiers"][path.name]
    assert hashlib.sha256(brut + b"corruption").hexdigest() != SHA
    for nom, empreinte in manifest["fichiers"].items():
        assert hashlib.sha256((CAPTURE / nom).read_bytes()).hexdigest() == empreinte
    html = brut.decode("utf-8")
    assert "FERMENTALG" in html.upper() and "FR0011271600" in html
    assert "1F6.F" not in html, "Le document ne prouve pas la cotation Yahoo .F"
    t = tableaux(html)
    resultat = [x for x in t if all(any(r[0] == k for r in x)
                                    for k in ("Revenue", "Net income attributable to the Group"))]
    bilan = [x for x in t if all(any(r[0] == k for r in x)
                                 for k in ("Shareholders' equity", "Cash and cash equivalents"))]
    assert len(resultat) == len(bilan) == 1, "Table source absente ou ambiguë"
    tables = {"RESULTAT_S1": resultat[0], "BILAN_S1": bilan[0]}
    assert "H1 2025" in resultat[0][0][1] and "H1 2026" in resultat[0][0][2]
    assert "31/12/2025" in bilan[0][0][1] and "30/06/2026" in bilan[0][0][2]
    faits = lire(FAITS)
    assert len(faits) == len(ATTENDUS)
    assert len({(r["Tableau_source"], r["Ligne_source"], r["Periode_cloture"]) for r in faits}) == len(faits)
    for r in faits:
        cle = (r["Tableau_source"], r["Ligne_source"], r["Periode_cloture"])
        assert cle in ATTENDUS
        assert r["Valeur_source"] == ATTENDUS[cle]
        assert r["Ticker"] == "1F6.F"
        assert r["Identifiant_emetteur"] == "ISIN:FR0011271600"
        assert r["ID_document"] == SOURCE_ID
        assert r["Source_URL"] == a["Source_URL"]
        assert r["Date_publication_UTC"] == a["Date_publication"]
        assert r["Date_collecte_UTC"] == a["Date_collecte_UTC"]
        assert r["SHA256_source"] == SHA
        assert r["Unite_source"] == "kEUR"
        assert r["Statut_qualification"] == "EN_ATTENTE_DATA"
        assert r["Note_SSI"] == r["Note_MCPA"] == "MANQUANTE"
        assert r["Statut_cotation"] == "A_VERIFIER_COTATION_1F6_F"
        matches = [x for x in tables[r["Tableau_source"]] if x[0] == r["Ligne_source"]]
        assert len(matches) == 1 and len(matches[0]) >= 3
        col = 1 if r["Periode_cloture"] == "2025-06-30" else 2
        assert matches[0][col] == r["Valeur_source"], "Transcription divergente: " + str(cle)
    print("FERMENTALG: 9 faits contrôlés sur HTML SHA256; 1F6.F non certifié; "
          "SSI/MCPA=MANQUANTE; aucun FCF calculé")


if __name__ == "__main__":
    test()

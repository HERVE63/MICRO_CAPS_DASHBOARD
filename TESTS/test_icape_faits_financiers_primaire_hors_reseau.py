"""Contrôle hors réseau de faits IFRS ICAPE sur capture primaire immuable.

Ne transforme jamais une observation en preuve SCE certifiée, note SSI ou MCPA.
La table de faits est une transcription contrôlée, pas une recommandation.
"""
from pathlib import Path
import csv
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "AUDITS/SOURCES_OFFICIELLES/20261031T103236976336Z"
FAITS = ROOT / "AUDITS/REPARATION/FAITS_FINANCIERS_ICAPE_S1_2026_NON_CERTIFIES.csv"
SOURCE_SHA = "05605e38d3a3e9778d3d8468b613752fe54ef2bbe529bd109b5c622824b0669c"
SOURCE_ID = "ICAPE_RESULTATS_S1_2026_EURONEXT"
URL = "https://live.euronext.com/en/ajax/node/company-press-release/12913664"
ATTENDUS = {
    ("COMPTE_RESULTAT_IFRS", "Revenue"): "113,342",
    ("COMPTE_RESULTAT_IFRS", "Current EBITDA"): "7,760",
    ("COMPTE_RESULTAT_IFRS", "EBIT"): "4,688",
    ("COMPTE_RESULTAT_IFRS", "Group share"): "1,648",
    ("BILAN_IFRS", "Cash and cash equivalents"): "18,341",
    ("BILAN_IFRS", "Borrowings and financial debt"): "31,349",
    ("BILAN_IFRS", "Borrowings and bank overdrafts"): "14,533",
    ("FLUX_TRESORERIE_IFRS", "Cash flow from operating activities"): "5,152",
    ("FLUX_TRESORERIE_IFRS", "Cash flow from investing activities"): "(3,904)",
}
MARQUEURS = {
    "COMPTE_RESULTAT_IFRS": ("Revenue", "Current EBITDA", "Group share"),
    "BILAN_IFRS": ("Total assets", "Borrowings and bank overdrafts"),
    "FLUX_TRESORERIE_IFRS": ("Cash flow from operating activities",
                           "Cash flow from investing activities"),
}


def empreinte(data):
    return hashlib.sha256(data).hexdigest()


def normaliser(fragment):
    # Extrait seulement les cellules d'une table déjà archivée ; pas de réseau.
    texte = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", texte).strip()


def tableaux(texte):
    resultat = []
    for table in re.findall(r"<table\b[^>]*>(.*?)</table>", texte,
                            flags=re.IGNORECASE | re.DOTALL):
        lignes = []
        for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", table,
                             flags=re.IGNORECASE | re.DOTALL):
            cellules = [normaliser(x) for x in
                        re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", tr,
                                   flags=re.IGNORECASE | re.DOTALL)]
            cellules = [x for x in cellules if x]
            if cellules:
                lignes.append(cellules)
        resultat.append(lignes)
    return resultat


def test():
    manifeste = json.loads((CAPTURE / "MANIFESTE.json").read_text(encoding="utf-8"))
    assert manifeste["notes_attribuees"] == 0
    assert manifeste["documents_collectes"] == 4
    audit_path = CAPTURE / "AUDIT_DOCUMENTS.csv"
    assert empreinte(audit_path.read_bytes()) == manifeste["fichiers"][audit_path.name]
    with audit_path.open(encoding="utf-8", newline="") as f:
        audits = list(csv.DictReader(f))
    assert len(audits) == 4
    ligne = [r for r in audits if r["ID_document"] == SOURCE_ID]
    assert len(ligne) == 1
    source = ligne[0]
    assert source["Source_URL"] == URL
    assert source["Date_publication"] == "2026-10-01T05:45:00Z"
    assert source["Statut_date_publication"] == "DATE_DECLAREE_A_VERIFIER"
    assert source["Statut"] == "DOCUMENT_COLLECTE_A_VERIFIER"
    assert source["Notes_attribuees"] == "0"
    assert source["Identifiant_emetteur"] == "ISIN:FR001400A3Q3"
    assert source["SHA256"] == SOURCE_SHA
    assert source["Type_contenu"].startswith("text/html")
    brut_path = ROOT / source["Fichier_brut"]
    assert brut_path.resolve().parent == CAPTURE.resolve(), "Chemin archive non autorisé"
    brut = brut_path.read_bytes()
    assert empreinte(brut) == SOURCE_SHA == manifeste["fichiers"][brut_path.name]
    # Régression : un seul octet changé rend la source inutilisable.
    assert empreinte(brut + b"X") != SOURCE_SHA
    texte = brut.decode("utf-8")
    assert 'data-isin="FR001400A3Q3"' in texte
    assert "ICAPE" in texte
    assert "ALICA" in texte
    # Le communiqué ne prouve PAS que la cotation allemande Z8J.F est identique.
    assert "Z8J.F" not in texte
    tables = tableaux(texte)
    assert len(tables) >= 3, "Tables IFRS introuvables"
    selection = {}
    for nom, marqueurs in MARQUEURS.items():
        candidats = [t for t in tables
                     if all(any(row[0] == m for row in t) for m in marqueurs)]
        assert len(candidats) == 1, "Table IFRS absente ou ambiguë: " + nom
        selection[nom] = candidats[0]
    with FAITS.open(encoding="utf-8", newline="") as f:
        faits = list(csv.DictReader(f))
    assert len(faits) == len(ATTENDUS)
    assert len({(r["Tableau_IFRS"], r["Ligne_IFRS"]) for r in faits}) == len(faits)
    for r in faits:
        cle = (r["Tableau_IFRS"], r["Ligne_IFRS"])
        assert cle in ATTENDUS, "Ligne financière ajoutée sans protocole"
        assert r["Valeur_source"] == ATTENDUS[cle]
        assert r["Ticker"] == "Z8J.F"
        assert r["Identifiant_emetteur"] == "ISIN:FR001400A3Q3"
        assert r["ID_document"] == SOURCE_ID
        assert r["Source_URL"] == URL
        assert r["Date_publication_UTC"] == source["Date_publication"]
        assert r["Date_collecte_UTC"] == source["Date_collecte_UTC"]
        assert r["SHA256_source"] == SOURCE_SHA
        assert r["Periode_cloture"] == "2026-06-30"
        assert r["Unite_source"] == "kEUR"
        assert r["Statut_qualification"] == "EN_ATTENTE_DATA"
        assert r["Note_SSI"] == r["Note_MCPA"] == "MANQUANTE"
        assert r["Statut_cotation"] == "A_VERIFIER_COTATION_Z8J_F"
        matches = [row for row in selection[r["Tableau_IFRS"]]
                   if row[0] == r["Ligne_IFRS"]]
        assert len(matches) == 1, "Ligne IFRS ambiguë: " + str(cle)
        assert len(matches[0]) >= 2 and matches[0][1] == r["Valeur_source"], (
            "Transcription non conforme à la source brute: " + str(cle))
    # Incohérence du communiqué: titre 1,6 M€ et narration 1,7 M€.
    # Le tableau IFRS fournit 1 648 k€ ; aucune note ou correction automatique.
    assert "Net Income (Group Share): €1.6 Million" in texte
    assert "rose sharply to €1.7 million" in texte
    print("ICAPE: 9 faits IFRS vérifiés sur archive SHA256 ; "
          "divergence rédactionnelle 1,6/1,7 M€ signalée ; "
          "Z8J.F non certifié ; SSI/MCPA non notés")


if __name__ == "__main__":
    test()

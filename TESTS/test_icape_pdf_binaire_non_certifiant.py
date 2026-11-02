"""Contrôle binaire du rapport ICAPE archivé : preuve d'intégrité, PAS certification SSI.

Réutilise le PDF 07AA du 31/10/2026 et son manifeste immuable.
Aucune collecte réseau, aucune écriture dans DONNEES, aucune note.
"""
from pathlib import Path
from io import BytesIO
import csv
import hashlib
import json
import re

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "AUDITS/SOURCES_OFFICIELLES/20261031T231641051863Z"
ID = "ICAPE_RFS_S1_2026_OFFICIEL"
SHA_ATTENDU = "549ce7bd618afe3c8fab56a33898566e6e3ad9272fb05527e78989d860e7ad96"
URL_ATTENDUE = "https://www.icape-group.com/wp-content/uploads/2026/10/ICAPE-GROUP-RFS-30.06.2026-VF_vdef.pdf"


def tester():
    manifeste = json.loads((ARCHIVE / "MANIFESTE.json").read_text(encoding="utf-8"))
    assert manifeste["notes_attribuees"] == 0
    audit = ARCHIVE / "AUDIT_DOCUMENTS.csv"
    assert hashlib.sha256(audit.read_bytes()).hexdigest() == manifeste["fichiers"]["AUDIT_DOCUMENTS.csv"]
    with audit.open(newline="", encoding="utf-8-sig") as f:
        lignes = [r for r in csv.DictReader(f) if r["ID_document"] == ID]
    assert len(lignes) == 1, "Document primaire ambigu ou absent"
    r = lignes[0]
    assert r["Source_URL"] == r["URL_finale"] == URL_ATTENDUE
    assert r["Type_contenu"].split(";")[0].lower() == "application/pdf"
    assert r["Date_publication"] == "2026-10-08"
    assert r["Statut_date_publication"] == "DATE_DECLAREE_A_VERIFIER"
    assert r["Statut"] == "DOCUMENT_COLLECTE_A_VERIFIER"
    assert r["Notes_attribuees"] == "0"
    assert r["Identifiant_emetteur"] == "ISIN:FR001400A3Q3"
    assert r["SHA256"] == SHA_ATTENDU
    assert r["Date_collecte_UTC"].endswith("+00:00") or r["Date_collecte_UTC"].endswith("Z")
    chemin = (ROOT / r["Fichier_brut"]).resolve()
    assert chemin.parent == ARCHIVE.resolve(), "Chemin d'archive non autorisé"
    assert chemin.name == SHA_ATTENDU + ".bin"
    octets = chemin.read_bytes()
    sha = hashlib.sha256(octets).hexdigest()
    assert sha == SHA_ATTENDU == manifeste["fichiers"][chemin.name]
    assert octets[:5] == b"%PDF-", "Le fichier déclaré PDF ne possède pas la signature PDF"
    assert b"%%EOF" in octets[-4096:], "Fin du PDF non trouvée"
    lecteur = PdfReader(BytesIO(octets), strict=False)
    assert not lecteur.is_encrypted, "PDF chiffré : revue manuelle nécessaire"
    assert len(lecteur.pages) == 42, "Pagination différente du rapport ICAPE archivé"
    extraits = [(i + 1, p.extract_text() or "") for i, p in enumerate(lecteur.pages)]
    pages_lisibles = sum(bool(t.strip()) for _, t in extraits)
    pages_icape = [n for n, t in extraits if re.search(r"\\bICAPE\\b", t, flags=re.I)]
    assert pages_lisibles >= 30, "Extraction textuelle insuffisante : revue manuelle requise"
    assert pages_icape, "Nom de l'émetteur introuvable dans le contenu PDF extrait"
    # Les marqueurs textuels ne prouvent ni la date officielle de publication,
    # ni le lien entre l'ISIN de l'émetteur et la cotation Z8J.F.
    print(json.dumps({
        "controle": "ICAPE_PDF_BINAIRE_NON_CERTIFIANT",
        "sha256_verifie": sha,
        "taille_octets": len(octets),
        "pages_pdf": len(lecteur.pages),
        "pages_texte_lisible": pages_lisibles,
        "pages_mention_icape": pages_icape[:20],
        "date_publication": "DECLAREE_A_VERIFIER",
        "identite_Z8J_F": "EN_ATTENTE_DATA",
        "ssi_mcpa": "MANQUANTE",
        "notes_attribuees": 0
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    tester()

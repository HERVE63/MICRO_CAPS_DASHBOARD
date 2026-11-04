"""Revalidation sur octets des archives 07AA legacy Hofseth (aucune preuve SCE)."""
from pathlib import Path
import csv
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
IDS=("20261010T132139701764Z","20261010T132359775157Z",
     "20261010T132940591629Z")
SHA_ATTENDU="46b6b8b1fd0e73a6a18f1320c5dd457bd8f35499a1eacae3a06ff471c41801c6"

def tester():
    captures=[]
    for ident_archive in IDS:
        dossier=ROOT/"AUDITS"/"SOURCES_OFFICIELLES"/ident_archive
        manifeste=json.loads((dossier/"MANIFESTE.json").read_text(encoding="utf-8"))
        assert "fichiers" not in manifeste, "Le schema legacy doit etre traite separement"
        with (dossier/"AUDIT_DOCUMENTS.csv").open(encoding="utf-8-sig",newline="") as f:
            lignes=list(csv.DictReader(f))
        assert len(lignes)==2, "Schema historique inattendu"
        hofseth=[r for r in lignes if r["ID_document"]=="HOFSETH_BIOCARE_Q2_2026"]
        assert len(hofseth)==1
        r=hofseth[0]
        assert r["Ticker"]=="HBQ.F" and r["Identifiant_emetteur"]=="ISIN:NO0010598683"
        assert r["Statut"]=="DOCUMENT_COLLECTE_A_VERIFIER"
        assert r["Type_source"]=="PUBLICATION_EMETTEUR"
        assert r["Notes_attribuees"]=="0"
        assert r["SHA256"]==SHA_ATTENDU
        assert r["Date_publication"]=="2026-08-21", "Date seulement declaree dans l'audit legacy"
        assert r["Source_URL"].startswith("https://")
        fichier=(ROOT/r["Fichier_brut"]).resolve()
        assert fichier.parent==dossier.resolve(), "Traversal de chemin refuse"
        assert fichier.name==SHA_ATTENDU+".bin"
        octets=fichier.read_bytes()
        assert octets.startswith(b"%PDF-"), "Fichier declare PDF sans signature PDF"
        assert hashlib.sha256(octets).hexdigest()==SHA_ATTENDU
        captures.append((r["Source_URL"],r["SHA256"],len(octets)))
    assert len(set(captures))==1, "Les trois copies historiques doivent etre identiques"
    print(json.dumps({"archives_legacy_verifiees":len(IDS),
                      "sources_independantes":1,
                      "sha256_octets_verifie":SHA_ATTENDU,
                      "taille_octets":captures[0][2],
                      "audit_legacy_sans_sha256":True,
                      "certification_SCE":False,
                      "notes_SSI_MCPA":0},ensure_ascii=False))
if __name__=="__main__":tester()

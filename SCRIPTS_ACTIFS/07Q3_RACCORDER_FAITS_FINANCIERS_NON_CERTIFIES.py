"""07Q3 — raccordement en lecture seule des faits financiers déjà archivés.

Les transcriptions primaires sont des PISTES, jamais des preuves SCE certifiées.
N'écrit ni dossiers SSI, ni scores, ni portefeuille, ni historiques officiels.
Chaque ligne invalide est isolée sans bloquer les autres dossiers.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import json
import re

NOMS = (
    "FAITS_FINANCIERS_ICAPE_S1_2026_NON_CERTIFIES.csv",
    "FAITS_FINANCIERS_FERMENTALG_S1_2026_NON_CERTIFIES.csv",
)
CHAMPS = ("Ticker", "Identifiant_emetteur", "ID_document", "Source_URL",
          "Date_publication_UTC", "Date_collecte_UTC", "SHA256_source",
          "Periode_cloture", "Unite_source", "Valeur_source",
          "Statut_qualification", "Note_SSI", "Note_MCPA", "Statut_cotation")
SORTIE = ("Fichier_faits", "Ticker", "Identifiant_emetteur", "ID_document",
          "Tableau_source", "Ligne_source", "Periode_cloture", "Unite_source",
          "Valeur_source", "Source_URL", "Date_publication_UTC",
          "Date_collecte_UTC", "SHA256_source", "Archive_source",
          "Statut_raccordement", "Motif", "Note_SSI", "Note_MCPA")


def lignes_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def date_utc(value):
    d = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def verifier_montant(texte):
    if not re.fullmatch(r"\\(?-?[0-9][0-9,]*(?:\\.[0-9]+)?\\)?", texte):
        return False
    if texte.startswith("(") != texte.endswith(")"):
        return False
    try:
        Decimal(texte.strip("()").replace(",", ""))
        return True
    except InvalidOperation:
        return False


def indexer_archives(racine):
    """Index 07AA par identifiant de document ET empreinte, sans supposer le ticker."""
    index = {}
    for audit in sorted((racine / "AUDITS/SOURCES_OFFICIELLES").glob("*/AUDIT_DOCUMENTS.csv")):
        dossier = audit.parent
        try:
            manifest = json.loads((dossier / "MANIFESTE.json").read_text(encoding="utf-8"))
            if manifest.get("fichiers", {}).get(audit.name) != sha256(audit):
                continue
            for a in lignes_csv(audit):
                if a.get("Statut") != "DOCUMENT_COLLECTE_A_VERIFIER":
                    continue
                cle = (a.get("ID_document", ""), a.get("SHA256", ""))
                index.setdefault(cle, []).append((dossier, manifest["fichiers"], a))
        except (OSError, ValueError, KeyError, UnicodeError, TypeError):
            continue
    return index


def controler_ligne(r, dossiers, archives, racine, maintenant):
    if any(not r.get(c, "").strip() for c in CHAMPS):
        return "EN_ATTENTE_DATA_SCHEMA", "Champ obligatoire absent", ""
    if r["Note_SSI"] != "MANQUANTE" or r["Note_MCPA"] != "MANQUANTE" or r["Statut_qualification"] != "EN_ATTENTE_DATA":
        return "REJET_NOTE_OU_QUALIFICATION", "Score/qualification non autorisé dans la transcription", ""
    if r["Unite_source"] != "kEUR" or not verifier_montant(r["Valeur_source"]):
        return "EN_ATTENTE_DATA_UNITE", "Montant ou unité non contrôlable", ""
    if not re.fullmatch(r"[0-9a-f]{64}", r["SHA256_source"]):
        return "EN_ATTENTE_DATA_SHA256", "Empreinte malformée", ""
    if not r["Source_URL"].startswith("https://"):
        return "EN_ATTENTE_DATA_PROVENANCE", "URL non HTTPS", ""
    try:
        publ = date_utc(r["Date_publication_UTC"])
        capture = date_utc(r["Date_collecte_UTC"])
        cloture = datetime.fromisoformat(r["Periode_cloture"]).replace(tzinfo=timezone.utc)
        if not (cloture <= publ <= capture <= maintenant):
            raise ValueError("Dates incohérentes")
    except ValueError:
        return "EN_ATTENTE_DATA_DATES", "Dates invalides ou non chronologiques", ""
    candidats = archives.get((r["ID_document"], r["SHA256_source"]), [])
    for dossier, fichiers, a in candidats:
        brut = (racine / a.get("Fichier_brut", "")).resolve()
        if brut.parent != dossier.resolve() or brut.name != r["SHA256_source"] + ".bin":
            continue
        if fichiers.get(brut.name) != r["SHA256_source"] or not brut.is_file():
            continue
        if sha256(brut) != r["SHA256_source"]:
            continue
        if any(a.get(k, "") != r[v] for k, v in (
            ("Ticker", "Ticker"), ("Identifiant_emetteur", "Identifiant_emetteur"),
            ("Source_URL", "Source_URL"), ("Date_publication", "Date_publication_UTC"),
            ("Date_collecte_UTC", "Date_collecte_UTC"))):
            continue
        chemin = str(brut.relative_to(racine))
        if r["Ticker"] not in dossiers:
            return "EN_ATTENTE_DATA_DOSSIER", "Ticker absent des dossiers SSI", chemin
        ident = dossiers[r["Ticker"]].get("Identifiant_emetteur_verifie", "").strip()
        if ident != r["Identifiant_emetteur"]:
            return "EN_ATTENTE_DATA_IDENTITE", "Identité SCE non certifiée/concordance absente", chemin
        return "PISTE_FINANCIERE_SHA256_OK_NON_CERTIFIEE", "Transcription documentaire seulement; aucune note autorisée", chemin
    return "EN_ATTENTE_DATA_SOURCE", "Archive primaire non concordante ou SHA256 invalide", ""


def executer(racine=None, maintenant=None):
    racine = Path(racine or Path(__file__).resolve().parents[1]).resolve()
    maintenant = maintenant or datetime.now(timezone.utc)
    d = racine / "DONNEES"
    dossiers_path = d / "DOSSIERS_SSI_A_QUALIFIER.csv"
    if not dossiers_path.exists():
        raise RuntimeError("07Q doit produire les dossiers SSI avant 07Q3")
    dossiers = {r["Ticker"]: r for r in lignes_csv(dossiers_path)}
    archives = indexer_archives(racine)
    resultat = []
    for nom in NOMS:
        path = racine / "AUDITS/REPARATION" / nom
        if not path.exists():
            continue
        for r in lignes_csv(path):
            statut, motif, archive = controler_ligne(r, dossiers, archives, racine, maintenant)
            resultat.append({
                "Fichier_faits": str(path.relative_to(racine)),
                "Ticker": r.get("Ticker", ""), "Identifiant_emetteur": r.get("Identifiant_emetteur", ""),
                "ID_document": r.get("ID_document", ""),
                "Tableau_source": r.get("Tableau_IFRS", r.get("Tableau_source", "")),
                "Ligne_source": r.get("Ligne_IFRS", r.get("Ligne_source", "")),
                "Periode_cloture": r.get("Periode_cloture", ""), "Unite_source": r.get("Unite_source", ""),
                "Valeur_source": r.get("Valeur_source", ""), "Source_URL": r.get("Source_URL", ""),
                "Date_publication_UTC": r.get("Date_publication_UTC", ""),
                "Date_collecte_UTC": r.get("Date_collecte_UTC", ""),
                "SHA256_source": r.get("SHA256_source", ""), "Archive_source": archive,
                "Statut_raccordement": statut, "Motif": motif,
                "Note_SSI": "MANQUANTE", "Note_MCPA": "MANQUANTE",
            })
    destination = d / "OBSERVATIONS_FINANCIERES_SSI_NON_CERTIFIEES.csv"
    tmp = destination.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SORTIE)
        writer.writeheader()
        writer.writerows(resultat)
    tmp.replace(destination)
    bilan = {}
    for r in resultat:
        bilan[r["Statut_raccordement"]] = bilan.get(r["Statut_raccordement"], 0) + 1
    audit = d / "AUDIT_RACCORDEMENT_FAITS_SSI.csv"
    with audit.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=("Observations", "Dossiers", "SHA256_et_identite_concordants_non_certifies",
                                          "EN_ATTENTE_DATA", "Scores_attribues", "Statut"))
        w.writeheader()
        w.writerow({"Observations": len(resultat), "Dossiers": len({r["Ticker"] for r in resultat}),
                    "SHA256_et_identite_concordants_non_certifies": bilan.get("PISTE_FINANCIERE_SHA256_OK_NON_CERTIFIEE", 0),
                    "EN_ATTENTE_DATA": len(resultat) - bilan.get("PISTE_FINANCIERE_SHA256_OK_NON_CERTIFIEE", 0),
                    "Scores_attribues": 0, "Statut": "AUCUNE_ADMISSION_SSI_AUTOMATIQUE"})
    print("07Q3 observations financières (sans score):", len(resultat), bilan)
    return resultat


if __name__ == "__main__":
    executer()

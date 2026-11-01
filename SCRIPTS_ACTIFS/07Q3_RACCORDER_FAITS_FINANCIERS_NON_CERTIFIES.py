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
    """Horodatage ISO avec heure et UTC explicite, sans conversion implicite.

    Un décalage +01:00 n'est pas une date de provenance UTC, même si
    datetime.astimezone() saurait le convertir. Les archives 07AA et 07R
    imposent la même exigence pour ne pas certifier des dates ambiguës.
    """
    texte = str(value).strip()
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)",
        texte,
    ):
        raise ValueError("Horodatage sans heure et UTC explicites")
    d = datetime.fromisoformat(texte.replace("Z", "+00:00"))
    if d.utcoffset() != timezone.utc.utcoffset(d):
        raise ValueError("Fuseau de provenance non UTC")
    return d


def verifier_montant(texte):
    """Séparateurs de milliers stricts : '1,2,3' ne vaut jamais 123."""
    nombre = r"(?:0|[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]+)?"
    if not re.fullmatch(rf"(?:-?{nombre}|\({nombre}\))", texte):
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
    if not (r.get("Tableau_IFRS", r.get("Tableau_source", "")).strip()
            and r.get("Ligne_IFRS", r.get("Ligne_source", "")).strip()):
        return "EN_ATTENTE_DATA_SCHEMA", "Tableau ou ligne source absent", ""
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
        # Une période comptable est une DATE civile, pas un horodatage
        # qu'on pourrait décaler ou tronquer silencieusement.
        periode = r["Periode_cloture"]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", periode):
            raise ValueError("Période de clôture non civile")
        cloture = datetime.fromisoformat(periode).replace(tzinfo=timezone.utc)
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
        if ident == "CONFLIT_TICKER_DUPLIQUE":
            return "EN_ATTENTE_DATA_IDENTITE_AMBIGUE", "Ticker dupliqué dans les dossiers SSI ; aucune identité ne peut être retenue", chemin
        if ident != r["Identifiant_emetteur"]:
            return "EN_ATTENTE_DATA_IDENTITE", "Identité SCE non certifiée/concordance absente", chemin
        return "PISTE_FINANCIERE_SHA256_OK_NON_CERTIFIEE", "Transcription documentaire seulement; aucune note autorisée", chemin
    return "EN_ATTENTE_DATA_SOURCE", "Archive primaire non concordante ou SHA256 invalide", ""



# Ce classement thématique n'est PAS une vérification des chiffres transcrits.
# Il sert seulement à identifier les blocs où des observations déjà archivées
# existent, pour organiser les contrôles primaires et l'identité SCE.
BLOCS_PISTES = {
    "B1": {"Cash and cash equivalents", "Borrowings and financial debt",
           "Borrowings and bank overdrafts", "Shareholders' equity",
           "Non-current financial liabilities", "Current financial liabilities"},
    "B2": {"Current EBITDA", "EBIT", "Group share",
           "Cash flow from operating activities", "Cash flow from investing activities",
           "Operating income before share-based payments and non-recurring items",
           "Operating income after share-based payments and non-recurring items",
           "Net income attributable to the Group"},
    "B3": {"Revenue"},
    "B4": set(), "B5": set(), "B6": set(), "B7": set(),
}
STATUTS_ARCHIVE_INTEGRE = {
    "PISTE_FINANCIERE_SHA256_OK_NON_CERTIFIEE",
    "EN_ATTENTE_DATA_IDENTITE",
    "EN_ATTENTE_DATA_IDENTITE_AMBIGUE",
}
COUVERTURE_COLONNES = (
    "Ticker", "Bloc_SSI", "Nombre_observations_pistes",
    "Nombre_documents_SHA256_distincts", "Lignes_source_pistes",
    "Periodes_pistes", "SHA256_sources_pistes", "Statuts_raccordement",
    "Statut_bloc", "Identite_SCE_certifiee", "Transcription_chiffres_verifiee",
    "Note_SSI", "Note_MCPA",
)


def isoler_conflits_factuels(resultat):
    """Même source/tableau/ligne/période/unité : deux valeurs distinctes = quarantaine.

    Ne compare pas des publications différentes, qui peuvent être retraitées.
    Ne modifie jamais les transcriptions archivées. Aucun score n'est autorisé.
    """
    groupes = {}
    for r in resultat:
        if r["Statut_raccordement"] not in STATUTS_ARCHIVE_INTEGRE:
            continue
        cle = tuple(r[k] for k in ("Ticker", "Identifiant_emetteur", "ID_document",
                                   "Tableau_source", "Ligne_source", "Periode_cloture",
                                   "Unite_source", "SHA256_source"))
        groupes.setdefault(cle, []).append(r)
    for lignes in groupes.values():
        if len({r["Valeur_source"] for r in lignes}) > 1:
            for r in lignes:
                r["Statut_raccordement"] = "EN_ATTENTE_DATA_CONFLIT_FACTUEL"
                r["Motif"] = "Valeurs divergentes pour le même fait primaire : transcription à vérifier"


def ecrire_couverture_pistes(resultat, donnees):
    """Couverture indicative, jamais une note, preuve certifiée ou admission SSI."""
    tickers = sorted({r["Ticker"] for r in resultat if r["Ticker"]})
    lignes = []
    for ticker in tickers:
        for bloc, libelles in BLOCS_PISTES.items():
            # Un même fait recopié deux fois ne double jamais la couverture.
            pistes = []
            deja_vus = set()
            for r in resultat:
                if not (r["Ticker"] == ticker
                        and r["Ligne_source"] in libelles
                        and r["Archive_source"]
                        and r["Statut_raccordement"] in STATUTS_ARCHIVE_INTEGRE):
                    continue
                cle = tuple(r[k] for k in ("Identifiant_emetteur", "ID_document",
                                           "Tableau_source", "Ligne_source", "Periode_cloture",
                                           "Unite_source", "Valeur_source", "SHA256_source"))
                if cle not in deja_vus:
                    deja_vus.add(cle)
                    pistes.append(r)
            identites = {r["Statut_raccordement"] for r in pistes}
            statut = ("EN_ATTENTE_DATA_IDENTITE_AMBIGUE"
                      if "EN_ATTENTE_DATA_IDENTITE_AMBIGUE" in identites
                      else "PISTES_ARCHIVEES_NON_CERTIFIEES" if pistes
                      else "EN_ATTENTE_DATA")
            def uniques(champ):
                return "|".join(sorted({r[champ] for r in pistes if r[champ]}))
            lignes.append({
                "Ticker": ticker, "Bloc_SSI": bloc,
                "Nombre_observations_pistes": len(pistes),
                "Nombre_documents_SHA256_distincts": len({r["SHA256_source"] for r in pistes}),
                "Lignes_source_pistes": uniques("Ligne_source"),
                "Periodes_pistes": uniques("Periode_cloture"),
                "SHA256_sources_pistes": uniques("SHA256_source"),
                "Statuts_raccordement": uniques("Statut_raccordement"),
                "Statut_bloc": statut,
                "Identite_SCE_certifiee": "NON",
                "Transcription_chiffres_verifiee": "NON",
                "Note_SSI": "MANQUANTE", "Note_MCPA": "MANQUANTE",
            })
    destination = donnees / "COUVERTURE_OBSERVATIONS_SSI_NON_CERTIFIEES.csv"
    tmp = destination.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COUVERTURE_COLONNES)
        w.writeheader()
        w.writerows(lignes)
    tmp.replace(destination)
    return lignes


def executer(racine=None, maintenant=None):
    racine = Path(racine or Path(__file__).resolve().parents[1]).resolve()
    maintenant = maintenant or datetime.now(timezone.utc)
    d = racine / "DONNEES"
    dossiers_path = d / "DOSSIERS_SSI_A_QUALIFIER.csv"
    if not dossiers_path.exists():
        raise RuntimeError("07Q doit produire les dossiers SSI avant 07Q3")
    # Un dictionnaire naïf écraserait silencieusement la première identité
    # d’un ticker dupliqué. Isoler ce ticker, sans bloquer les autres dossiers.
    dossiers = {}
    doublons = set()
    for dossier in lignes_csv(dossiers_path):
        ticker = dossier.get("Ticker", "").strip()
        if not ticker:
            continue
        if ticker in dossiers:
            doublons.add(ticker)
        else:
            dossiers[ticker] = dossier
    for ticker in doublons:
        dossiers[ticker] = {"Identifiant_emetteur_verifie": "CONFLIT_TICKER_DUPLIQUE"}
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
    isoler_conflits_factuels(resultat)
    destination = d / "OBSERVATIONS_FINANCIERES_SSI_NON_CERTIFIEES.csv"
    tmp = destination.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SORTIE)
        writer.writeheader()
        writer.writerows(resultat)
    tmp.replace(destination)
    couverture = ecrire_couverture_pistes(resultat, d)
    print("07Q3 couverture indicative SSI (sans preuve ni score):", len(couverture))
    bilan = {}
    for r in resultat:
        bilan[r["Statut_raccordement"]] = bilan.get(r["Statut_raccordement"], 0) + 1
    audit = d / "AUDIT_RACCORDEMENT_FAITS_SSI.csv"
    # Meme garantie de reprise que les sorties observations/couverture :
    # une panne pendant l'ecriture ne doit pas tronquer l'audit precedent.
    audit_tmp = audit.with_suffix(".tmp")
    with audit_tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=("Observations", "Dossiers", "SHA256_et_identite_concordants_non_certifies",
                                          "EN_ATTENTE_DATA", "Scores_attribues", "Statut"))
        w.writeheader()
        w.writerow({"Observations": len(resultat), "Dossiers": len({r["Ticker"] for r in resultat}),
                    "SHA256_et_identite_concordants_non_certifies": bilan.get("PISTE_FINANCIERE_SHA256_OK_NON_CERTIFIEE", 0),
                    "EN_ATTENTE_DATA": len(resultat) - bilan.get("PISTE_FINANCIERE_SHA256_OK_NON_CERTIFIEE", 0),
                    "Scores_attribues": 0, "Statut": "AUCUNE_ADMISSION_SSI_AUTOMATIQUE"})
    audit_tmp.replace(audit)
    print("07Q3 observations financières (sans score):", len(resultat), bilan)
    return resultat


if __name__ == "__main__":
    executer()

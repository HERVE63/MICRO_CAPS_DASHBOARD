#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09J : revue des accessions SEC absentes de l'index recent ou amendees.

Reutilise les captures 09F et les audits 09G/09H/09I. Pour une accession
ancienne, consulte uniquement les index historiques declares dans le JSON
submissions SEC deja archive, et conserve la reponse primaire avec SHA256.
Un 10-Q/A n'est JAMAIS assimile a un 10-Q pour valider un fait financier.
Aucune certification, note ou transaction. Les echecs sont non bloquants.
"""
import csv
import hashlib
import importlib.util
import json
import os
import re
import tempfile
import time
from collections import defaultdict, Counter
from datetime import datetime, timezone, date
from pathlib import Path

HERE = Path(__file__).resolve().parent
URL_ARCHIVE = re.compile(r"^https://data\.sec\.gov/submissions/(CIK\d{10}-submissions-\d{3}\.json)$")
COLONNES = ("CIK", "Accession", "Tickers", "Date_depot_fait",
            "Formulaire_companyfacts", "Formulaire_submissions",
            "Statut_initial_09I", "Statut_09J", "Date_depot_historique",
            "Formulaire_historique", "URL_source_historique",
            "SHA256_source_historique", "Statut_preuve")


def module(nom, fichier):
    spec = importlib.util.spec_from_file_location(nom, HERE / fichier)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def lire_csv(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def verifier_entrees(d):
    i = module("historique_09i", "09I_AUDITER_ACCESSIONS_SEC.py")
    f = module("historique_09f", "09F_PILOTE_SEC_US_5.py")
    d, mf, mg, mh = i.verifier(d)
    mi_path = d / "AUDIT_ACCESSIONS_09I/MANIFESTE_09I.json"
    mi = json.loads(mi_path.read_text(encoding="utf-8"))
    if (mi.get("Statut") != "RECOUPEMENT_DEPOTS_SEC_NON_CERTIFIANT"
            or any(mi.get(k) != 0 for k in ("Notes_SSI", "Notes_MCPA", "Arbitrages"))):
        raise ValueError("AUDIT_09I_NON_ADMISSIBLE")
    for k, p in (("SHA256_manifeste_09F", d / "MANIFESTE.json"),
                 ("SHA256_manifeste_09G", d / "NORMALISATION_07U_07V/MANIFESTE_REPLAY.json"),
                 ("SHA256_manifeste_09H", d / "AUDIT_PERIODES_09H/MANIFESTE_09H.json")):
        if mi.get(k) != sha(p):
            raise ValueError("LIAISON_MANIFESTES_INVALIDE_" + k)
    for rel, digest in mi.get("Fichiers_SHA256", {}).items():
        i.fichier_verifie(mi_path.parent, rel, digest)
    if not mi.get("Fichiers_SHA256"):
        raise ValueError("AUDIT_09I_SANS_PREUVES")
    lignes = lire_csv(mi_path.parent / "REVUE_ACCESSIONS_SEC_09I.csv")
    if len(lignes) != sum(x["Observations"] for x in mi["Audits"].values()):
        raise ValueError("DETAIL_09I_INCOMPLET")
    return f, mf, mi, lignes


def extraire_cibles(lignes):
    statuts = {"EN_ATTENTE_DATA_FORMULAIRE_DIVERGENT",
               "EN_ATTENTE_DATA_ACCESSION_HORS_INDEX_RECENT"}
    groupes = defaultdict(list)
    for r in lignes:
        if r["Statut_accession_09I"] in statuts:
            groupes[(r["CIK"], r["Accession"])].append(r)
    cibles = []
    for (cik, accn), rows in sorted(groupes.items()):
        if not re.fullmatch(r"\d{10}", cik) or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accn):
            raise ValueError("IDENTIFIANT_ACCESSION_INVALIDE")
        valeurs = {(r["Date_depot_fait"], r["Formulaire"],
                    r["Formulaire_submissions"], r["Statut_accession_09I"]) for r in rows}
        if len(valeurs) != 1:
            statut = "EN_ATTENTE_DATA_DIVERGENCE_INTER_HORIZONS"
        else:
            statut = ""
        date_fait, form_fait, form_sub, initial = sorted(valeurs)[0]
        cibles.append({"CIK": cik, "Accession": accn,
                       "Tickers": ",".join(sorted({r["Ticker"] for r in rows})),
                       "Date_depot_fait": date_fait, "Formulaire_companyfacts": form_fait,
                       "Formulaire_submissions": form_sub, "Statut_initial_09I": initial,
                       "Statut_09J": statut, "Date_depot_historique": "",
                       "Formulaire_historique": "", "URL_source_historique": "",
                       "SHA256_source_historique": "",
                       "Statut_preuve": "A_VERIFIER_IDENTITE_ET_PERIODE"})
    return cibles


def extraire_fichiers_historiques(d, mf, cik, date_fait):
    sources = [s for s in mf["Sources"]
               if s.get("URL") == "https://data.sec.gov/submissions/CIK" + cik + ".json"]
    if len(sources) != 1:
        return [], "EN_ATTENTE_DATA_SUBMISSIONS_NON_UNIQUES"
    brut = (d / sources[0]["Fichier_brut"]).resolve()
    if not brut.is_relative_to(d.resolve()) or sha(brut) != sources[0]["SHA256"]:
        raise ValueError("SHA256_SUBMISSIONS_INVALIDE")
    obj = json.loads(brut.read_bytes())
    if str(obj.get("cik", "")).zfill(10) != cik:
        raise ValueError("CIK_SUBMISSIONS_INVALIDE")
    fichiers = obj.get("filings", {}).get("files", [])
    if not isinstance(fichiers, list):
        return [], "EN_ATTENTE_DATA_SCHEMA_INDEX_HISTORIQUE"
    candidats = []
    for entry in fichiers:
        if not isinstance(entry, dict):
            continue
        nom = entry.get("name", "")
        if (isinstance(nom, str) and URL_ARCHIVE.fullmatch(
                "https://data.sec.gov/submissions/" + nom)
                and entry.get("filingFrom", "9999-12-31") <= date_fait
                <= entry.get("filingTo", "0000-01-01")):
            candidats.append("https://data.sec.gov/submissions/" + nom)
    candidats = sorted(set(candidats))
    if not candidats:
        return [], "EN_ATTENTE_DATA_INDEX_HISTORIQUE_NON_REPERTORIE"
    if len(candidats) > 3:
        return [], "EN_ATTENTE_DATA_INDEX_HISTORIQUE_AMBIGU"
    return candidats, ""


def executer(dossier, fetcher=None, agent=None, pause=time.sleep, maintenant=None):
    d = Path(dossier).resolve()
    f, mf, mi, lignes = verifier_entrees(d)
    cible = d / "AUDIT_HISTORIQUE_09J"
    if cible.exists():
        raise FileExistsError("AUDIT_09J_EXISTANT_NE_PAS_ECRASER")
    fetcher = fetcher or f.lire_json
    agent = agent if agent is not None else os.getenv("SEC_USER_AGENT", "")
    horodatage = maintenant or datetime.now(timezone.utc)
    if horodatage.tzinfo is None or horodatage.utcoffset() is None:
        raise ValueError("HORODATAGE_UTC_REQUIS")
    cibles = extraire_cibles(lignes)
    cache, captures = {}, []
    with tempfile.TemporaryDirectory(prefix=".09J_", dir=d) as tmp:
        travail = Path(tmp)
        (travail / "BRUTS_HISTORIQUES").mkdir()
        for row in cibles:
            if row["Statut_09J"]:
                continue
            if row["Statut_initial_09I"] == "EN_ATTENTE_DATA_FORMULAIRE_DIVERGENT":
                if (row["Formulaire_companyfacts"] == "10-Q"
                        and row["Formulaire_submissions"] == "10-Q/A"):
                    row["Statut_09J"] = "AMENDEMENT_10_Q_A_REPERE_NON_CERTIFIANT"
                else:
                    row["Statut_09J"] = "EN_ATTENTE_DATA_FORMULAIRE_A_EXAMINER"
                continue
            urls, erreur = extraire_fichiers_historiques(
                d, mf, row["CIK"], row["Date_depot_fait"])
            if erreur:
                row["Statut_09J"] = erreur
                continue
            occurrences = set()
            for url in urls:
                if url not in cache:
                    try:
                        f.verifier_url(url)
                        obj, brut = fetcher(url, agent)
                        if not isinstance(obj, dict) or not isinstance(brut, bytes) or json.loads(brut) != obj:
                            raise ValueError("REPONSE_SEC_BRUT_DIVERGENT")
                        if not brut or len(brut) > 20_000_000:
                            raise ValueError("TAILLE_SEC_INVALIDE")
                        digest = hashlib.sha256(brut).hexdigest()
                        chemin = "BRUTS_HISTORIQUES/" + digest + ".json"
                        (travail / chemin).write_bytes(brut)
                        cache[url] = (obj, digest, chemin, "")
                        captures.append({"URL": url, "SHA256": digest, "Fichier_brut": chemin,
                                         "Date_collecte_UTC": horodatage.isoformat()})
                        pause(0.35)
                    except Exception as exc:
                        cache[url] = (None, "", "", "EN_ATTENTE_DATA_SEC_" + type(exc).__name__)
                obj, digest, chemin, echec = cache[url]
                if echec:
                    row["Statut_09J"] = echec
                    continue
                rec = obj.get("accessionNumber", [])
                dates = obj.get("filingDate", [])
                forms = obj.get("form", [])
                if not all(isinstance(x, list) for x in (rec, dates, forms)) or len({len(x) for x in (rec, dates, forms)}) != 1:
                    row["Statut_09J"] = "EN_ATTENTE_DATA_SCHEMA_HISTORIQUE"
                    continue
                for accn, dep, form in zip(rec, dates, forms):
                    if accn == row["Accession"]:
                        occurrences.add((str(dep), str(form), url, digest))
            if len(occurrences) == 1:
                dep, form, url, digest = next(iter(occurrences))
                row["Date_depot_historique"] = dep
                row["Formulaire_historique"] = form
                row["URL_source_historique"] = url
                row["SHA256_source_historique"] = digest
                if dep != row["Date_depot_fait"]:
                    row["Statut_09J"] = "EN_ATTENTE_DATA_DATE_HISTORIQUE_DIVERGENTE"
                elif form != row["Formulaire_companyfacts"]:
                    row["Statut_09J"] = "EN_ATTENTE_DATA_FORMULAIRE_HISTORIQUE_DIVERGENT"
                else:
                    row["Statut_09J"] = "DEPOT_HISTORIQUE_RECOUPE_NON_CERTIFIANT"
            elif len(occurrences) > 1:
                row["Statut_09J"] = "EN_ATTENTE_DATA_DEPOT_HISTORIQUE_AMBIGU"
            elif not row["Statut_09J"]:
                row["Statut_09J"] = "EN_ATTENTE_DATA_ACCESSION_HISTORIQUE_ABSENTE"
        with (travail / "REVUE_HISTORIQUE_SEC_09J.csv").open("w", newline="", encoding="utf-8") as fd:
            writer = csv.DictWriter(fd, fieldnames=COLONNES)
            writer.writeheader()
            writer.writerows(cibles)
        bilan = {"Statut": "AUDIT_HISTORIQUE_NON_CERTIFIANT",
                 "Date_collecte_UTC": horodatage.isoformat(),
                 "Source_manifeste_09I_SHA256": sha(d / "AUDIT_ACCESSIONS_09I/MANIFESTE_09I.json"),
                 "Accessions_distinctes": len(cibles),
                 "Statuts": dict(sorted(Counter(r["Statut_09J"] for r in cibles).items())),
                 "Captures": captures, "Notes_SSI": 0, "Notes_MCPA": 0, "Arbitrages": 0,
                 "Fichiers_SHA256": {str(p.relative_to(travail)): sha(p)
                                    for p in sorted(travail.rglob("*")) if p.is_file()}}
        (travail / "MANIFESTE_09J.json").write_text(
            json.dumps(bilan, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        os.replace(travail, cible)
    print("09J", json.dumps({"accessions": len(cibles), "statuts": bilan["Statuts"],
                              "captures": len(captures)}, ensure_ascii=False))
    return bilan


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: 09J_REVOIR_HISTORIQUE_SEC.py DOSSIER_09F")
    executer(sys.argv[1])

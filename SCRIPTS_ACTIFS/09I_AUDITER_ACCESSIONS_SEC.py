#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09I : recouper les accessions des conflits 09H avec les submissions SEC archivées.

Ne télécharge rien : réutilise 09F, 09G et 09H, vérifie leurs SHA256 et
conserve chaque dossier incertain en EN_ATTENTE_DATA. Une concordance SEC
ne certifie ni l'identité SCE, ni les faits financiers, ni un score.
"""
import csv
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

COLONNES = (
    "Horizon", "Ticker", "CIK", "Concept", "Tag_SEC", "Taxonomie_SEC",
    "Debut_periode", "Fin_periode", "Accession", "Formulaire",
    "Date_depot_fait", "Valeur", "Statut_groupe_09H",
    "Statut_accession_09I", "Date_depot_submissions",
    "Formulaire_submissions", "URL_depot_indicative_non_consultee",
    "URL_source_submissions", "SHA256_submissions", "SHA256_companyfacts",
    "Statut_preuve",
)
ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")
DOCUMENT = re.compile(r"^[A-Za-z0-9_.-]+$")
URL_SUB = re.compile(r"^https://data\.sec\.gov/submissions/CIK(\d{10})\.json$")
URL_FACT = re.compile(r"^https://data\.sec\.gov/api/xbrl/companyfacts/CIK(\d{10})\.json$")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fichier_verifie(base, rel, attendu):
    cible = (base / rel).resolve()
    if not cible.is_relative_to(base.resolve()) or not cible.is_file() or sha(cible) != attendu:
        raise ValueError("SHA256_INVALIDE: " + str(rel))
    return cible


def csv_lignes(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def verifier(dossier):
    # Chaque couche déjà validée reste immuable ; aucun téléchargement.
    d = Path(dossier).resolve()
    f9 = d / "MANIFESTE.json"
    g9 = d / "NORMALISATION_07U_07V/MANIFESTE_REPLAY.json"
    h9 = d / "AUDIT_PERIODES_09H/MANIFESTE_09H.json"
    mf, mg, mh = [json.loads(p.read_text(encoding="utf-8")) for p in (f9, g9, h9)]
    if (mf.get("Statut") != "PILOTE_DIAGNOSTIQUE_NON_CERTIFIANT"
            or mg.get("Statut") != "REPLAY_SEC_NON_CERTIFIANT"
            or mh.get("Statut") != "AUDIT_PERIODES_NON_CERTIFIANT"):
        raise ValueError("STATUT_SOURCE_NON_ADMISSIBLE")
    for m in (mg, mh):
        if any(m.get(k) != 0 for k in ("Notes_SSI", "Notes_MCPA", "Arbitrages")):
            raise ValueError("PROMOTION_SCORE_INTERDITE")
    if mh.get("Source_manifeste_09G_SHA256") != sha(g9):
        raise ValueError("SHA256_LIAISON_09G_09H_INVALIDE")
    for base, manifest in ((d, mf), (g9.parent, mg), (h9.parent, mh)):
        for rel, digest in manifest.get("Fichiers_SHA256", {}).items():
            fichier_verifie(base, rel, digest)
    if not mf.get("Sources") or not mg.get("Sources_reutilisees"):
        raise ValueError("MANIFESTE_SOURCE_INCOMPLET")
    for source in mf["Sources"]:
        fichier_verifie(d, source["Fichier_brut"], source["SHA256"])
    return d, mf, mg, mh


def indexer_submissions(d, mf):
    """Les dossiers absents/ambigus restent non bloquants pour les autres."""
    captures = defaultdict(list)
    for s in mf["Sources"]:
        match = URL_SUB.fullmatch(s["URL"])
        if match:
            captures[match.group(1)].append(s)
    result = {}
    for cik, sources in captures.items():
        if len({(s["URL"], s["SHA256"]) for s in sources}) != 1:
            result[cik] = ("EN_ATTENTE_DATA_SUBMISSIONS_AMBIGUES", {}, "", "")
            continue
        s = sources[0]
        try:
            obj = json.loads((d / s["Fichier_brut"]).read_text(encoding="utf-8"))
            if str(obj.get("cik", "")).zfill(10) != cik:
                raise ValueError("CIK_SUBMISSIONS_DIVERGENT")
            rec = obj.get("filings", {}).get("recent", {})
            champs = ("accessionNumber", "filingDate", "form", "primaryDocument")
            listes = [rec.get(k) for k in champs]
            if not all(isinstance(x, list) for x in listes) or len({len(x) for x in listes}) != 1:
                raise ValueError("SCHEMA_SUBMISSIONS_INCOMPLET")
            index = defaultdict(set)
            for accn, filed, form, doc in zip(*listes):
                if isinstance(accn, str) and ACCESSION.fullmatch(accn):
                    index[accn].add((str(filed), str(form), str(doc)))
            result[cik] = ("OK", index, s["URL"], s["SHA256"])
        except (ValueError, TypeError, KeyError, AttributeError):
            result[cik] = ("EN_ATTENTE_DATA_SUBMISSIONS_INEXPLOITABLES", {}, s["URL"], s["SHA256"])
    return result


def rapprocher(r, mg, index, horizon, limite):
    ticker = r.get("Ticker", "")
    lien = mg["Sources_reutilisees"].get(ticker)
    if not lien or not URL_FACT.fullmatch(lien.get("URL", "")):
        raise ValueError("SOURCE_COMPANYFACTS_INVALIDE")
    cik = URL_FACT.fullmatch(lien["URL"]).group(1)
    if r.get("CIK") != cik or r.get("SHA256_brut_SEC") != lien["SHA256"]:
        raise ValueError("CIK_OU_SHA256_FAIT_DIVERGENT")
    if r.get("Horizon") != horizon or r.get("Statut_preuve") != "A_VERIFIER_IDENTITE_ET_PERIODE":
        raise ValueError("PREUVE_09H_NON_ADMISSIBLE")
    if r.get("Statut_groupe") not in ("EN_ATTENTE_DATA_CONFLIT_ALIAS", "EN_ATTENTE_DATA_REVISION"):
        raise ValueError("GROUPE_09H_NON_ADMISSIBLE")
    if date.fromisoformat(r["Date_depot"]) > limite:
        raise ValueError("FUITE_TEMPORELLE_ACCESSION")
    etat, entries, source_url, digest = index.get(
        cik, ("EN_ATTENTE_DATA_SUBMISSIONS_ABSENTES", {}, "", ""))
    accn = r.get("Accession", "")
    statut, date_sub, form_sub, url = etat, "", "", ""
    if etat == "OK":
        if not ACCESSION.fullmatch(accn):
            statut = "EN_ATTENTE_DATA_ACCESSION_INVALIDE"
        elif accn not in entries:
            statut = "EN_ATTENTE_DATA_ACCESSION_HORS_INDEX_RECENT"
        elif len(entries[accn]) != 1:
            statut = "EN_ATTENTE_DATA_ACCESSION_AMBIGUE"
        else:
            date_sub, form_sub, doc = next(iter(entries[accn]))
            if date_sub != r["Date_depot"]:
                statut = "EN_ATTENTE_DATA_DATE_DEPOT_DIVERGENTE"
            elif form_sub != r.get("Formulaire", ""):
                statut = "EN_ATTENTE_DATA_FORMULAIRE_DIVERGENT"
            else:
                statut = "DEPOT_SEC_CONCORDE_NON_CERTIFIANT"
                if DOCUMENT.fullmatch(doc):
                    url = ("https://www.sec.gov/Archives/edgar/data/"
                           + str(int(cik)) + "/" + accn.replace("-", "") + "/" + doc)
    return dict(zip(COLONNES, (
        horizon, ticker, cik, r.get("Concept", ""), r.get("Tag_SEC", ""),
        r.get("Taxonomie_SEC", ""), r.get("Debut_periode", ""),
        r.get("Fin_periode", ""), accn, r.get("Formulaire", ""),
        r["Date_depot"], r.get("Valeur", ""), r["Statut_groupe"],
        statut, date_sub, form_sub, url, source_url, digest,
        lien["SHA256"], "A_VERIFIER_IDENTITE_ET_PERIODE",
    )))


def executer(dossier):
    d, mf, mg, mh = verifier(dossier)
    destination = d / "AUDIT_ACCESSIONS_09I"
    if destination.exists():
        raise FileExistsError("AUDIT_09I_EXISTANT_NE_PAS_ECRASER")
    index = indexer_submissions(d, mf)
    details = csv_lignes(d / "AUDIT_PERIODES_09H/DETAIL_CONFLITS_REVISIONS_09H.csv")
    sorties, audits = [], {}
    for horizon, limite in (("T0", date.fromisoformat(mg["T0"])),
                            ("COURANT", date.fromisoformat(mg["Date_collecte"]))):
        lignes = [r for r in details if r.get("Horizon") == horizon]
        attendu = mh["Audits"][horizon]["Observations_a_revoir"]
        if len(lignes) != attendu:
            raise ValueError("DETAIL_09H_INCOMPLET_" + horizon)
        resultat = [rapprocher(r, mg, index, horizon, limite) for r in lignes]
        sorties.extend(resultat)
        audits[horizon] = {"Observations": len(resultat),
                           "Statuts": dict(sorted(Counter(
                               r["Statut_accession_09I"] for r in resultat).items())),
                           "Certifications_SSI": 0, "Notes_MCPA": 0, "Arbitrages": 0}
    if len(sorties) != len(details):
        raise ValueError("HORIZON_09H_INCONNU")
    with tempfile.TemporaryDirectory(prefix=".09I_", dir=d) as tmp:
        p = Path(tmp)
        with (p / "REVUE_ACCESSIONS_SEC_09I.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLONNES)
            w.writeheader()
            w.writerows(sorties)
        (p / "AUDIT_ACCESSIONS_09I.json").write_text(
            json.dumps(audits, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        manifest = {
            "Statut": "RECOUPEMENT_DEPOTS_SEC_NON_CERTIFIANT",
            "SHA256_manifeste_09F": sha(d / "MANIFESTE.json"),
            "SHA256_manifeste_09G": sha(d / "NORMALISATION_07U_07V/MANIFESTE_REPLAY.json"),
            "SHA256_manifeste_09H": sha(d / "AUDIT_PERIODES_09H/MANIFESTE_09H.json"),
            "Audits": audits, "Notes_SSI": 0, "Notes_MCPA": 0, "Arbitrages": 0,
            "Fichiers_SHA256": {f.name: sha(f) for f in p.iterdir() if f.is_file()},
        }
        (p / "MANIFESTE_09I.json").write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        os.replace(p, destination)
    print("09I", json.dumps(audits, ensure_ascii=False, sort_keys=True))
    return manifest


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: 09I_AUDITER_ACCESSIONS_SEC.py DOSSIER_09F")
    executer(sys.argv[1])

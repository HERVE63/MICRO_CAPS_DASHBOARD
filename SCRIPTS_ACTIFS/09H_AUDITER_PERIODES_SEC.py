#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09H : audit conservateur des périodes SEC issues du replay 09G.

Réutilise EXCLUSIVEMENT les fichiers 07U/07V archivés par 09G et leurs SHA256.
Ne crée ni preuve SSI certifiée, ni score, ni ordre. Un cumul semestriel ou
neuf mois n'est jamais converti artificiellement en trimestre indépendant.
Les révisions et les alias contradictoires restent EN_ATTENTE_DATA.
"""
import csv
import hashlib
import importlib.util
import json
import os
import tempfile
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "SCRIPTS_ACTIFS" / "07V_NORMALISER_FAITS_SEC.py"
TITRES = ("IDN", "INFU", "OSS", "CXDO", "LWAY")
COLONNES = ("Horizon", "Ticker", "CIK", "Concept", "Unite", "Cadence",
            "Debut_periode", "Fin_periode", "Nb_alias", "Nb_valeurs_distinctes",
            "Nb_observations_brutes", "Nb_revisions_meme_tag",
            "Date_depot_max", "SHA256_brut_SEC", "Statut")


def empreinte(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def lire_csv(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def date_iso(s):
    return date.fromisoformat(s)


def valeur(s):
    try:
        n = Decimal(s)
    except (InvalidOperation, TypeError):
        raise ValueError("VALEUR_FINANCIERE_NON_NUMERIQUE")
    if not n.is_finite():
        raise ValueError("VALEUR_FINANCIERE_NON_FINIE")
    return n


def charger_module_flux():
    spec = importlib.util.spec_from_file_location("historique_07v_flux", V)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.FLUX


def verifier_entrees(dossier):
    base = dossier / "NORMALISATION_07U_07V"
    manifest = base / "MANIFESTE_REPLAY.json"
    m = json.loads(manifest.read_text(encoding="utf-8"))
    if m.get("Statut") != "REPLAY_SEC_NON_CERTIFIANT" or any(
        m.get(k) != 0 for k in ("Notes_SSI", "Notes_MCPA", "Arbitrages")
    ):
        raise ValueError("REPLAY_NON_ADMISSIBLE")
    fichiers = m.get("Fichiers_SHA256", {})
    if not fichiers or not m.get("Sources_reutilisees"):
        raise ValueError("MANIFESTE_REPLAY_INCOMPLET")
    for relatif, digest in fichiers.items():
        p = (base / relatif).resolve()
        if not p.is_relative_to(base.resolve()) or not p.is_file() or empreinte(p) != digest:
            raise ValueError("SHA256_REPLAY_INVALIDE: " + relatif)
    return base, manifest, m


def analyser_horizon(base, m, label, limite, flux):
    raw_path = base / label / "FAITS_FINANCIERS_SEC_SSI.csv"
    cmp_path = base / label / "FAITS_SEC_COMPARABLES_SSI.csv"
    raw = lire_csv(raw_path)
    comparables = lire_csv(cmp_path)
    liens = m["Sources_reutilisees"]
    def controle(r):
        ticker = r.get("Ticker", "")
        if ticker not in liens or r.get("SHA256_brut_SEC") != liens[ticker]["SHA256"]:
            raise ValueError("PROVENANCE_FAIT_INVALIDE")
        if r.get("Statut_preuve") != "A_VERIFIER_IDENTITE_ET_PERIODE":
            raise ValueError("PROMOTION_PREUVE_INTERDITE")
        if date_iso(r["Date_depot"]) > limite or date_iso(r["Fin_periode"]) > date_iso(r["Date_depot"]):
            raise ValueError("FUITE_TEMPORELLE")
        if r.get("Debut_periode") and date_iso(r["Debut_periode"]) > date_iso(r["Fin_periode"]):
            raise ValueError("PERIODE_INVERSEE")
        valeur(r["Valeur"])
    for r in raw + comparables:
        controle(r)
    ident = ("Ticker", "CIK", "Concept", "Tag_SEC", "Taxonomie_SEC", "Unite",
             "Debut_periode", "Fin_periode", "Date_depot", "Accession", "Valeur")
    signatures = {tuple(r.get(k, "") for k in ident) for r in raw}
    for r in comparables:
        if tuple(r.get(k, "") for k in ident) not in signatures:
            raise ValueError("FAIT_COMPARABLE_ABSENT_DES_BRUTS")
    def cle(r, cadence):
        return (r["Ticker"], r["CIK"], r["Concept"], r["Unite"],
                cadence, r["Debut_periode"], r["Fin_periode"])
    groupes = defaultdict(list)
    for r in comparables:
        if r.get("Cadence") not in ("ANNUEL", "TRIMESTRIEL", "INSTANTANE"):
            raise ValueError("CADENCE_NON_INDEPENDANTE")
        groupes[cle(r, r["Cadence"])].append(r)
    raw_par_cle = defaultdict(list)
    cumuls_exclus = 0
    for r in raw:
        deb = r.get("Debut_periode", "")
        if r["Concept"] in flux and deb:
            duree = (date_iso(r["Fin_periode"]) - date_iso(deb)).days
            if 110 < duree < 330:
                cumuls_exclus += 1
        for cadence in ("ANNUEL", "TRIMESTRIEL", "INSTANTANE"):
            k = cle(r, cadence)
            if k in groupes:
                raw_par_cle[k].append(r)
    lignes = []
    compteurs = defaultdict(int)
    for k, obs in sorted(groupes.items()):
        historiques = raw_par_cle[k]
        valeurs = {valeur(r["Valeur"]) for r in obs}
        par_tag = defaultdict(set)
        for r in historiques:
            par_tag[(r["Tag_SEC"], r.get("Taxonomie_SEC", ""))].add(valeur(r["Valeur"]))
        revisions = sum(1 for valeurs_tag in par_tag.values() if len(valeurs_tag) > 1)
        if len(valeurs) > 1:
            statut = "EN_ATTENTE_DATA_CONFLIT_ALIAS"
        elif revisions:
            statut = "EN_ATTENTE_DATA_REVISION"
        else:
            statut = "PISTE_PERIODE_INDEPENDANTE_NON_CERTIFIEE"
        compteurs[statut] += 1
        lignes.append(dict(zip(COLONNES, (
            label, k[0], k[1], k[2], k[3], k[4], k[5], k[6],
            len({(r["Tag_SEC"], r.get("Taxonomie_SEC", "")) for r in obs}),
            len(valeurs), len(historiques), revisions,
            max(r["Date_depot"] for r in historiques),
            liens[k[0]]["SHA256"], statut
        ))))
    return lignes, {
        "Faits_bruts": len(raw), "Faits_comparables_07V": len(comparables),
        "Periodes_distinctes": len(lignes),
        "Cumuls_intermediaires_bruts_non_convertis": cumuls_exclus,
        "Statuts": dict(compteurs),
        "Titres_sans_periode": sorted(set(TITRES) - {r["Ticker"] for r in lignes}),
        "Notes_SSI": 0, "Notes_MCPA": 0, "Arbitrages": 0
    }


def executer(dossier):
    dossier = Path(dossier).resolve()
    base, source_manifest, m = verifier_entrees(dossier)
    destination = dossier / "AUDIT_PERIODES_09H"
    if destination.exists():
        raise FileExistsError("AUDIT_09H_EXISTANT_NE_PAS_ECRASER")
    flux = charger_module_flux()
    resultats, audits = [], {}
    for label, limite in (("T0", date_iso(m["T0"])),
                          ("COURANT", date_iso(m["Date_collecte"]))):
        lignes, audit = analyser_horizon(base, m, label, limite, flux)
        resultats.extend(lignes)
        audits[label] = audit
    with tempfile.TemporaryDirectory(prefix=".09H_", dir=dossier) as tmp:
        p = Path(tmp)
        with (p / "PERIODES_SEC_09H.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLONNES)
            w.writeheader()
            w.writerows(resultats)
        (p / "AUDIT_PERIODES_09H.json").write_text(
            json.dumps(audits, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        manifeste = {
            "Statut": "AUDIT_PERIODES_NON_CERTIFIANT",
            "Source_manifeste_09G_SHA256": empreinte(source_manifest),
            "Date_collecte": m["Date_collecte"],
            "Audits": audits,
            "Notes_SSI": 0, "Notes_MCPA": 0, "Arbitrages": 0,
            "Fichiers_SHA256": {f.name: empreinte(f) for f in p.iterdir() if f.is_file()}
        }
        (p / "MANIFESTE_09H.json").write_text(
            json.dumps(manifeste, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        os.replace(p, destination)
    print("09H périodes:", {k: v["Periodes_distinctes"] for k, v in audits.items()},
          "zéro score, zéro arbitrage")
    return manifeste


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: 09H_AUDITER_PERIODES_SEC.py DOSSIER_09F")
    executer(sys.argv[1])

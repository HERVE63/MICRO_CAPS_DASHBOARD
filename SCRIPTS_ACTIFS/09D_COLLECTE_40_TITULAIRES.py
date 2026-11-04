# -*- coding: utf-8 -*-
"""Observations EODHD des 40 titulaires, sans admission SSI/MCPA.

EODHD est un fournisseur de données, PAS une preuve réglementaire primaire.
Un échec par titre ne bloque jamais les 39 autres. Les réponses conservées
sont des instantanés JSON canoniques, vérifiables par SHA256, en artefact CI
et non des preuves primaires validées.
"""
from collections import Counter
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
import json
import math
import os
import re
from urllib.parse import quote

import pandas as pd
import requests

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
OUT = BASE / "DONNEES/COLLECTE_DIRECTE_40_TITULAIRES.csv"
HIST = BASE / "AUDITS/HISTORIQUE_COLLECTES_HEBDOMADAIRES"


def _ecrire_atomique(path, contenu):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(contenu)
    tmp.replace(path)


def collecter():
    positions = pd.read_csv(SRC, dtype={"Ticker": str}, keep_default_na=False)
    if len(positions) != 40 or positions["Ticker"].nunique() != 40:
        raise RuntimeError("Inventaire des 40 positions incoherent")
    api = os.environ.get("EODHD_API_TOKEN") or os.environ.get("EODHD_API_KEY")
    debut = datetime.now(timezone.utc).isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    dossier = HIST / ("COLLECTE_40_" + stamp)
    brut = dossier / "REPONSES_FOURNISSEUR"
    records = []
    fichiers = {}
    for _, p in positions.iterrows():
        ticker = str(p["Ticker"]).strip()
        # Les cinq titulaires US de la cohorte T0 sont stockés sans suffixe
        # (IDN, INFU, OSS, CXDO, LWAY), tandis que l'API EODHD attend .US.
        # Ne jamais changer le ticker officiel de la position ni ajouter
        # .US à une cotation déjà suffixée (.TO, .V, .PA, .L, etc.).
        ticker_eodhd = (ticker + ".US" if str(p["Devise"]).upper() == "USD"
                        and re.fullmatch(r"[A-Za-z0-9-]+", ticker) else ticker)
        # Le suffixe Yahoo .L n'est pas le code EODHD de Londres (.LSE).
        # Correspondance de place seulement : elle ne certifie pas l'ISIN.
        if ticker_eodhd.upper().endswith(".L"):
            ticker_eodhd = ticker_eodhd[:-2] + ".LSE"
        row = {
            "ID_position": p["ID_position"], "Societe": p["Societe"],
            "Ticker": ticker, "Ticker_requete_EODHD": ticker_eodhd,
            "Devise": p["Devise"],
            "Horodatage_UTC": datetime.now(timezone.utc).isoformat(),
            "Source": "EODHD fundamentals (fournisseur secondaire)",
            "Endpoint_sans_secret": "/api/fundamentals/" + ticker_eodhd,
            "Statut": "EN_ATTENTE_CLE" if not api else "EN_ATTENTE_DATA_FOURNISSEUR",
            "Statut_identite": "NON_CERTIFIEE",
            "Preuve_primaire_validee": "NON", "Score_SSI": "MANQUANTE",
            "Score_MCPA": "MANQUANTE",
        }
        if api:
            try:
                response = requests.get(
                    "https://eodhd.com/api/fundamentals/" + ticker_eodhd,
                    params={"api_token": api, "fmt": "json"}, timeout=25,
                )
                row["HTTP_statut"] = response.status_code
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict) or not isinstance(data.get("General"), dict):
                    row["Statut"] = "REPONSE_NON_EXPLOITABLE"
                else:
                    # Le hash porte sur le JSON canonique réellement archivé,
                    # pas sur une représentation HTTP impossible à reproduire.
                    contenu = json.dumps(
                        data, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":"), allow_nan=False,
                    ).encode("utf-8")
                    empreinte = sha256(contenu).hexdigest()
                    # Identifiant de position pour éviter toute collision de noms.
                    nom = str(p["ID_position"]) + ".json"
                    chemin = brut / nom
                    _ecrire_atomique(chemin, contenu)
                    fichiers[str(chemin.relative_to(dossier))] = empreinte
                    g = data["General"]
                    code = str(g.get("Code") or "").strip()
                    # La concordance du code n'est PAS une identité émetteur.
                    code_attendu = ticker.split(".")[0].upper()
                    code_ok = bool(code) and code.upper() == code_attendu
                    row.update({
                        "SHA256_JSON_canonique": empreinte,
                        "Archive_JSON": str(chemin.relative_to(BASE)),
                        "Code_EODHD": code, "Exchange_EODHD": g.get("Exchange"),
                        "ISIN_fournisseur_non_certifie": g.get("ISIN"),
                        "Statut": ("OBSERVATION_FOURNISSEUR_NON_CERTIFIEE"
                                   if code_ok else "EN_ATTENTE_DATA_IDENTITE"),
                        "Statut_identite": ("PISTE_CODE_CONCORDANT_NON_CERTIFIEE"
                                           if code_ok else "CODE_DIVERGENT_OU_ABSENT"),
                        "MarketCapitalization": (data.get("Highlights") or {}).get("MarketCapitalization"),
                        "RevenueTTM": (data.get("Highlights") or {}).get("RevenueTTM"),
                        "EBITDA": (data.get("Highlights") or {}).get("EBITDA"),
                    })
            except (requests.RequestException, ValueError, TypeError) as exc:
                # Ne jamais enregistrer str(exc): une URL peut contenir la clé.
                row["Erreur_type"] = type(exc).__name__
        # Plan B indépendant : le compte EODHD peut autoriser les cours EOD
        # (HTTP 200) tout en refusant /fundamentals (HTTP 403). Le refus des
        # fondamentaux ne doit ni masquer les cours ni inventer une note.
        row["Statut_cours"] = "EN_ATTENTE_CLE" if not api else "EN_ATTENTE_DATA_COURS"
        if api:
            try:
                cours_response = requests.get(
                    "https://eodhd.com/api/eod/" + ticker_eodhd,
                    params={"api_token": api, "fmt": "json",
                            "from": (datetime.now(timezone.utc) - timedelta(days=21)).date().isoformat()},
                    timeout=25,
                )
                row["HTTP_cours"] = cours_response.status_code
                cours_response.raise_for_status()
                cours = cours_response.json()
                if isinstance(cours, list) and cours:
                    seances = []
                    for point in cours:
                        if not isinstance(point, dict):
                            continue
                        try:
                            date = datetime.strptime(str(point.get("date", "")), "%Y-%m-%d").date()
                            valeur = float(point.get("adjusted_close"))
                        except (TypeError, ValueError):
                            continue
                        if date <= datetime.now(timezone.utc).date() and math.isfinite(valeur) and valeur > 0:
                            seances.append((date, valeur))
                    if seances:
                        # Une même date peut apparaître deux fois dans une
                        # réponse fournisseur. max((date, prix)) choisissait
                        # silencieusement le prix le plus élevé : cela ne
                        # constitue PAS une clôture univoque.
                        dernier = max(date for date, _ in seances)
                        valeurs = {prix for date, prix in seances if date == dernier}
                        contenu = json.dumps(cours, ensure_ascii=False, sort_keys=True,
                                             separators=(",", ":"), allow_nan=False).encode("utf-8")
                        chemin = brut / (str(p["ID_position"]) + "_EOD.json")
                        _ecrire_atomique(chemin, contenu)
                        empreinte = sha256(contenu).hexdigest()
                        fichiers[str(chemin.relative_to(dossier))] = empreinte
                        row.update({
                            "Date_cours": dernier.isoformat(),
                            "SHA256_EOD_JSON": empreinte,
                            "Archive_EOD_JSON": str(chemin.relative_to(BASE)),
                        })
                        if len(valeurs) != 1:
                            # Archiver la réponse pour audit, mais ne publier
                            # aucun cours arbitraire. Le dossier voisin continue.
                            row["Statut_cours"] = "EN_ATTENTE_DATA_COURS_CONFLIT"
                            row["Anomalie_cours"] = "CLOTURE_MULTIPLE_CONTRADICTOIRE"
                        else:
                            row["Cours_ajuste_fournisseur"] = next(iter(valeurs))
                            row["Statut_cours"] = "COURS_FOURNISSEUR_NON_CERTIFIE"
                            if row["Statut"] != "OBSERVATION_FOURNISSEUR_NON_CERTIFIEE":
                                row["Statut"] = "OBSERVATION_COURS_SEULEMENT_NON_CERTIFIEE"
            except (requests.RequestException, ValueError, TypeError, OverflowError) as exc:
                # Ne jamais exposer le message d'exception : il peut contenir le token.
                row["Erreur_cours_type"] = type(exc).__name__
        # Diagnostic uniquement lorsque le fournisseur répond explicitement 404.
        # Le moteur conserve le ticker T0 et NE substitue JAMAIS une suggestion
        # de recherche à une cotation : code, place et ISIN restent à certifier
        # indépendamment sur une source primaire.
        if api and row.get("HTTP_cours") == 404:
            row["Statut_recherche"] = "EN_ATTENTE_RECHERCHE_FOURNISSEUR"
            try:
                nom = str(p["Societe"]).strip()
                recherche = requests.get(
                    "https://eodhd.com/api/search/" + quote(nom, safe=""),
                    params={"api_token": api, "fmt": "json",
                            "type": "stock", "limit": 10},
                    timeout=25,
                )
                row["HTTP_recherche"] = recherche.status_code
                recherche.raise_for_status()
                suggestions = recherche.json()
                if isinstance(suggestions, list):
                    contenu = json.dumps(
                        suggestions, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":"), allow_nan=False,
                    ).encode("utf-8")
                    chemin = brut / (str(p["ID_position"]) + "_SEARCH.json")
                    _ecrire_atomique(chemin, contenu)
                    empreinte = sha256(contenu).hexdigest()
                    fichiers[str(chemin.relative_to(dossier))] = empreinte
                    row["SHA256_recherche_JSON"] = empreinte
                    row["Archive_recherche_JSON"] = str(chemin.relative_to(BASE))
                    row["Nombre_pistes_recherche"] = len(suggestions)
                    row["Statut_recherche"] = (
                        "PISTES_FOURNISSEUR_NON_CERTIFIEES" if suggestions
                        else "AUCUNE_PISTE_FOURNISSEUR"
                    )
                else:
                    row["Statut_recherche"] = "REPONSE_RECHERCHE_NON_EXPLOITABLE"
            except (requests.RequestException, ValueError, TypeError) as exc:
                # Ne jamais journaliser l'URL complète ni le message de
                # l'exception, susceptibles de contenir la clé API.
                row["Erreur_recherche_type"] = type(exc).__name__
        records.append(row)
    rapport = pd.DataFrame(records)
    _ecrire_atomique(OUT, rapport.to_csv(index=False).encode("utf-8"))
    copie = dossier / "COLLECTE_40.csv"
    _ecrire_atomique(copie, OUT.read_bytes())
    fichiers[str(copie.relative_to(dossier))] = sha256(copie.read_bytes()).hexdigest()
    compte = dict(Counter(rapport["Statut"]))
    synthese = {
        "debut_UTC": debut, "fin_UTC": datetime.now(timezone.utc).isoformat(),
        "nombre_positions": len(records), "statuts": compte,
        "codes_http": dict(Counter(str(x.get("HTTP_statut", "AUCUN")) for x in records)),
        "types_erreur": dict(Counter(x.get("Erreur_type", "AUCUNE") for x in records)),
        "observations_fournisseur": compte.get("OBSERVATION_FOURNISSEUR_NON_CERTIFIEE", 0),
        "cours_EOD_observes": int(rapport["Statut_cours"].eq("COURS_FOURNISSEUR_NON_CERTIFIE").sum()),
        "cours_EOD_conflits": int(rapport["Statut_cours"].eq("EN_ATTENTE_DATA_COURS_CONFLIT").sum()),
        "recherches_identite_404": int(rapport.get("HTTP_recherche", pd.Series(dtype=object)).notna().sum()),
        "pistes_identite_non_certifiees": int(pd.to_numeric(
            rapport.get("Nombre_pistes_recherche", pd.Series(dtype=object)),
            errors="coerce").fillna(0).sum()),
        "preuves_primaires_validees": 0, "scores_attribues": 0,
        "revue_MCPA_validee": False, "arbitrage_autorise": False,
        "type_sha256": "SHA256 des octets du JSON canonique archive",
        "fichiers_sha256": fichiers,
    }
    _ecrire_atomique(dossier / "MANIFESTE.json", json.dumps(
        synthese, indent=2, ensure_ascii=False, sort_keys=True
    ).encode("utf-8"))
    print("COLLECTE_40_STATUTS " + json.dumps(compte, ensure_ascii=False, sort_keys=True))
    print("COLLECTE_40_HTTP " + json.dumps(synthese["codes_http"], sort_keys=True))
    print("COLLECTE_40_COURS_EOD " + str(synthese["cours_EOD_observes"]) + "/40")
    print("COLLECTE_40_COURS_EOD_CONFLITS " + str(synthese["cours_EOD_conflits"]) + " (quarantaine)")
    print("COLLECTE_40_RECHERCHES_404 " + str(synthese["recherches_identite_404"]) +
          " PISTES_NON_CERTIFIEES " + str(synthese["pistes_identite_non_certifiees"]))
    print("COLLECTE_40_ERREURS " + json.dumps(synthese["types_erreur"], sort_keys=True))
    print("COLLECTE_40_PREUVES_PRIMAIRES=0; ARBITRAGE_INTERDIT")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("### Collecte EODHD : observations non certifiées\n\n")
            f.write("40 lignes traitées ; preuves primaires validées : **0** ; "
                    "SSI/MCPA et arbitrages : **non autorisés**.\n\n")
            f.write("Statuts : " + json.dumps(compte, ensure_ascii=False) + "\n\n")
            f.write("Cours EOD fournisseurs disponibles : **" +
                    str(synthese["cours_EOD_observes"]) + "/40** ; données secondaires, "
                    "pas une valorisation EUR ni une preuve de qualification.\n")
    return records


if __name__ == "__main__":
    collecter()

# -*- coding: utf-8 -*-
"""Observations EODHD des 40 titulaires, sans admission SSI/MCPA.

EODHD est un fournisseur de données, PAS une preuve réglementaire primaire.
Un échec par titre ne bloque jamais les 39 autres. Les réponses conservées
sont des instantanés JSON canoniques, vérifiables par SHA256, en artefact CI
et non des preuves primaires validées.
"""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import re

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
        ticker = str(p["Ticker"])
        row = {
            "ID_position": p["ID_position"], "Societe": p["Societe"],
            "Ticker": ticker, "Devise": p["Devise"],
            "Horodatage_UTC": datetime.now(timezone.utc).isoformat(),
            "Source": "EODHD fundamentals (fournisseur secondaire)",
            "Endpoint_sans_secret": "/api/fundamentals/" + ticker,
            "Statut": "EN_ATTENTE_CLE" if not api else "EN_ATTENTE_DATA_FOURNISSEUR",
            "Statut_identite": "NON_CERTIFIEE",
            "Preuve_primaire_validee": "NON", "Score_SSI": "MANQUANTE",
            "Score_MCPA": "MANQUANTE",
        }
        if api:
            try:
                response = requests.get(
                    "https://eodhd.com/api/fundamentals/" + ticker,
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
    print("COLLECTE_40_ERREURS " + json.dumps(synthese["types_erreur"], sort_keys=True))
    print("COLLECTE_40_PREUVES_PRIMAIRES=0; ARBITRAGE_INTERDIT")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("### Collecte EODHD : observations non certifiées\n\n")
            f.write("40 lignes traitées ; preuves primaires validées : **0** ; "
                    "SSI/MCPA et arbitrages : **non autorisés**.\n\n")
            f.write("Statuts : " + json.dumps(compte, ensure_ascii=False) + "\n")
    return records


if __name__ == "__main__":
    collecter()

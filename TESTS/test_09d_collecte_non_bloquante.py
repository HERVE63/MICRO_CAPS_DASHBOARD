"""Régression 09D : erreurs isolées, preuve fournisseur traçable, aucun score."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "SCRIPTS_ACTIFS/09D_COLLECTE_40_TITULAIRES.py"


class Reponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("Erreur HTTP simulee, sans secret")

    def json(self):
        return self.data


def executer():
    spec = importlib.util.spec_from_file_location("collecte_09d_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        source = root / "DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
        source.parent.mkdir()
        pd.DataFrame([
            {"ID_position": i, "Societe": "Growens" if i == 5 else "Société " + str(i),
             "Ticker": "T3.TO" if i == 3 else "T4.L" if i == 4 else "GROW.MI" if i == 5 else "T" + str(i),
             "Devise": "CAD" if i == 3 else "GBP" if i == 4 else "EUR" if i == 5 else "USD"}
            for i in range(1, 41)
        ]).to_csv(source, index=False)
        module.BASE = root
        module.SRC = source
        module.OUT = root / "DONNEES/COLLECTE_DIRECTE_40_TITULAIRES.csv"
        module.HIST = root / "AUDITS/HISTORIQUE_COLLECTES_HEBDOMADAIRES"

        appels = []
        def faux_get(url, params, timeout):
            assert params["api_token"] == "TEST_SECRET"
            assert timeout == 25
            appels.append(url)
            if url.endswith("/eod/T1.US"):
                return Reponse([{"date": "2026-10-31", "adjusted_close": 4.25}])
            if url.endswith("/eod/T3.TO"):
                return Reponse([{"date": "2026-10-31", "adjusted_close": 2.5}])
            if url.endswith("/eod/T4.LSE"):
                return Reponse([{"date": "2026-10-31", "adjusted_close": 11.0}])
            if url.endswith("/T1.US"):
                return Reponse({
                    "General": {"Code": "T1", "Exchange": "US", "ISIN": "US0000000001"},
                    "Highlights": {"RevenueTTM": 1234},
                })
            if url.endswith("/T2.US"):
                return Reponse({"General": {"Code": "AUTRE", "Exchange": "US"}})
            if url.endswith("/eod/GROW.MI"):
                return Reponse({"error": "Ticker Not Found"}, status_code=404)
            if url.endswith("/search/Growens"):
                return Reponse([
                    {"Code": "GROW", "Exchange": "MI", "Name": "Growens S.p.A.",
                     "ISIN": "IT0005040354"},
                    {"Code": "GROW", "Exchange": "US", "Name": "Autre société",
                     "ISIN": "US0000000002"},
                ])
            raise requests.Timeout("secret dans une URL à ne pas publier")

        with patch.dict(os.environ, {"EODHD_API_TOKEN": "TEST_SECRET"}, clear=True):
            with patch.object(module.requests, "get", side_effect=faux_get):
                rows = module.collecter()
        assert len(rows) == 40
        assert appels[:8] == [
            "https://eodhd.com/api/fundamentals/T1.US",
            "https://eodhd.com/api/eod/T1.US",
            "https://eodhd.com/api/fundamentals/T2.US",
            "https://eodhd.com/api/eod/T2.US",
            "https://eodhd.com/api/fundamentals/T3.TO",
            "https://eodhd.com/api/eod/T3.TO",
            "https://eodhd.com/api/fundamentals/T4.LSE",
            "https://eodhd.com/api/eod/T4.LSE",
        ], "Suffixes US/LSE et plan B EOD ne doivent pas modifier les cotations originales"
        assert rows[0]["Ticker"] == "T1" and rows[0]["Ticker_requete_EODHD"] == "T1.US"
        assert rows[2]["Ticker"] == "T3.TO" and rows[2]["Ticker_requete_EODHD"] == "T3.TO"
        assert rows[3]["Ticker"] == "T4.L" and rows[3]["Ticker_requete_EODHD"] == "T4.LSE"
        assert rows[0]["Statut"] == "OBSERVATION_FOURNISSEUR_NON_CERTIFIEE"
        assert rows[1]["Statut"] == "EN_ATTENTE_DATA_IDENTITE"
        assert rows[2]["Statut"] == rows[3]["Statut"] == "OBSERVATION_COURS_SEULEMENT_NON_CERTIFIEE"
        assert rows[0]["Statut_cours"] == rows[2]["Statut_cours"] == "COURS_FOURNISSEUR_NON_CERTIFIE"
        assert rows[2]["Cours_ajuste_fournisseur"] == 2.5
        assert all(r["Statut"] == "EN_ATTENTE_DATA_FOURNISSEUR" for r in rows[4:])
        assert "https://eodhd.com/api/search/Growens" in appels
        assert rows[4]["HTTP_cours"] == 404
        assert rows[4]["Statut_recherche"] == "PISTES_FOURNISSEUR_NON_CERTIFIEES"
        assert rows[4]["Nombre_pistes_recherche"] == 2
        assert rows[4]["Statut_cours"] == "EN_ATTENTE_DATA_COURS"
        assert rows[4]["Statut_identite"] == "NON_CERTIFIEE"
        assert rows[4]["Ticker_requete_EODHD"] == "GROW.MI"
        assert rows[4]["Score_SSI"] == rows[4]["Score_MCPA"] == "MANQUANTE"
        assert all(r["Preuve_primaire_validee"] == "NON" for r in rows)
        assert all(r["Score_SSI"] == r["Score_MCPA"] == "MANQUANTE" for r in rows)
        csv_bytes = module.OUT.read_bytes()
        assert b"TEST_SECRET" not in csv_bytes
        assert len(pd.read_csv(module.OUT)) == 40
        dossiers = list(module.HIST.glob("COLLECTE_40_*"))
        assert len(dossiers) == 1
        manifeste = json.loads((dossiers[0] / "MANIFESTE.json").read_text())
        assert manifeste["nombre_positions"] == 40
        assert manifeste["preuves_primaires_validees"] == 0
        assert manifeste["scores_attribues"] == 0
        assert manifeste["cours_EOD_observes"] == 3
        assert manifeste["arbitrage_autorise"] is False
        for rel, attendu in manifeste["fichiers_sha256"].items():
            assert hashlib.sha256((dossiers[0] / rel).read_bytes()).hexdigest() == attendu
        assert b"TEST_SECRET" not in (dossiers[0] / "MANIFESTE.json").read_bytes()
        assert len(list((dossiers[0] / "REPONSES_FOURNISSEUR").glob("*.json"))) == 6
        assert (dossiers[0] / "REPONSES_FOURNISSEUR/5_SEARCH.json").exists()
        assert manifeste["recherches_identite_404"] == 1
        assert manifeste["pistes_identite_non_certifiees"] == 2
        # Absence de clé : aucun appel réseau, 40 dossiers en attente, pas d'échec global.
        module.HIST = root / "AUDITS/SANS_CLE"
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(module.requests, "get", side_effect=AssertionError("réseau interdit")):
                sans_cle = module.collecter()
        assert len(sans_cle) == 40
        assert all(r["Statut"] == "EN_ATTENTE_CLE" for r in sans_cle)
        print("09D : 40/40 traités, 2 fondamentaux + 3 EOD + 1 recherche 404 SHA256, 0 score ; sans clé 40 EN_ATTENTE_CLE")


if __name__ == "__main__":
    executer()

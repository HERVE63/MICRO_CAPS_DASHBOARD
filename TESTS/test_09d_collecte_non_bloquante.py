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
    status_code = 200

    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

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
            {"ID_position": i, "Societe": "Société " + str(i),
             "Ticker": "T" + str(i), "Devise": "USD"}
            for i in range(1, 41)
        ]).to_csv(source, index=False)
        module.BASE = root
        module.SRC = source
        module.OUT = root / "DONNEES/COLLECTE_DIRECTE_40_TITULAIRES.csv"
        module.HIST = root / "AUDITS/HISTORIQUE_COLLECTES_HEBDOMADAIRES"

        def faux_get(url, params, timeout):
            assert params["api_token"] == "TEST_SECRET"
            assert timeout == 25
            if url.endswith("/T1"):
                return Reponse({
                    "General": {"Code": "T1", "Exchange": "US", "ISIN": "US0000000001"},
                    "Highlights": {"RevenueTTM": 1234},
                })
            if url.endswith("/T2"):
                return Reponse({"General": {"Code": "AUTRE", "Exchange": "US"}})
            raise requests.Timeout("secret dans une URL à ne pas publier")

        with patch.dict(os.environ, {"EODHD_API_TOKEN": "TEST_SECRET"}, clear=True):
            with patch.object(module.requests, "get", side_effect=faux_get):
                rows = module.collecter()
        assert len(rows) == 40
        assert rows[0]["Statut"] == "OBSERVATION_FOURNISSEUR_NON_CERTIFIEE"
        assert rows[1]["Statut"] == "EN_ATTENTE_DATA_IDENTITE"
        assert all(r["Statut"] == "EN_ATTENTE_DATA_FOURNISSEUR" for r in rows[2:])
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
        assert manifeste["arbitrage_autorise"] is False
        for rel, attendu in manifeste["fichiers_sha256"].items():
            assert hashlib.sha256((dossiers[0] / rel).read_bytes()).hexdigest() == attendu
        assert b"TEST_SECRET" not in (dossiers[0] / "MANIFESTE.json").read_bytes()
        assert len(list((dossiers[0] / "REPONSES_FOURNISSEUR").glob("*.json"))) == 2
        # Absence de clé : aucun appel réseau, 40 dossiers en attente, pas d'échec global.
        module.HIST = root / "AUDITS/SANS_CLE"
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(module.requests, "get", side_effect=AssertionError("réseau interdit")):
                sans_cle = module.collecter()
        assert len(sans_cle) == 40
        assert all(r["Statut"] == "EN_ATTENTE_CLE" for r in sans_cle)
        print("09D : 40/40 traités malgré 38 erreurs, 2 snapshots SHA256, 0 score ; sans clé 40 EN_ATTENTE_CLE")


if __name__ == "__main__":
    executer()

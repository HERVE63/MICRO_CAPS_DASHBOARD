"""Réception hors réseau du collecteur incrémental : priorité, reprise et échec."""
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone
import importlib.util

import pandas as pd

SRC = Path(__file__).resolve().parents[1] / "SCRIPTS_ACTIFS/07N2_COLLECTE_FONDAMENTAUX_INCREMENTALE.py"
spec = importlib.util.spec_from_file_location("incremental", SRC)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
INSTANT = datetime(2026, 10, 30, 10, 0, tzinfo=timezone.utc)


def executer():
    with TemporaryDirectory() as temp:
        base = Path(temp)
        (base / "DONNEES").mkdir()
        d = base / "DONNEES"
        pd.DataFrame([
            {"Ticker": "A", "Admissible_filtre_marche": "OUI"},
            {"Ticker": "B", "Admissible_filtre_marche": "OUI"},
            {"Ticker": "C", "Admissible_filtre_marche": "NON_DONNEE_MANQUANTE"},
        ]).to_csv(d / "UNIVERS_PRET_FILTRES_OBJECTIFS.csv", index=False)
        pd.DataFrame([{
            "Ticker": "A", "Date_scan": "2026-10-08", "CA_TTM": 125,
            "Cash": 12, "Dette_totale": 5, "Actions": 1000,
            "Insiders_pct": 0.15, "Statut_fondamentaux": "OK",
            "Source_fondamentaux": "Yahoo Finance / yfinance get_info"
        }]).to_csv(d / "FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv", index=False)
        appels = []

        def fournisseur(ticker):
            appels.append(ticker)
            return {"totalRevenue": 230, "totalCash": 20, "totalDebt": 6,
                    "sharesOutstanding": 2000, "heldPercentInsiders": 0.20}

        bilan = module.executer(base=base, fetcher=fournisseur,
                                taille_lot=1, instant=INSTANT)
        assert appels == ["B"], appels
        assert int(bilan.Lot_tente.iloc[0]) == 1
        t = pd.read_csv(d / "FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv")
        assert set(t.Ticker) == {"A", "B"}
        assert t.set_index("Ticker").loc["B", "Statut_fondamentaux"] == "OK"
        assert t.set_index("Ticker").loc["A", "Date_scan"] == "2026-10-08"

        def echec(ticker):
            appels.append(ticker)
            raise RuntimeError("fournisseur temporairement indisponible")

        bilan = module.executer(base=base, fetcher=echec,
                                taille_lot=1, instant=INSTANT)
        assert appels == ["B", "A"], appels
        assert int(bilan.Erreurs_source.iloc[0]) == 1
        t = pd.read_csv(d / "FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv").set_index("Ticker")
        assert t.loc["A", "Date_scan"] == "2026-10-08"
        assert t.loc["A", "CA_TTM"] == 125
        assert t.loc["A", "Statut_derniere_tentative"] == "ERREUR_SOURCE"
        assert t.loc["A", "Statut_fondamentaux"] == "OK"

        bilan = module.executer(base=base, fetcher=echec,
                                taille_lot=1, instant=INSTANT)
        assert appels == ["B", "A"], "Une tentative ne doit pas se répéter le même jour"
        assert int(bilan.Lot_tente.iloc[0]) == 0
        assert not (d / "RESULTATS_SSI.csv").exists(), "Aucune note SSI imputée"
        print("Collecteur incrémental : priorité, reprise, échec et absence de score vérifiés")


if __name__ == "__main__":
    executer()

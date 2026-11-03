"""Test isolé du collecteur historique 09N, sans accès réseau ni données officielles."""
import csv
import importlib.util
from pathlib import Path


def test_09n_quarantaine_par_titre_et_aucune_note(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "SCRIPTS_ACTIFS" / "09N_COLLECTE_HISTORIQUES_YAHOO_40.py"
    spec = importlib.util.spec_from_file_location("collecte_09n_isolee", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    donnees = tmp_path / "DONNEES"
    donnees.mkdir()
    with (donnees / "ETAT_INITIAL_PORTEFEUILLE_GERE.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ID_position", "Ticker"])
        writer.writeheader()
        writer.writerows({"ID_position": str(i), "Ticker": f"TEST{i}"} for i in range(1, 41))
    monkeypatch.setattr(module, "D", donnees)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    def simulation(symbol):
        if symbol == "TEST2":
            raise TimeoutError("simulation de source indisponible")
        return ({
            "timestamp": [1609459200, 1609545600],
            "indicators": {
                "quote": [{"close": [10.0, 11.0], "volume": [100, 120]}],
                "adjclose": [{"adjclose": [9.0, 10.0]}],
            },
        }, "https://example.invalid/test")

    monkeypatch.setattr(module, "fetch", simulation)
    module.main()
    with (donnees / "COUVERTURE_HISTORIQUES_YAHOO_40.csv").open(newline="", encoding="utf-8") as f:
        couverture = list(csv.DictReader(f))
    with (donnees / "HISTORIQUES_YAHOO_40.csv").open(newline="", encoding="utf-8") as f:
        historiques = list(csv.DictReader(f))
    assert len(couverture) == 40
    assert sum(r["Statut"] == "OK" for r in couverture) == 39
    assert next(r for r in couverture if r["Ticker"] == "TEST2")["Statut"] == "FAILED_TimeoutError"
    assert len(historiques) == 78
    assert all(r["Ticker"] != "TEST2" for r in historiques)
    assert all(r["AdjClose"] for r in historiques)
    assert not (donnees / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv").exists()


def test_09n_ne_certifie_pas_une_serie_sans_cours_ajustes(tmp_path, monkeypatch):
    """Les clôtures brutes ne suffisent pas pour certifier le momentum ajusté."""
    source = Path(__file__).resolve().parents[1] / "SCRIPTS_ACTIFS" / "09N_COLLECTE_HISTORIQUES_YAHOO_40.py"
    spec = importlib.util.spec_from_file_location("collecte_09n_adj", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    donnees = tmp_path / "DONNEES"
    donnees.mkdir()
    with (donnees / "ETAT_INITIAL_PORTEFEUILLE_GERE.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ID_position", "Ticker"])
        writer.writeheader()
        writer.writerows({"ID_position": str(i), "Ticker": f"TEST{i}"} for i in range(1, 41))
    monkeypatch.setattr(module, "D", donnees)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    def simulation(symbol):
        adj = [] if symbol == "TEST2" else [9.0, 10.0]
        return ({
            "timestamp": [1609459200, 1609545600],
            "indicators": {
                "quote": [{"close": [10.0, 11.0], "volume": [100, 120]}],
                "adjclose": [{"adjclose": adj}],
            },
        }, "https://example.invalid/test")
    monkeypatch.setattr(module, "fetch", simulation)
    module.main()
    with (donnees / "COUVERTURE_HISTORIQUES_YAHOO_40.csv").open(newline="", encoding="utf-8") as f:
        couverture = list(csv.DictReader(f))
    assert len(couverture) == 40
    assert sum(r["Statut"] == "OK" for r in couverture) == 39
    assert next(r for r in couverture if r["Ticker"] == "TEST2")["Statut"] == "MISSING_ADJUSTED"
    with (donnees / "HISTORIQUES_YAHOO_40.csv").open(newline="", encoding="utf-8") as f:
        historiques = list(csv.DictReader(f))
    assert len(historiques) == 80
    assert all(r["AdjClose"] == "" for r in historiques if r["Ticker"] == "TEST2")
    assert not (donnees / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv").exists()

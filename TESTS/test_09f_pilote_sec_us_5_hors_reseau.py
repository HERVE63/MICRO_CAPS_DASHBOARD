"""Non-regression 09F : sources SEC brutes, CIK, quarantaine, point-in-time et SHA256."""
import csv
import hashlib
import importlib.util
import json
import os
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pilote_sec_us_5", ROOT / "SCRIPTS_ACTIFS/09F_PILOTE_SEC_US_5.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def donnees(tmp):
    d = Path(tmp) / "DONNEES"
    d.mkdir()
    lignes = [
        ("1", "Intellicheck", "IDN"), ("2", "InfuSystem", "INFU"),
        ("3", "One Stop Systems", "OSS"), ("4", "Crexendo", "CXDO"),
        ("5", "Lifeway Foods", "LWAY"),
    ]
    with (d / "ETAT_INITIAL_PORTEFEUILLE_GERE.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ID_position", "Societe", "Ticker", "Devise", "Date_entree"])
        for i, nom, ticker in lignes:
            w.writerow([i, nom, ticker, "USD", "2026-10-01"])
    return d / "ETAT_INITIAL_PORTEFEUILLE_GERE.csv"


def source(url, agent):
    assert agent == "Research test@research.invalid"
    if url == mod.MAPPING:
        obj = {str(i): {"ticker": t, "cik_str": cik, "title": t}
               for i, (t, cik) in enumerate([
                   ("IDN", 1001), ("INFU", 1002), ("OSS", 1003),
                   ("CXDO", 1004), ("CXDO", 1005), ("LWAY", 1006)])}
    elif "CIK0000001002" in url:
        raise urllib.error.HTTPError(url, 403, "interdit", {}, None)
    elif "/submissions/CIK" in url:
        cik = int(url.split("CIK")[1].split(".json")[0])
        obj = {
            "cik": 9999 if cik == 1003 else cik,
            "tickers": {1001: ["IDN"], 1003: ["OSS"], 1006: ["LWAY"]}.get(cik, []),
            "filings": {"recent": {"filingDate": ["2026-10-30"],
                                    "form": ["10-Q"]}},
        }
    elif "/companyfacts/CIK" in url:
        cik = int(url.split("CIK")[1].split(".json")[0])
        obj = {"cik": cik, "facts": {"us-gaap": {
            "Assets": {"units": {"USD": [{"val": 12, "end": "2026-09-30"}]}}
        } if cik == 1001 else {"us-gaap": {}}}
    else:
        raise AssertionError(url)
    brut = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return obj, brut


def verifier_manifestes(dossier, manifest):
    assert manifest["Univers"] == manifest["Lignes"] == 5
    assert manifest["Notes_attribuees"] == manifest["Arbitrages"] == 0
    assert manifest["Identites_SCE_certifiees"] == 0
    for rel, digest in manifest["Fichiers_SHA256"].items():
        cible = (dossier / rel).resolve()
        assert cible.is_relative_to(dossier.resolve())
        assert hashlib.sha256(cible.read_bytes()).hexdigest() == digest
    for s in manifest["Sources"]:
        assert s["URL"].startswith(("https://www.sec.gov/", "https://data.sec.gov/"))
        assert hashlib.sha256((dossier / s["Fichier_brut"]).read_bytes()).hexdigest() == s["SHA256"]


def test_pilote_non_bloquant():
    with TemporaryDirectory() as tmp:
        entree = donnees(tmp)
        sha_avant = hashlib.sha256(entree.read_bytes()).hexdigest()
        instant = datetime(2026, 11, 2, 7, 0, tzinfo=timezone.utc)
        with patch.dict(os.environ, {"SEC_USER_AGENT": "Research test@research.invalid"}):
            m = mod.executer(base=tmp, fetcher=source, pause=lambda _: None, maintenant=instant)
        dossier = Path(tmp) / "AUDITS/SEC_PILOTE_US_5/20261102T070000000000Z"
        verifier_manifestes(dossier, m)
        assert m["Captures_brutes"] == 6, m
        with (dossier / "DIAGNOSTIC_SEC_US_5.csv").open(newline="") as f:
            rows = {r["Ticker"]: r for r in csv.DictReader(f)}
        assert len(rows) == 5
        assert rows["IDN"]["Statut"] == "XBRL_BRUT_A_VERIFIER"
        assert rows["IDN"]["Disponibilite_publication_T0"] == "POSTERIEUR_OU_JOUR_T0"
        assert rows["INFU"]["Statut"] == "EN_ATTENTE_DATA_SEC_HTTP_403"
        assert rows["OSS"]["Statut"] == "EN_ATTENTE_DATA_IDENTITE_SEC_DIVERGENTE"
        assert rows["CXDO"]["Statut"] == "EN_ATTENTE_DATA_TICKER_ABSENT_OU_AMBIGU"
        assert rows["LWAY"]["Statut"] == "EN_ATTENTE_DATA_XBRL_ABSENT"
        assert all(r["Score_SSI"] == "MANQUANTE" and r["Score_MCPA"] == "MANQUANTE"
                   and r["Preuve_SCE_certifiee"] == "NON" for r in rows.values())
        assert hashlib.sha256(entree.read_bytes()).hexdigest() == sha_avant


def test_contact_requis():
    with TemporaryDirectory() as tmp:
        donnees(tmp)
        with patch.dict(os.environ, {"SEC_USER_AGENT": ""}):
            try:
                mod.executer(base=tmp, fetcher=source, pause=lambda _: None)
            except RuntimeError as e:
                assert "SEC_USER_AGENT" in str(e)
            else:
                raise AssertionError("Un contact absent ne doit pas permettre la collecte")
        assert not (Path(tmp) / "AUDITS").exists()


def test_registre_indisponible_n_interrompt_pas_cohorte():
    with TemporaryDirectory() as tmp:
        donnees(tmp)
        def panne(url, agent):
            raise urllib.error.HTTPError(url, 429, "rate limited", {}, None)
        with patch.dict(os.environ, {"SEC_USER_AGENT": "Research test@research.invalid"}):
            m = mod.executer(base=tmp, fetcher=panne, pause=lambda _: None,
                             maintenant=datetime(2026, 11, 2, 7, 1, tzinfo=timezone.utc))
        dossier = Path(tmp) / "AUDITS/SEC_PILOTE_US_5/20261102T070100000000Z"
        verifier_manifestes(dossier, m)
        assert m["Captures_brutes"] == 0
        assert m["Erreurs_registre"] == ["REGISTRE_SEC_HTTPError"]
        with (dossier / "DIAGNOSTIC_SEC_US_5.csv").open(newline="") as f:
            assert all(r["Statut"] == "EN_ATTENTE_DATA_REGISTRE_SEC"
                       for r in csv.DictReader(f))


if __name__ == "__main__":
    test_pilote_non_bloquant()
    test_contact_requis()
    test_registre_indisponible_n_interrompt_pas_cohorte()
    print("TEST 09F OK: 5 lignes, SHA256, CIK, T0, erreurs isolees, 0 score")

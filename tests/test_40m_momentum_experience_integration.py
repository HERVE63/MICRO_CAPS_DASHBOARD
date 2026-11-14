"""Test d'integration du classement des 40 titulaires; aucun ordre ni note fictive."""
import csv
import subprocess
import sys
from pathlib import Path
from datetime import date

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"DONNEES"

def test_momentum_40_titulaires_et_verrou_arbitrage():
    result=subprocess.run([sys.executable,str(ROOT/"SCRIPTS_ACTIFS/40M_MOMENTUM_EXPERIENCE.py")],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    with (DATA/"ETAT_INITIAL_PORTEFEUILLE_GERE.csv").open(encoding="utf-8-sig",newline="") as f:
        holdings=list(csv.DictReader(f))
    with (DATA/"EXPERIENCE_MOMENTUM_40.csv").open(encoding="utf-8-sig",newline="") as f:
        signals=list(csv.DictReader(f))
    assert len(holdings)==len(signals)==40
    assert len({r["Ticker"] for r in signals})==40
    assert {r["Ticker"] for r in holdings}=={r["Ticker"] for r in signals}
    assert all(r["Arbitrage_autorise"]=="NON" for r in signals)
    assert all(r["Statut"] in {"CALCULABLE_FRAIS","HISTORIQUE_PERIME","INCOMPLET_SANS_SIGNAL"} for r in signals)
    for r in signals:
        if r["Statut"]=="CALCULABLE_FRAIS":
            assert r["Date_historique"]
            assert (date.today()-date.fromisoformat(r["Date_historique"])).days<=5
            assert r["Rang_momentum"]
        else:
            assert not r["Rang_momentum"]
            assert r["Signal"]=="DONNEES_PERIMEES_SANS_ARBITRAGE" or r["Statut"]=="INCOMPLET_SANS_SIGNAL"
    print("40M_INTEGRATION_OK titulaires=40 arbitrages_autorises=0 frais=",sum(r["Statut"]=="CALCULABLE_FRAIS" for r in signals))

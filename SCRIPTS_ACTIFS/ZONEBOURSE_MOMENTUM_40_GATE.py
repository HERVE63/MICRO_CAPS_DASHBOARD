#!/usr/bin/env python3
"""Gate de validation des 40 titulaires: réutilise le moteur 40M et ses preuves navigateur Zonebourse.
Aucun téléchargement Yahoo, aucune note MCPA, aucun ordre ni journalisation.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"DONNEES"
ENGINE=ROOT/"SCRIPTS_ACTIFS"/"40M_MOMENTUM_EXPERIENCE.py"

def main():
    spec=importlib.util.spec_from_file_location("momentum40_existing",ENGINE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ledger=DATA/"JOURNAL_ARBITRAGES_GERE.csv"
    before=hashlib.sha256(ledger.read_bytes()).hexdigest()
    report=module.main(ROOT,datetime.now(timezone.utc))
    after=hashlib.sha256(ledger.read_bytes()).hexdigest()
    if before!=after:
        raise RuntimeError("JOURNAL_VIRTUEL_MODIFIE")
    if report.get("titulaires")!=40:
        raise SystemExit("COHORTE_INCOMPLETE")
    count=report.get("lectures_exploitables",0)
    print(json.dumps({"titulaires":40,"zonebourse_valides":count,
        "manquants":40-count,"journal_inchange":True,
        "seuil_minimum":module.MIN_VALIDATED,"arbitrage_autorise":report["arbitrage_autorise"],
        "lignes_exclues":report["lignes_exclues"],
        "suspensions":report.get("suspensions_documentees",[])},ensure_ascii=False))
    if not report["arbitrage_autorise"]:
        raise SystemExit(2)

if __name__=="__main__":
    main()

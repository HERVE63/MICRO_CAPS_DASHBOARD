#!/usr/bin/env python3
"""Create a non-certifying, source-aware work queue for existing holdings first."""
import csv
import json
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
D = BASE / "DONNEES"
def read(name):
    with (D / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))
positions = read("ETAT_INITIAL_PORTEFEUILLE_GERE.csv")
if len(positions) != 40 or len({r["Ticker"] for r in positions}) != 40:
    raise RuntimeError("40 titulaires uniques requis")
sources = {
    "USD": ("SEC_EDGAR", "RAPPORTS_EMETTEUR", "EODHD", "YAHOO", "ZONEBOURSE"),
    "CAD": ("SEDAR_PLUS", "RAPPORTS_EMETTEUR", "TSX_TSXV", "EODHD", "YAHOO", "ZONEBOURSE"),
    "GBP": ("COMPANIES_HOUSE", "RNS_LSE", "RAPPORTS_EMETTEUR", "EODHD", "YAHOO", "ZONEBOURSE"),
    "EUR": ("REGULATEUR_NATIONAL", "EURONEXT_OU_PLACE", "RAPPORTS_EMETTEUR", "EODHD", "YAHOO", "ZONEBOURSE"),
    "SEK": ("REGULATEUR_NATIONAL", "NASDAQ_NORDIC_OU_PLACE", "RAPPORTS_EMETTEUR", "EODHD", "YAHOO", "ZONEBOURSE"),
}
rows = []
for p in positions:
    currency = p["Devise"].strip().upper()
    for rank, source in enumerate(sources.get(currency, ("REGULATEUR_NATIONAL", "RAPPORTS_EMETTEUR", "EODHD", "YAHOO", "ZONEBOURSE")), 1):
        rows.append({"Priorite_portefeuille": "TITULAIRE_AVANT_CHALLENGER",
                     "ID_position": p["ID_position"], "Societe": p["Societe"],
                     "Ticker": p["Ticker"], "Devise": currency,
                     "Rang_source": rank, "Source_cible": source,
                     "Identite_emetteur_verifiee": "NON",
                     "Donnees_financieres_validees": "NON",
                     "Statut": "A_COLLECTER_SANS_IMPUTATION"})
out = D / "PLAN_COLLECTE_MULTISOURCE_40_TITULAIRES.csv"
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(json.dumps({"titulaires": len(positions), "pistes_de_sources": len(rows), "fichier": str(out.relative_to(BASE)), "scores_crees": 0, "transactions": 0}, ensure_ascii=False))

#!/usr/bin/env python3
"""Read-only integrity check for existing MICRO CAPS interfaces."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def rows(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

positions = rows("DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv")
journal = rows("DONNEES/JOURNAL_ARBITRAGES_GERE.csv")
params = {r["Parametre"]: r["Valeur"] for r in rows("CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv")}
checks = {
    "positions_40": len(positions) == 40,
    "unique_ids": len({p["ID_position"] for p in positions}) == 40,
    "capital_4000": abs(sum(float(p["Capital_initial_EUR"]) for p in positions) - 4000) < 0.01,
    "fees_buy": params.get("Frais_achat") == "2.5",
    "fees_sell": params.get("Frais_vente") == "2.5",
    "weekly_review": params.get("Frequence_revue") == "HEBDOMADAIRE_MARDI",
    "monthly_rebalance": params.get("Frequence_arbitrage_normal") == "MENSUEL",
    "replay_exists": (ROOT / "SCRIPTS_ACTIFS/05C_REPLAY_PORTEFEUILLE_GERE.py").is_file(),
}
print(json.dumps({"checks": checks, "journal_operations": len(journal), "read_only": True}, ensure_ascii=False))
if not all(checks.values()):
    raise SystemExit(1)

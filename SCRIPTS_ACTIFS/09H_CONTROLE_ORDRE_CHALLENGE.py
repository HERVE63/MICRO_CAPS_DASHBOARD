#!/usr/bin/env python3
"""Read-only gate: incumbents first, external challengers second, duel last."""
import csv
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / "DONNEES"
def read(name):
    p = ROOT / name
    if not p.exists() or p.stat().st_size == 0:
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))
positions = read("ETAT_INITIAL_PORTEFEUILLE_GERE.csv")
revue = read("REVUE_HEBDOMADAIRE_MCPA_IPS.csv")
ssi = read("RESULTATS_SSI.csv")
duels = read("DUELS_PROCHAIN_EURO.csv")
titulaires = [r for r in revue if r.get("Type", "").upper() == "TITULAIRE" and r.get("Statut_analyse", "").upper() in ("VALIDE", "VALIDEE")]
challengers = [r for r in revue if r.get("Type", "").upper() == "CHALLENGER" and r.get("Statut_analyse", "").upper() in ("VALIDE", "VALIDEE")]
actifs = [r for r in positions if r.get("Statut", "").upper() == "ACTIF"]
# This is a read-only preparation gate, not a replacement for the strict 09/08B validators.
# The initial 40 holdings are checked before considering any external candidate.
titulaire_ids = {str(r.get("ID_position", "")).strip() for r in titulaires}
actif_ids = {str(r.get("ID_position", "")).strip() for r in actifs}
admis = {r.get("Ticker") for r in ssi if r.get("Statut_SSI") == "ADMIS_SSI"}
etape_1 = bool(actifs) and len(titulaire_ids) == len(titulaires) and titulaire_ids == actif_ids
etape_2 = etape_1 and bool(challengers) and all(r.get("Ticker") in admis for r in challengers)
etape_3 = etape_2 and bool(duels)
print(json.dumps({"ordre": ["TITULAIRES", "CHALLENGERS", "DUELS", "ARBITRAGE_VIRTUEL"], "titulaires_actifs": len(actifs), "titulaires_valides": len(titulaires), "challengers_valides": len(challengers), "challengers_admis_ssi": len(admis), "duels_existants": len(duels), "etape_1_couverture_titulaires": etape_1, "etape_2_challengers": etape_2, "etape_3_duels": etape_3, "etape_suivante": ("NOTER_LES_TITULAIRES" if not etape_1 else "QUALIFIER_LES_CHALLENGERS" if not etape_2 else "VALIDER_LES_DUELS" if not etape_3 else "CONTROLE_STRICT_09_08B_10"), "arbitrage_autorise_par_ce_controle": False}, ensure_ascii=False))

if "--require-ready" in sys.argv and not etape_3:
    raise SystemExit("BLOQUE: titulaires puis challengers puis duels non verifies")

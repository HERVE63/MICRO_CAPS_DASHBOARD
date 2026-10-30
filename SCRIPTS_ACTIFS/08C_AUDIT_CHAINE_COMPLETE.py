"""Audit strict en lecture seule : aucune admission fictive, aucune mutation des historiques."""
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "DONNEES"

def lire(nom):
    p = D / nom
    if not p.is_file():
        raise RuntimeError(f"Fichier manquant : {nom}")
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def verifier():
    chasse = lire("CHASSE_CANDIDATS.csv")
    if not chasse:
        raise RuntimeError("BLOQUE : chasse vide malgré une exécution déclarée réussie")
    if not all(x.get("Ticker", "").strip() for x in chasse):
        raise RuntimeError("BLOQUE : tickers absents dans la chasse")
    ssi = lire("RESULTATS_SSI.csv")
    admis = {r["Ticker"].strip().upper(): r for r in ssi
             if r.get("Statut_SSI") == "ADMIS_SSI" and
             float(r.get("SSI") or 0) >= 65}
    revue = lire("REVUE_HEBDOMADAIRE_MCPA_IPS.csv")
    challengers = [r for r in revue if r.get("Type", "").upper() == "CHALLENGER"]
    if not admis or not challengers:
        raise RuntimeError("BLOQUE : aucune admission SSI ou aucun challenger en revue")
    tickers = {r["Ticker"].strip().upper() for r in chasse}
    for r in challengers:
        t = r.get("Ticker", "").strip().upper()
        if t not in tickers or t not in admis:
            raise RuntimeError(f"BLOQUE : challenger {t} sans preuve de chasse/SSI")
        if float(r.get("SSI") or 0) < 65:
            raise RuntimeError(f"BLOQUE : SSI insuffisant pour {t}")
    print(f"Chasse {len(chasse)} | SSI admis {len(admis)} | challengers {len(challengers)}")
    print("Audit partiel OK : affichage mobile et arbitrages restent à tester séparément")

if __name__ == "__main__":
    try:
        verifier()
    except (RuntimeError, ValueError, KeyError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)

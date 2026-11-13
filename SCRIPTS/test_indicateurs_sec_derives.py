#!/usr/bin/env python3
"""Regression gate for SEC-derived indicators. No score or trade authorization."""
import csv
from pathlib import Path

PATH = Path("DONNEES/INDICATEURS_SEC_DERIVES_NON_CERTIFIES_20261113.csv")

def validate(path=PATH):
    with open(path, newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 5, f"expected 5 rows, got {len(rows)}"
    assert {r["Ticker"] for r in rows} == {"IDN", "INFU", "OSS", "CXDO", "LWAY"}
    checks = 0
    for r in rows:
        def value(key):
            return float(r[key]) if r[key] else None
        assert value("CA_YTD_USD") > 0
        assert abs(100 * value("Resultat_operationnel_YTD_USD") / value("CA_YTD_USD") - value("Marge_operationnelle_YTD_pct")) <= 0.011
        checks += 1
        assert abs(100 * value("Passifs_USD") / value("Actifs_USD") - value("Passifs_sur_actifs_pct")) <= 0.011
        checks += 1
        cfo, capex, fcf = (value(k) for k in ("CFO_YTD_USD", "Capex_YTD_USD", "FCF_proxy_YTD_USD"))
        if cfo is None or capex is None:
            assert fcf is None and r["Statut_FCF"] in {"INCOMPLET_CFO_OU_CAPEX", "INCOMPLET_CAPEX_ZERO_NON_VERIFIE"}
            if r["Ticker"] == "CXDO":
                assert cfo is not None and capex is None and r["Statut_FCF"] == "INCOMPLET_CAPEX_ZERO_NON_VERIFIE"
        else:
            assert fcf is not None and abs((cfo - capex) - fcf) < 0.01
        checks += 1
        assert r["Statut"] == "DERIVE_NON_CERTIFIE_SANS_SCORE"
    print(f"PASS: titulaires={len(rows)} controles={checks}; aucun score certifie")
    return checks

if __name__ == "__main__":
    validate()

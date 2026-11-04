"""Contrôle hors réseau des pistes SEC_BRIDGE : jamais de qualification par ticker seul."""
from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[1]
PISTES = ROOT / "AUDITS/REPARATION/PISTES_RAPPROCHEMENT_SEC_BRIDGE_20261030.csv"
CANDIDATS = ROOT / "DONNEES/CANDIDATS_PRETS_SSI.csv"
SHA_AUTORISES = {
    "6c5b80ac96e86c825f5f94f520f50555f1a1c487a03a8bdc2bdbdd7c7b29aacf",
    "b9c7fd94a7cb299df9076c446ba2829c9f5e590d7bcd44cdc6c2d51125d944bd",
}

def lire(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def executer():
    avant = CANDIDATS.read_bytes()
    candidats = {r["Ticker"]: r for r in lire(CANDIDATS)}
    pistes = lire(PISTES)
    assert len(pistes) == 24, "Inventaire historique : nombre de pistes inattendu"
    assert len({r["Ticker_candidat"] for r in pistes}) == len(pistes)
    for r in pistes:
        t = r["Ticker_candidat"]
        assert t in candidats, "Piste hors cohorte SSI"
        assert r["Nom_candidat"] == candidats[t]["Societe"]
        assert r["Code_base_non_identifiant"] == t.rsplit(".", 1)[0]
        assert all(re.fullmatch(r"[0-9]{10}", x) for x in r["CIK_piste_archives"].split("|"))
        assert set(r["SHA256_sources"].split("|")) <= SHA_AUTORISES
        assert len(r["SHA256_sources"].split("|")) == len(r["Drive_ID_sources"].split("|"))
        assert len(r["Dates_sources_UTC"].split("|")) == len(r["Drive_ID_sources"].split("|"))
        assert r["Statut_candidat"] in (
            "PISTE_NON_VERIFIEE_ISIN_IDENTITE", "CONFLIT_ARCHIVES_EN_ATTENTE_DATA"
        )
        assert r["CIK_injecte"] == r["SSI_attribue"] == r["MCPA_attribue"] == "NON"
    # Exemples documentés d'homonymies : les codes de cotation allemands
    # ne désignent pas nécessairement les émetteurs américains SEC_BRIDGE.
    exemples = {r["Ticker_candidat"]: r for r in pistes}
    assert "Silver X Mining" in exemples["AGX.F"]["Nom_candidat"]
    assert "ARGAN INC" in exemples["AGX.F"]["Nom_emetteur_archives"]
    assert "Amber Grid" in exemples["AMH.F"]["Nom_candidat"]
    assert "American Homes 4 Rent" in exemples["AMH.F"]["Nom_emetteur_archives"]
    assert CANDIDATS.read_bytes() == avant, "Aucune mutation du registre SSI"
    print("SEC_BRIDGE : 24 pistes tracées, homonymies démontrées, 0 CIK injecté, 0 note")

if __name__ == "__main__":
    executer()

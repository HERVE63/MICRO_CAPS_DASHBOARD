"""Régression hors réseau : remplacement de preuve lié à l'émetteur, jamais au ticker seul.

Toutes les preuves et sociétés sont fictives. Aucune admission ni note réelle.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "SCRIPTS_ACTIFS"))
from preuves_ssi import CHAMPS, registre


def preuve(pid, ident, date, remplace=""):
    row = dict.fromkeys(CHAMPS, "")
    row.update(
        ID_preuve=pid, Remplace_ID=remplace, Ticker="COLLISION.F",
        Bloc="IDENTITE_SCE", Identifiant_emetteur=ident,
        Source_URL="https://example.org/fixture/" + pid,
        Type_source="DEPOT_REGLEMENTAIRE", Date_publication="2026-09-01",
        Fichier_brut="document_fixture.txt", SHA256=SHA,
        Statut_identite="VERIFIEE", Statut_verification="VERIFIEE",
        Verificateur="TEST_HORS_RESEAU",
        Date_verification_UTC=date, Justification="FICTION SANS VALIDATION REELLE",
    )
    return row


def executer():
    global SHA
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        d = base / "DONNEES"
        d.mkdir()
        document = base / "document_fixture.txt"
        document.write_bytes(b"DOCUMENT FICTIF SANS PREUVE PRIMAIRE")
        SHA = hashlib.sha256(document.read_bytes()).hexdigest()
        p = d / "REGISTRE_PREUVES_SSI.csv"
        old = preuve("P1", "ISIN:US0378331005", "2026-10-01T00:00:00Z")
        same = preuve("P2", "ISIN:US0378331005", "2026-10-02T00:00:00Z", "P1")
        pd.DataFrame([old, same]).to_csv(p, index=False)
        out = registre(base)
        assert set(out.ID_preuve) == {"P2"}, "Même émetteur : remplacement valide"
        # Même ticker et même bloc, mais émetteur différent : aucune substitution.
        other = preuve("P3", "CIK:0000000123", "2026-10-03T00:00:00Z", "P1")
        pd.DataFrame([old, other]).to_csv(p, index=False)
        before = p.read_bytes()
        try:
            registre(base)
        except RuntimeError as exc:
            assert "Remplacement de preuve incohérent" in str(exc), str(exc)
        else:
            raise AssertionError("Preuve d'un autre émetteur substituée par ticker")
        assert p.read_bytes() == before, "Registre source modifié"
        # Même identifiant mais autre ticker : également interdit.
        cross = dict(same)
        cross["Ticker"] = "AUTRE.F"
        pd.DataFrame([old, cross]).to_csv(p, index=False)
        try:
            registre(base)
        except RuntimeError as exc:
            assert "Remplacement de preuve incohérent" in str(exc)
        else:
            raise AssertionError("Preuve remplacée entre deux tickers")
    print("SSI : remplacement autorisé seulement à ticker, bloc et émetteur identiques")


if __name__ == "__main__":
    executer()

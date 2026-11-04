"""Régression hors réseau : aucune preuve SSI sur une vérification sans UTC explicite.

Fixtures entièrement fictives. Aucun score économique, aucun portefeuille modifié.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "SCRIPTS_ACTIFS"))
from preuves_ssi import CHAMPS, verifier, horodatage_verification_utc_strict


def test():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        brut = root / "fixture.bin"
        brut.write_bytes(b"PREUVE FICTIVE - TEST UTC HORS RESEAU")
        r = dict.fromkeys(CHAMPS, "")
        r.update(
            ID_preuve="TEST_UTC", Ticker="FIX.US", Bloc="B1",
            Identifiant_emetteur="CIK:0000001234",
            Source_URL="https://example.org/fixture",
            Type_source="DEPOT_REGLEMENTAIRE",
            Date_publication="2026-01-01",
            Fichier_brut=brut.name,
            SHA256=hashlib.sha256(brut.read_bytes()).hexdigest(),
            Statut_identite="VERIFIEE", Statut_verification="VERIFIEE",
            Verificateur="FIXTURE_INDEPENDANTE",
            Date_verification_UTC="2026-01-02T00:00:00Z",
            Justification="Fixture sans portée financière", Note="8",
        )
        avant = brut.read_bytes()
        for bon in ("2026-01-02T00:00:00Z", "2026-01-02T00:00:00+00:00"):
            r["Date_verification_UTC"] = bon
            assert horodatage_verification_utc_strict(bon)
            assert verifier(pd.Series(r), "FIX.US", "B1", root) == [], bon
        for mauvais in (
            "2026-01-02", "2026-01-02T00:00:00",
            "2026-01-02T01:00:00+01:00",
            "2026-01-02T00:00:00-00:00",
            "2026-02-30T00:00:00Z",
            "",
        ):
            r["Date_verification_UTC"] = mauvais
            assert not horodatage_verification_utc_strict(mauvais), mauvais
            assert any("UTC explicite" in e for e in verifier(
                pd.Series(r), "FIX.US", "B1", root)), mauvais
        r["Date_verification_UTC"] = "2999-01-01T00:00:00Z"
        assert horodatage_verification_utc_strict(r["Date_verification_UTC"])
        assert any("dates futures" in e for e in verifier(
            pd.Series(r), "FIX.US", "B1", root))
        assert brut.read_bytes() == avant
    print("07R : horodatages UTC explicites et documents fictifs SHA256 vérifiés")


if __name__ == "__main__":
    test()

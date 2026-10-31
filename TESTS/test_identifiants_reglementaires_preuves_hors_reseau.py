"""Validation ISO des identifiants de preuves SSI, hors réseau.

Les codes servent UNIQUEMENT aux tests de format/checksum : ils ne prouvent
aucune relation avec le ticker fictif, aucune identité ni aucun score.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "SCRIPTS_ACTIFS"))
from preuves_ssi import verifier

def executer():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        brut = root / "preuve_fixture.txt"
        brut.write_bytes(b"DOCUMENT FICTIF DE TEST, AUCUNE PREUVE REGLEMENTAIRE")
        sha = hashlib.sha256(brut.read_bytes()).hexdigest()
        r = dict(
            Ticker="FICTIF.TEST", Bloc="IDENTITE_SCE",
            Identifiant_emetteur="CIK:0000000123",
            Source_URL="https://example.org/fixture",
            Type_source="DEPOT_REGLEMENTAIRE",
            Date_publication="2026-01-01",
            Date_verification_UTC="2026-01-02T00:00:00+00:00",
            Fichier_brut="preuve_fixture.txt", SHA256=sha,
            Statut_identite="VERIFIEE", Statut_verification="VERIFIEE",
            Verificateur="TEST_FICTIF", Justification="TEST DE CHECKSUM UNIQUEMENT",
            Note=""
        )
        def erreurs(ident):
            return verifier(pd.Series({**r, "Identifiant_emetteur":ident}),
                            "FICTIF.TEST", "IDENTITE_SCE", root)
        # Ces valeurs ne sont que des exemples de controle de chiffres.
        for ident in ("CIK:0000000123", "ISIN:US0378331005",
                      "LEI:5493001KJTIIGC8Y1R12"):
            assert not erreurs(ident), (ident, erreurs(ident))
        for ident in ("CIK:123", "ISIN:US0378331006",
                      "LEI:5493001KJTIIGC8Y1R13",
                      "ISIN:US037833100", "LEI:5493001KJTIIGC8Y1R1!",
                      "ISIN:MANQUANTE", "MANQUANTE"):
            assert any("identifiant" in e for e in erreurs(ident)), (ident, erreurs(ident))
        alt = pd.Series({**r, "Identifiant_emetteur":"ISIN:US0378331005", "SHA256":"0"*64})
        assert "empreinte document divergente" in verifier(alt, "FICTIF.TEST", "IDENTITE_SCE", root)
    print("SSI identifiants: CIK, ISIN/Luhn et LEI/mod97 controles, SHA256 preserve")

if __name__ == "__main__":
    executer()

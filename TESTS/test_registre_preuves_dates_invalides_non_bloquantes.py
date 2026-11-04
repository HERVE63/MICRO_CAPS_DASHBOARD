"""Test hors réseau : une preuve à date invalide ne bloque pas les autres.

Aucune identité ni note réelle. Le registre fictif n'est jamais publié.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone
import hashlib
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "SCRIPTS_ACTIFS"))
from preuves_ssi import CHAMPS, registre, verifier


def test():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "DONNEES"
        data.mkdir()
        brut = root / "preuve_fictive.bin"
        brut.write_bytes(b"FICTION - AUCUNE DONNEE ECONOMIQUE")
        empreinte = hashlib.sha256(brut.read_bytes()).hexdigest()

        def preuve(ident, ticker, date, remplace=""):
            r = dict.fromkeys(CHAMPS, "")
            r.update(
                ID_preuve=ident, Remplace_ID=remplace, Ticker=ticker, Bloc="B1",
                Identifiant_emetteur="CIK:0000001234",
                Source_URL="https://example.org/fixture/" + ident,
                Type_source="DEPOT_REGLEMENTAIRE",
                Date_publication="2026-01-01",
                Fichier_brut=brut.name, SHA256=empreinte,
                Statut_identite="VERIFIEE", Statut_verification="VERIFIEE",
                Verificateur="TEST_FICTIF", Date_verification_UTC=date,
                Justification="Preuve fictive pour test de robustesse", Note="8",
            )
            return r

        lignes = [
            preuve("OK_A", "A.US", "2026-01-02T00:00:00Z"),
            preuve("MAUVAIS_B", "B.US", "date_invalide"),
            preuve("OLD_C", "C.US", "date_invalide"),
            preuve("NEW_C", "C.US", "2026-01-03T00:00:00Z", "OLD_C"),
            preuve("OLD_D", "D.US", "2026-01-02T00:00:00Z"),
            preuve("NEW_D", "D.US", "date_invalide", "OLD_D"),
        ]
        pd.DataFrame(lignes, columns=CHAMPS).to_csv(
            data / "REGISTRE_PREUVES_SSI.csv", index=False)
        preuves = registre(root, datetime(2026, 11, 1, tzinfo=timezone.utc))
        ids = set(preuves.ID_preuve)
        # Les dates invalides restent traçables et sont rejetées par verifier().
        assert {"OK_A", "MAUVAIS_B", "OLD_C", "OLD_D"} <= ids
        assert "NEW_C" not in ids and "NEW_D" not in ids, (
            "Remplacements aux dates non vérifiables exclus du registre ACTIF")
        assert verifier(preuves[preuves.ID_preuve.eq("OK_A")].iloc[0],
                        "A.US", "B1", root) == []
        assert any("dates" in e for e in verifier(
            preuves[preuves.ID_preuve.eq("MAUVAIS_B")].iloc[0],
            "B.US", "B1", root))
        # Un remplacement mal daté ne révoque jamais la preuve valide.
        assert "OLD_D" in ids
        # L'ordre d'une preuve historique mal datée est indémontrable :
        # aucun remplacement automatique, même si le nouveau est daté.
        assert "OLD_C" in ids
        assert brut.read_bytes() == b"FICTION - AUCUNE DONNEE ECONOMIQUE"
    print("SSI : dates invalides isolées, preuves saines conservées, aucune note créée")


if __name__ == "__main__":
    test()

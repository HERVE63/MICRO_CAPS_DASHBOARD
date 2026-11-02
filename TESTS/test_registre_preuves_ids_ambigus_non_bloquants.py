"""Non-régression SSI : ID de preuve dupliqués/vides isolés sans arrêt global.

Toutes les données sont fictives, sous TemporaryDirectory. Aucun score réel,
registre officiel, historique ou portefeuille n'est modifié.
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
        base = Path(tmp)
        data = base / "DONNEES"
        data.mkdir()
        brut = base / "document_fictif.bin"
        brut.write_bytes(b"TEST FICTIF - AUCUNE PREUVE ECONOMIQUE")
        empreinte = hashlib.sha256(brut.read_bytes()).hexdigest()

        def preuve(pid, ticker, remplace=""):
            row = dict.fromkeys(CHAMPS, "")
            row.update(
                ID_preuve=pid, Remplace_ID=remplace, Ticker=ticker, Bloc="B1",
                Identifiant_emetteur="CIK:0000000123",
                Source_URL="https://example.org/fixture/" + (pid or "vide"),
                Type_source="DEPOT_REGLEMENTAIRE",
                Date_publication="2026-10-01",
                Fichier_brut=brut.name, SHA256=empreinte,
                Statut_identite="VERIFIEE", Statut_verification="VERIFIEE",
                Verificateur="TEST_FICTIF",
                Date_verification_UTC="2026-10-02T00:00:00Z",
                Justification="Essai local sans certification", Note="8",
            )
            return row

        lignes = [
            preuve("SAIN_A", "SAIN_A.US"),
            preuve("SAIN_B", "SAIN_B.US"),
            preuve("AMBIGU", "DOUTE_A.US"),
            preuve("AMBIGU", "DOUTE_B.US"),
            preuve("", "SANS_ID.US"),
            preuve("MANQUANTE", "ID_MARQUEUR.US"),
            preuve("REMPLACE_AMBIGU", "DOUTE_A.US", "AMBIGU"),
        ]
        p = data / "REGISTRE_PREUVES_SSI.csv"
        pd.DataFrame(lignes, columns=CHAMPS).to_csv(p, index=False)
        avant = p.read_bytes()
        actifs = registre(base, datetime(2026, 11, 2, tzinfo=timezone.utc))
        ids = list(actifs.ID_preuve)
        assert ids == ["SAIN_A", "SAIN_B"], (
            "Seules les preuves saines et sans remplacement ambigu restent actives : " + repr(ids)
        )
        assert all(not verifier(actifs.iloc[i], ticker, "B1", base)
                   for i, ticker in enumerate(("SAIN_A.US", "SAIN_B.US")))
        assert p.read_bytes() == avant, "Le registre append-only a été modifié"
        assert brut.read_bytes() == b"TEST FICTIF - AUCUNE PREUVE ECONOMIQUE"
    print("SSI : IDs dupliqués/vides isolés, 2 preuves saines conservées, zéro admission réelle")


if __name__ == "__main__":
    test()

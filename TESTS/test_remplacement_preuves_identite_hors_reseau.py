"""SSI : remplacements invalides isolés, autres preuves conservées et exploitables.

Fixtures fictives hors réseau ; aucun score, émetteur ou ordre réel.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "SCRIPTS_ACTIFS"))
from preuves_ssi import CHAMPS, registre, verifier


def preuve(pid, ident, date, remplace="", ticker="COLLISION.F", bloc="IDENTITE_SCE"):
    row = dict.fromkeys(CHAMPS, "")
    row.update(
        ID_preuve=pid, Remplace_ID=remplace, Ticker=ticker,
        Bloc=bloc, Identifiant_emetteur=ident,
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
        sain = preuve("SAIN", "CIK:0000000123", "2026-10-03T00:00:00Z",
                     ticker="SAIN.US")
        def lire(lignes):
            pd.DataFrame(lignes, columns=CHAMPS).to_csv(p, index=False)
            avant = p.read_bytes()
            out = registre(base)
            assert p.read_bytes() == avant, "Le registre append-only a été modifié"
            assert "SAIN" in set(out.ID_preuve), "Un dossier sain ne doit jamais être bloqué"
            assert verifier(out[out.ID_preuve.eq("SAIN")].iloc[0],
                            "SAIN.US", "IDENTITE_SCE", base) == []
            return set(out.ID_preuve)

        assert lire([old, same, sain]) == {"P2", "SAIN"}, (
            "Même émetteur, même bloc, chronologie correcte : remplacement autorisé")
        concurrent = preuve("P9", "ISIN:US0378331005",
                            "2026-10-03T00:00:00Z", "P1")
        assert lire([old, same, concurrent, sain]) == {"P1", "SAIN"}, (
            "Deux revisions admissibles du meme parent sont ambiguës : "
            "garder P1 et exclure toutes les revisions concurrentes")
        assert lire([concurrent, old, sain, same]) == {"P1", "SAIN"}, (
            "L'issue ne doit pas dependre de l'ordre du CSV")
        descendant = preuve("P10", "ISIN:US0378331005",
                            "2026-10-04T00:00:00Z", "P2")
        assert lire([old, same, concurrent, descendant, sain]) == {"P1", "SAIN"}, (
            "Un descendant d'une revision concurrente en quarantaine "
            "ne doit pas contourner le rejet de son parent")


        # Une chaine valide P1 -> P2 -> P10 doit produire la meme preuve
        # active quelle que soit la permutation des lignes append-only.
        assert lire([old, same, descendant, sain]) == {"P10", "SAIN"}, (
            "Une chaine chronologique valide ne garde que la revision terminale")
        assert lire([old, descendant, same, sain]) == {"P10", "SAIN"}, (
            "La permutation des revisions ne doit pas ressusciter P1")
        assert lire([descendant, sain, old, same]) == {"P10", "SAIN"}, (
            "Une revision arrivee avant son parent dans le CSV reste admissible")

        other = preuve("P3", "CIK:0000000123", "2026-10-03T00:00:00Z", "P1")
        assert lire([old, other, sain]) == {"P1", "SAIN"}, (
            "Un émetteur homonyme ne doit ni remplacer P1 ni être actif")
        cross = preuve("P4", "ISIN:US0378331005", "2026-10-03T00:00:00Z",
                      "P1", ticker="AUTRE.F")
        assert lire([old, cross, sain]) == {"P1", "SAIN"}, (
            "Un autre ticker ne doit ni remplacer P1 ni être actif")
        ancien = preuve("P5", "ISIN:US0378331005",
                       "2026-09-30T00:00:00Z", "P1")
        assert lire([old, ancien, sain]) == {"P1", "SAIN"}, (
            "Une révision antérieure ne peut révoquer P1 ni arrêter le lot")
        egal = preuve("P6", "ISIN:US0378331005",
                     "2026-10-01T00:00:00Z", "P1")
        assert lire([old, egal, sain]) == {"P1", "SAIN"}, (
            "Une révision à la même seconde ne peut révoquer P1")
        orphelin = preuve("P7", "ISIN:US0378331005",
                         "2026-10-04T00:00:00Z", "INEXISTANT")
        assert lire([old, orphelin, sain]) == {"P1", "SAIN"}, (
            "Une référence manquante doit être isolée sans admission")
        invalide = preuve("P8", "ISIN:US0378331005",
                         "date_invalide", "P1")
        assert lire([old, invalide, sain]) == {"P1", "SAIN"}, (
            "Une date invalide ne doit pas révoquer P1")
        assert document.read_bytes() == b"DOCUMENT FICTIF SANS PREUVE PRIMAIRE"
    print("SSI : 10 scénarios de remplacement, preuves saines préservées, aucun arrêt global")


if __name__ == "__main__":
    executer()

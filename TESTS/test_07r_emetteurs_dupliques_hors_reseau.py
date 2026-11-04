"""07R: une identite reglementaire partagee ne peut pas produire deux challengers.
Test hors reseau, donnees fictives, aucune modification des donnees reelles.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def executer():
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        scripts = base / "SCRIPTS_ACTIFS"
        data = base / "DONNEES"
        scripts.mkdir()
        data.mkdir()
        for name in ("07R_VALIDER_NOTES_SSI.py", "preuves_ssi.py"):
            shutil.copy2(ROOT / "SCRIPTS_ACTIFS" / name, scripts / name)

        # Deux cotations par emetteur, l'une SEC, l'autre non-US ;
        # une identite distincte et un identifiant malforme doivent continuer.
        lignes = [
            ("CLASSA.US", "0000000123", ""),
            ("CLASSB.US", "0000000123", ""),
            ("LISTING1.F", "", "ISIN:FR001400A3Q3"),
            ("LISTING2.PA", "", "ISIN:FR001400A3Q3"),
            ("SAIN.US", "0000000456", ""),
            ("INVALIDE.US", "ABC", ""),
        ]
        rows = []
        for ticker, cik, ident in lignes:
            r = dict(Ticker=ticker, CIK=cik,
                     Identifiant_emetteur_verifie=ident,
                     SCE_valide="NON", Preuves_identite_SCE="MANQUANTE",
                     Conflit_identite_CIK="NON",
                     Decision_eliminatoire="A_VERIFIER",
                     Motif_eliminatoire="MANQUANTE")
            for bloc in ("B1", "B2", "B3", "B4", "B5", "B6", "B7"):
                r["Note_" + bloc] = "MANQUANTE"
                r["Preuve_" + bloc] = "MANQUANTE"
            rows.append(r)
        pd.DataFrame(rows).to_csv(
            data / "DOSSIERS_SSI_A_QUALIFIER.csv", index=False)

        run = subprocess.run(
            [sys.executable, "-B", str(scripts / "07R_VALIDER_NOTES_SSI.py")],
            cwd=base, capture_output=True, text=True)
        assert run.returncode == 0, (run.stdout, run.stderr)
        out = pd.read_csv(data / "RESULTATS_SSI.csv",
                          dtype=str, keep_default_na=False).set_index("Ticker")
        assert len(out) == len(lignes)
        for ticker in ("CLASSA.US", "CLASSB.US", "LISTING1.F", "LISTING2.PA"):
            r = out.loc[ticker]
            assert r.Statut_SSI == "EN_ATTENTE_DATA_EMETTEUR_DUPLIQUE", ticker
            assert r.SSI == "MANQUANTE", ticker
            assert r.Nombre_blocs_SSI_documentes == "0", ticker
            assert r.Portee_plafond == "NON_CALCULE_EMETTEUR_DUPLIQUE", ticker
        # Le traitement des autres societes n'est pas bloque.
        assert out.loc["SAIN.US", "Statut_SSI"] == "A_COMPLETER_PREUVES_SSI"
        assert out.loc["INVALIDE.US", "Statut_SSI"] == "EN_ATTENTE_DATA_IDENTITE_CIK"
        assert (out.SSI == "MANQUANTE").all()
        audit = pd.read_csv(data / "AUDIT_SSI.csv").iloc[0]
        assert int(audit.Dossiers) == 6
        assert int(audit.Dossiers_emetteur_duplique) == 4
        assert int(audit.Admis) == 0
        assert int(audit.Identites_CIK_en_quarantaine) == 1
    print("07R: 4 cotations d'emetteurs dupliques isolees, 2 dossiers independants traites, 0 score")


if __name__ == "__main__":
    executer()

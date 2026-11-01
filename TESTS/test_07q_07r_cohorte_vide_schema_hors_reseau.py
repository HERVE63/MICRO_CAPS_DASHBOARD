"""Régression 07Q/07R : cohorte vide ≠ schéma invalide.
Fixtures hors réseau ; aucun titre réel, aucune note, aucun ordre.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import shutil
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("07Q_PREPARER_DOSSIERS_SSI.py", "07R_VALIDER_NOTES_SSI.py", "preuves_ssi.py")


def executer():
    with TemporaryDirectory() as temp:
        base = Path(temp)
        scripts = base / "SCRIPTS_ACTIFS"
        data = base / "DONNEES"
        scripts.mkdir()
        data.mkdir()
        for name in MODULES:
            shutil.copy2(ROOT / "SCRIPTS_ACTIFS" / name, scripts / name)

        source = data / "CANDIDATS_PRETS_SSI.csv"
        pd.DataFrame(columns=["Ticker", "CIK", "Date_scan_fond"]).to_csv(source, index=False)
        before_source = source.read_bytes()

        def run(name):
            return subprocess.run([sys.executable, "-B", str(scripts / name)],
                                  cwd=base, text=True, capture_output=True)

        p = run(MODULES[0])
        assert p.returncode == 0, (p.stdout, p.stderr)
        assert source.read_bytes() == before_source
        dossiers = data / "DOSSIERS_SSI_A_QUALIFIER.csv"
        original_dossiers = dossiers.read_bytes()
        cols = set(pd.read_csv(dossiers, nrows=0).columns)
        mandatory = {"Ticker", "CIK", "SCE_valide", "Preuves_identite_SCE",
                     "Conflit_identite_CIK", "Decision_eliminatoire", "Motif_eliminatoire"}
        mandatory.update("Note_B" + str(i) for i in range(1, 8))
        mandatory.update("Preuve_B" + str(i) for i in range(1, 8))
        assert mandatory.issubset(cols), sorted(mandatory - cols)

        p = run(MODULES[1])
        assert p.returncode == 0, (p.stdout, p.stderr)
        assert dossiers.read_bytes() == original_dossiers
        output = data / "RESULTATS_SSI.csv"
        audit = data / "AUDIT_SSI.csv"
        result = pd.read_csv(output, dtype=str, keep_default_na=False)
        assert result.empty
        assert {"SSI", "Statut_SSI", "Motif_decision_SSI",
                "Portee_plafond", "Points_sur_blocs_documentes"}.issubset(result.columns)
        row = pd.read_csv(audit).iloc[0]
        assert int(row.Dossiers) == int(row.Admis) == 0
        good_output = output.read_bytes()
        good_audit = audit.read_bytes()

        # Une cohorte vide dont le champ de collision a disparu est un
        # incident de contrat, pas une qualification SSI réussie.
        pd.read_csv(dossiers, dtype=str).drop(columns=["Conflit_identite_CIK"]).to_csv(dossiers, index=False)
        p = run(MODULES[1])
        assert p.returncode != 0, "07R ne doit pas valider un schéma vide cassé"
        assert "Conflit_identite_CIK" in p.stderr
        assert output.read_bytes() == good_output, "Résultat valide écrasé après échec"
        assert audit.read_bytes() == good_audit, "Audit valide écrasé après échec"
    print("07Q/07R cohorte vide : schéma stable, fail-closed, aucune admission, sources intactes")


if __name__ == "__main__":
    executer()

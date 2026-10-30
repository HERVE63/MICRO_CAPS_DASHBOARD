"""Régression 07Q : une collision CIK ne doit jamais réutiliser les notes d'un autre émetteur."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SCRIPTS_ACTIFS/07Q_PREPARER_DOSSIERS_SSI.py"

def executer():
    with TemporaryDirectory() as d:
        base = Path(d)
        (base / "SCRIPTS_ACTIFS").mkdir()
        (base / "DONNEES").mkdir()
        shutil.copy2(SOURCE, base / "SCRIPTS_ACTIFS/07Q_PREPARER_DOSSIERS_SSI.py")
        candidats = []
        for ticker, cik in [("MEME", ""), ("COLLISION", "0000000999"), ("NOUVEAU", "0000000777")]:
            candidats.append(dict(Ticker=ticker, CIK=cik, Societe=ticker, Pays="USA",
                Capitalisation_EUR="10000000", Cash="100", Dette_totale="20",
                EBITDA="10", FCF="8", Croissance_CA="0.1", Marge_brute="0.3",
                Insiders_pct="0.05", Actions="1000000", Source_fondamentaux="SOURCE_TEST",
                Date_scan_fond="2026-10-01", Volume_monetaire_median_63s_local="200000",
                Momentum_3m_pct="1", Momentum_6m_pct="2", Au_dessus_MM200="OUI"))
        pd.DataFrame(candidats).to_csv(base / "DONNEES/CANDIDATS_PRETS_SSI.csv", index=False)
        anciens = [
            dict(Ticker="MEME", CIK="0000000123", Note_B1="12", Preuve_B1="PREUVE_MEME",
                 SCE_valide="OUI", Preuves_identite_SCE="A|B", Decision_eliminatoire="NON"),
            dict(Ticker="COLLISION", CIK="0000000456", Note_B1="15",
                 Preuve_B1="PREUVE_AUTRE_EMETTEUR", SCE_valide="OUI",
                 Preuves_identite_SCE="C|D", Decision_eliminatoire="NON"),
            dict(Ticker="NOUVEAU", CIK="", Note_B1="MANQUANTE",
                 Preuve_B1="MANQUANTE", SCE_valide="NON",
                 Preuves_identite_SCE="MANQUANTE", Decision_eliminatoire="A_VERIFIER"),
        ]
        pd.DataFrame(anciens).to_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv", index=False)
        p = subprocess.run([sys.executable, str(base / "SCRIPTS_ACTIFS/07Q_PREPARER_DOSSIERS_SSI.py")],
                           cwd=base, text=True, capture_output=True)
        assert p.returncode == 0, (p.stdout, p.stderr)
        result = pd.read_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv",
                             dtype=str, keep_default_na=False).set_index("Ticker")
        assert len(result) == 3
        assert result.loc["MEME", "CIK"] == ""
        assert result.loc["MEME", "Note_B1"] == "MANQUANTE"
        assert result.loc["MEME", "Preuve_B1"] == "MANQUANTE"
        assert result.loc["MEME", "SCE_valide"] == "NON"
        assert result.loc["MEME", "Statut_SSI"] == "EN_ATTENTE_DATA_IDENTITE_CIK"
        assert result.loc["MEME", "Conflit_identite_CIK"] == "NON"
        assert result.loc["COLLISION", "CIK"] == "0000000999"
        assert result.loc["COLLISION", "Conflit_identite_CIK"] == "OUI"
        assert result.loc["COLLISION", "Statut_SSI"] == "EN_ATTENTE_DATA_IDENTITE_CIK"
        assert result.loc["COLLISION", "Note_B1"] == "MANQUANTE"
        assert result.loc["COLLISION", "Preuve_B1"] == "MANQUANTE"
        assert result.loc["COLLISION", "SCE_valide"] == "NON"
        assert result.loc["COLLISION", "Preuves_identite_SCE"] == "MANQUANTE"
        assert result.loc["NOUVEAU", "CIK"] == "0000000777"
        audit = pd.read_csv(base / "DONNEES/AUDIT_DOSSIERS_SSI.csv")
        assert int(audit.Conflits_CIK.iloc[0]) == 1
        archives = list((base / "AUDITS/DOSSIERS_SSI").glob("*/DOSSIERS_SSI_A_QUALIFIER.csv"))
        assert len(archives) == 1
        assert pd.read_csv(archives[0], dtype=str, keep_default_na=False).loc[1, "CIK"] == "0000000456"
        # Une seconde régénération ne doit pas blanchir la collision initiale :
        # le CIK source et le CIK actif sont désormais identiques, mais
        # aucune preuve indépendante n'a été apportée pour lever le blocage.
        p2 = subprocess.run([sys.executable, str(base / "SCRIPTS_ACTIFS/07Q_PREPARER_DOSSIERS_SSI.py")],
                            cwd=base, text=True, capture_output=True)
        assert p2.returncode == 0, (p2.stdout, p2.stderr)
        deuxieme = pd.read_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv",
                               dtype=str, keep_default_na=False).set_index("Ticker")
        assert deuxieme.loc["COLLISION", "Conflit_identite_CIK"] == "OUI"
        assert deuxieme.loc["COLLISION", "Statut_SSI"] == "EN_ATTENTE_DATA_IDENTITE_CIK"
        assert deuxieme.loc["COLLISION", "Preuve_B1"] == "MANQUANTE"
        assert deuxieme.loc["MEME", "CIK"] == ""
        assert deuxieme.loc["MEME", "Statut_SSI"] == "EN_ATTENTE_DATA_IDENTITE_CIK"
        assert deuxieme.loc["MEME", "Preuve_B1"] == "MANQUANTE"
        assert len(deuxieme) == 3
        # Quand la source retrouve enfin le CIK, aucune ancienne note
        # ne doit etre restauree par simple coincidence du ticker.
        source = base / "DONNEES/CANDIDATS_PRETS_SSI.csv"
        recup = pd.read_csv(source, dtype=str, keep_default_na=False)
        recup.loc[recup.Ticker.eq("MEME"), "CIK"] = "0000000123"
        recup.to_csv(source, index=False)
        p3 = subprocess.run([sys.executable, str(base / "SCRIPTS_ACTIFS/07Q_PREPARER_DOSSIERS_SSI.py")],
                            cwd=base, text=True, capture_output=True)
        assert p3.returncode == 0, (p3.stdout, p3.stderr)
        troisieme = pd.read_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv",
                                dtype=str, keep_default_na=False).set_index("Ticker")
        assert troisieme.loc["MEME", "CIK"] == "0000000123"
        assert troisieme.loc["MEME", "Preuve_B1"] == "MANQUANTE"
        assert troisieme.loc["MEME", "Note_B1"] == "MANQUANTE"
        assert troisieme.loc["MEME", "SCE_valide"] == "NON"
        print("07Q OK : collision CIK et absence source isolees ; aucune ancienne note restauree")

if __name__ == "__main__":
    executer()

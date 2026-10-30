"""Test d'intégration isolé : 07M -> 07O -> 07Q -> 07R.
Aucune donnée officielle ni preuve primaire n'est modifiée.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import shutil
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ["07M_PREPARER_FILTRES_OBJECTIFS.py",
           "07O_CONTROLE_PRE_SSI.py",
           "07Q_PREPARER_DOSSIERS_SSI.py",
           "07R_VALIDER_NOTES_SSI.py", "preuves_ssi.py"]
DONNEES = ["UNIVERS_INVESTISSABLE_MICRO_CAPS.csv",
           "PRESELECTION_VARIABLES_MARCHE.csv",
           "FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv",
           "DOSSIERS_SSI_A_QUALIFIER.csv",
           "REGISTRE_PREUVES_SSI.csv"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def executer():
    originaux = [ROOT / "SCRIPTS_ACTIFS" / n for n in SCRIPTS]
    originaux += [ROOT / "DONNEES" / n for n in DONNEES]
    assert all(p.is_file() for p in originaux), "Entrée du test absente"
    avant = {str(p): sha(p) for p in originaux}

    with TemporaryDirectory() as repertoire:
        base = Path(repertoire)
        for nom in ("SCRIPTS_ACTIFS", "DONNEES"):
            (base / nom).mkdir()
        for n in SCRIPTS:
            shutil.copy2(ROOT / "SCRIPTS_ACTIFS" / n, base / "SCRIPTS_ACTIFS" / n)
        for n in DONNEES:
            shutil.copy2(ROOT / "DONNEES" / n, base / "DONNEES" / n)

        anciens = pd.read_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv",
                              dtype=str, keep_default_na=False)
        # Régression : les preuves d'identité SCE et le CIK doivent survivre
        # à 07Q, sans être considérés comme validés en l'absence des bruts.
        assert not anciens.empty
        anciens.loc[0, "CIK"] = "0000000123"
        anciens.loc[0, "SCE_valide"] = "OUI"
        anciens.loc[0, "Preuves_identite_SCE"] = "PREUVE_TEST_1|PREUVE_TEST_2"
        anciens.to_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv", index=False)
        annotations = {}
        for _, ligne in anciens.iterrows():
            champs = {c: ligne[c] for c in anciens
                      if c.startswith(("Note_", "Preuve_")) or
                      c in ("Decision_eliminatoire", "Motif_eliminatoire",
                            "CIK", "SCE_valide", "Preuves_identite_SCE")}
            annotations[ligne["Ticker"]] = champs

        for n in SCRIPTS[:4]:
            p = subprocess.run([sys.executable, str(base / "SCRIPTS_ACTIFS" / n)],
                               cwd=base, text=True, capture_output=True)
            assert p.returncode == 0, (n, p.stdout[-1200:], p.stderr[-1200:])

        nouveaux = pd.read_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv",
                               dtype=str, keep_default_na=False)
        resultat = pd.read_csv(base / "DONNEES/RESULTATS_SSI.csv",
                               dtype=str, keep_default_na=False)
        controle = pd.read_csv(base / "DONNEES/AUDIT_PRE_SSI.csv")
        assert len(nouveaux) == len(resultat) > 0
        assert nouveaux.Ticker.is_unique and resultat.Ticker.is_unique
        assert len(nouveaux) == int(controle.Prets_SSI.iloc[0])
        assert set(resultat.Statut_SSI).issubset(
            {"ADMIS_SSI", "REFUSE_SSI", "ELIMINE",
             "A_COMPLETER_PREUVES_SSI", "REFUSE_SSI_PLAFOND_VERIFIE"})
        # Les documents bruts ne sont PAS copiés dans ce test : aucune
        # admission ne doit être produite sur des références non vérifiables.
        assert not resultat.Statut_SSI.eq("ADMIS_SSI").any()
        assert {"CIK", "SCE_valide", "Preuves_identite_SCE"}.issubset(nouveaux.columns)
        assert nouveaux.loc[0, "SCE_valide"] == "OUI"
        assert nouveaux.loc[0, "CIK"] == "0000000123"
        assert nouveaux.loc[0, "Preuves_identite_SCE"] == "PREUVE_TEST_1|PREUVE_TEST_2"
        assert resultat.loc[0, "Statut_SSI"] != "ADMIS_SSI"
        for _, ligne in nouveaux.iterrows():
            if ligne.Ticker in annotations:
                for c, attendu in annotations[ligne.Ticker].items():
                    assert str(ligne[c]) == str(attendu), (ligne.Ticker, c)
        assert list((base / "AUDITS/DOSSIERS_SSI").glob("*/DOSSIERS_SSI_A_QUALIFIER.csv")), (
            "La préparation doit archiver l'ancien registre avant remplacement")
        print("CHAINE SSI ISOLEE OK :",
              len(nouveaux), "dossiers, aucune admission sans preuve brute")

    assert {str(p): sha(p) for p in originaux} == avant, (
        "Une entrée versionnée a été modifiée")


if __name__ == "__main__":
    executer()

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

        # Le filtre 07O peut changer la cohorte : choisir un ticker réellement
        # présent dans sa sortie, puis injecter des annotations dans l'ancien
        # registre temporaire afin de tester 07Q sans hypothèse d'ordre.
        for n in SCRIPTS[:2]:
            p = subprocess.run([sys.executable, str(base / "SCRIPTS_ACTIFS" / n)],
                               cwd=base, text=True, capture_output=True)
            assert p.returncode == 0, (n, p.stdout[-1200:], p.stderr[-1200:])
        candidats = pd.read_csv(base / "DONNEES/CANDIDATS_PRETS_SSI.csv",
                                dtype=str, keep_default_na=False)
        assert not candidats.empty
        assert len(candidats) >= 2
        ticker_test = candidats.iloc[0]["Ticker"]
        ticker_source = candidats.iloc[1]["Ticker"]
        # Un CIK issu de la collecte ne doit pas perdre ses zéros initiaux.
        candidats["CIK"] = ""
        # Identite presente dans la collecte : seules ces annotations peuvent
        # etre preservees. Les autres tickers restent en attente d'identite.
        candidats.loc[candidats.Ticker.eq(ticker_test), "CIK"] = "0000000123"
        candidats.loc[candidats.Ticker.eq(ticker_source), "CIK"] = "0000000456"
        candidats.to_csv(base / "DONNEES/CANDIDATS_PRETS_SSI.csv", index=False)
        anciens = pd.read_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv",
                              dtype=str, keep_default_na=False)
        # Second ticker sans annotation antérieure : reprendre le CIK source.
        anciens = anciens.loc[anciens.Ticker.ne(ticker_source)].copy()
        if not anciens.Ticker.eq(ticker_test).any():
            ajout = {c: "" for c in anciens.columns}
            ajout["Ticker"] = ticker_test
            anciens = pd.concat([anciens, pd.DataFrame([ajout])], ignore_index=True)
        masque = anciens.Ticker.eq(ticker_test)
        anciens.loc[masque, "CIK"] = "0000000123"
        anciens.loc[masque, "SCE_valide"] = "OUI"
        anciens.loc[masque, "Preuves_identite_SCE"] = "PREUVE_TEST_1|PREUVE_TEST_2"
        anciens = anciens.fillna("")
        anciens.to_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv", index=False)
        annotations = {}
        for _, ligne in anciens.iterrows():
            champs = {c: ligne[c] for c in anciens
                      if c.startswith(("Note_", "Preuve_")) or
                      c in ("Decision_eliminatoire", "Motif_eliminatoire",
                            "CIK", "SCE_valide", "Preuves_identite_SCE")}
            annotations[ligne["Ticker"]] = champs

        for n in SCRIPTS[2:4]:
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
             "A_COMPLETER_PREUVES_SSI", "REFUSE_SSI_PLAFOND_VERIFIE",
             "EN_ATTENTE_DATA_IDENTITE_CIK"})
        # Les documents bruts ne sont PAS copiés dans ce test : aucune
        # admission ne doit être produite sur des références non vérifiables.
        assert not resultat.Statut_SSI.eq("ADMIS_SSI").any()
        assert {"CIK", "SCE_valide", "Preuves_identite_SCE"}.issubset(nouveaux.columns)
        cible = nouveaux.loc[nouveaux.Ticker.eq(ticker_test)]
        assert len(cible) == 1, "Dossier de test absent après préparation"
        assert cible.iloc[0]["SCE_valide"] == "OUI"
        assert cible.iloc[0]["CIK"] == "0000000123"
        assert cible.iloc[0]["Preuves_identite_SCE"] == "PREUVE_TEST_1|PREUVE_TEST_2"
        assert nouveaux.loc[nouveaux.Ticker.eq(ticker_source), "CIK"].iloc[0] == "0000000456"
        assert resultat.loc[resultat.Ticker.eq(ticker_test), "Statut_SSI"].iloc[0] != "ADMIS_SSI"
        for _, ligne in nouveaux.iterrows():
            if ligne.Ticker == ticker_test:
                for champ, attendu in annotations[ticker_test].items():
                    assert str(ligne[champ]) == str(attendu), (ligne.Ticker, champ)
            elif ligne.Ticker in annotations and ligne.Ticker != ticker_source:
                # La collecte courante n'a pas de CIK pour ces tickers deja connus.
                # Ne pas recycler une ancienne preuve ou validation SCE.
                assert ligne.CIK in ("", "MANQUANTE")
                assert ligne.SCE_valide == "NON"
                assert ligne.Statut_SSI == "EN_ATTENTE_DATA_IDENTITE_CIK"
                assert all(ligne[champ] == "MANQUANTE" for champ in nouveaux.columns
                           if champ.startswith(("Note_", "Preuve_")))
        assert list((base / "AUDITS/DOSSIERS_SSI").glob("*/DOSSIERS_SSI_A_QUALIFIER.csv")), (
            "La préparation doit archiver l'ancien registre avant remplacement")
        # Incident de collecte : plus aucun candidat admissible. Le registre actif
        # doit être vidé (pas d'admission périmée), mais archivé sans perte.
        ancien_contenu = (base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv").read_bytes()
        archives_avant = set((base / "AUDITS/DOSSIERS_SSI").glob("*/DOSSIERS_SSI_A_QUALIFIER.csv"))
        candidats.iloc[0:0].to_csv(base / "DONNEES/CANDIDATS_PRETS_SSI.csv", index=False)
        p = subprocess.run([sys.executable, str(base / "SCRIPTS_ACTIFS/07Q_PREPARER_DOSSIERS_SSI.py")],
                           cwd=base, text=True, capture_output=True)
        assert p.returncode == 0, (p.stdout, p.stderr)
        archives_apres = set((base / "AUDITS/DOSSIERS_SSI").glob("*/DOSSIERS_SSI_A_QUALIFIER.csv"))
        nouvelles_archives = archives_apres - archives_avant
        assert len(nouvelles_archives) == 1
        assert next(iter(nouvelles_archives)).read_bytes() == ancien_contenu
        assert pd.read_csv(base / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv").empty
        p = subprocess.run([sys.executable, str(base / "SCRIPTS_ACTIFS/07R_VALIDER_NOTES_SSI.py")],
                           cwd=base, text=True, capture_output=True)
        assert p.returncode == 0, (p.stdout, p.stderr)
        assert pd.read_csv(base / "DONNEES/RESULTATS_SSI.csv").empty
        assert int(pd.read_csv(base / "DONNEES/AUDIT_SSI.csv").Dossiers.iloc[0]) == 0
        print("CHAINE SSI ISOLEE OK :", len(nouveaux),
              "dossiers, CIK préservé, cohorte vide archivée, aucune admission sans preuve brute")

    assert {str(p): sha(p) for p in originaux} == avant, (
        "Une entrée versionnée a été modifiée")


if __name__ == "__main__":
    executer()

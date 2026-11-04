"""07Q/07R : des doublons isolés ne bloquent jamais les autres microcaps.
Fixtures fictives, aucune donnée officielle, aucun score économique, aucune transaction.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("07Q_PREPARER_DOSSIERS_SSI.py", "07R_VALIDER_NOTES_SSI.py", "preuves_ssi.py")


def executer():
    with TemporaryDirectory() as temporaire:
        base = Path(temporaire)
        scripts = base / "SCRIPTS_ACTIFS"
        donnees = base / "DONNEES"
        scripts.mkdir()
        donnees.mkdir()
        for nom in MODULES:
            shutil.copy2(ROOT / "SCRIPTS_ACTIFS" / nom, scripts / nom)

        def candidat(ticker, cik):
            return dict(Ticker=ticker, CIK=cik, Societe="FIXTURE " + ticker,
                Pays="USA", Capitalisation_EUR="10000000", Cash="100",
                Dette_totale="20", EBITDA="10", FCF="8",
                Croissance_CA="0.1", Marge_brute="0.3",
                Insiders_pct="0.05", Actions="1000000",
                Source_fondamentaux="TEST_HORS_RESEAU",
                Date_scan_fond="2026-10-01",
                Volume_monetaire_median_63s_local="200000",
                Momentum_3m_pct="1", Momentum_6m_pct="2",
                Au_dessus_MM200="OUI")
        source = donnees / "CANDIDATS_PRETS_SSI.csv"
        pd.DataFrame([candidat("OK1", "0000000001"),
                      candidat("DUP", "0000000002"),
                      candidat("dup ", "0000000003"),
                      candidat(" ", ""),
                      candidat("OK2", "0000000004")]).to_csv(source, index=False)
        octets_source = source.read_bytes()
        ancien = donnees / "DOSSIERS_SSI_A_QUALIFIER.csv"
        pd.DataFrame([
            dict(Ticker="OK1", CIK="0000000001", Note_B1="5",
                 Preuve_B1="PREUVE_FICTIVE", SCE_valide="NON"),
            dict(Ticker="OK2", CIK="0000000004", Note_B1="18",
                 Preuve_B1="PREUVE_OBSOLETE_A", SCE_valide="OUI"),
            dict(Ticker="OK2", CIK="0000000005", Note_B1="19",
                 Preuve_B1="PREUVE_OBSOLETE_B", SCE_valide="OUI")
        ]).to_csv(ancien, index=False)
        octets_ancien = ancien.read_bytes()

        def lancer(nom):
            p = subprocess.run([sys.executable, "-B", str(scripts / nom)],
                               cwd=base, capture_output=True, text=True)
            assert p.returncode == 0, (nom, p.stdout, p.stderr)
        lancer(MODULES[0])
        assert source.read_bytes() == octets_source, "07Q a modifié les candidats source"
        sorties = pd.read_csv(ancien, dtype=str, keep_default_na=False)
        assert list(sorties.Ticker) == ["OK1", "OK2"], sorties.Ticker.tolist()
        ok1 = sorties.set_index("Ticker").loc["OK1"]
        ok2 = sorties.set_index("Ticker").loc["OK2"]
        assert ok1.Note_B1 == "5", "Annotation unique liée au CIK perdue"
        assert ok2.Note_B1 == "MANQUANTE", "Note d'un ancien ticker dupliqué réutilisée"
        assert ok2.Preuve_B1 == "MANQUANTE"
        assert ok2.SCE_valide == "NON"
        q = pd.read_csv(donnees / "QUARANTAINE_DOUBLONS_SSI.csv",
                        dtype=str, keep_default_na=False)
        assert len(q) == 3, q.to_dict("records")
        assert set(q.Statut) == {"EN_ATTENTE_DATA_IDENTITE_AMBIGUE"}
        assert int(q.loc[q.Ticker_normalise.eq("DUP"), "Lignes"].iloc[0]) == 2
        assert int(q.loc[q.Ticker_normalise.eq(""), "Lignes"].iloc[0]) == 1
        assert int(q.loc[(q.Ticker_normalise.eq("OK2")) &
                         (q.Origine.eq("DOSSIERS_SSI_HISTORIQUE")), "Lignes"].iloc[0]) == 2
        audit_q = pd.read_csv(donnees / "AUDIT_DOSSIERS_SSI.csv").iloc[0]
        assert int(audit_q.Dossiers_prets) == 2
        assert int(audit_q.Lignes_source_quarantaine) == 3
        assert int(audit_q.Lignes_ancien_registre_quarantaine) == 2
        archives = list((base / "AUDITS/DOSSIERS_SSI").glob("*/DOSSIERS_SSI_A_QUALIFIER.csv"))
        assert len(archives) == 1 and archives[0].read_bytes() == octets_ancien

        # Injection d'une anomalie en aval : 07R doit isoler uniquement OK1,
        # et continuer OK2, sans jamais afficher un score sur OK1.
        injection = pd.concat([sorties, sorties.iloc[[0]].copy(),
                               sorties.iloc[[0]].assign(Ticker=" ")],
                              ignore_index=True)
        injection.to_csv(ancien, index=False)
        octets_injection = ancien.read_bytes()
        lancer(MODULES[1])
        assert ancien.read_bytes() == octets_injection, "07R a modifié les dossiers"
        resultat = pd.read_csv(donnees / "RESULTATS_SSI.csv",
                               dtype=str, keep_default_na=False)
        ambigus = resultat.loc[resultat.Ticker.str.strip().isin(["OK1", ""])]
        assert len(ambigus) == 3
        assert set(ambigus.Statut_SSI) == {"EN_ATTENTE_DATA_IDENTITE_AMBIGUE"}
        assert set(ambigus.SSI) == {"MANQUANTE"}
        assert set(ambigus.Portee_plafond) == {"NON_CALCULE_IDENTITE_AMBIGUE"}
        sain = resultat.loc[resultat.Ticker.eq("OK2")]
        assert len(sain) == 1
        assert sain.iloc[0].Statut_SSI == "A_COMPLETER_PREUVES_SSI"
        assert sain.iloc[0].SSI == "MANQUANTE"
        audit_r = pd.read_csv(donnees / "AUDIT_SSI.csv").iloc[0]
        assert int(audit_r.Dossiers_identite_ambigue) == 3
        assert int(audit_r.Admis) == 0
        print("07Q/07R OK : 5 lignes source, 2 candidats traités, 3 quarantaines source, "
              "2 anciennes lignes isolées, 0 score, aucune mutation source")


if __name__ == "__main__":
    executer()

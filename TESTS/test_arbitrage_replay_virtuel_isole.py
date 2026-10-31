"""Test d'integration 09B -> 10 -> 05C, hors reseau et sans modifier les donnees officielles.
Les notes, prix et decisions sont exclusivement des fixtures SYNTHETIQUES DE TEST.
Aucune qualification SSI/MCPA reelle n'est revendiquee.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import os
import shutil
from types import SimpleNamespace

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def module(nom, fichier):
    spec = importlib.util.spec_from_file_location(nom, ROOT / "SCRIPTS_ACTIFS" / fichier)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def executer():
    duel = module("duel_test", "09B_DUEL_PROCHAIN_EURO.py")
    execu = module("execution_test", "10_EXECUTION_MENSUELLE.py")
    replay = module("replay_test", "05C_REPLAY_PORTEFEUILLE_GERE.py")
    with TemporaryDirectory() as d:
        tmp = Path(d)
        init = tmp / "ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
        journal = tmp / "JOURNAL_ARBITRAGES_GERE.csv"
        params = tmp / "PARAMETRES_ARBITRAGE_MICRO_CAPS.csv"
        revue = tmp / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv"
        shutil.copy2(ROOT / "DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv", init)
        shutil.copy2(ROOT / "DONNEES/JOURNAL_ARBITRAGES_GERE.csv", journal)
        shutil.copy2(ROOT / "CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv", params)
        original_journal = journal.read_bytes()
        original_initial = init.read_bytes()
        positions = pd.read_csv(init)
        assert len(positions) == 40
        assert abs(positions.Capital_initial_EUR.sum() - 4000) < 0.01
        identifiants = positions.ID_position.astype(str).tolist()
        source, destination = identifiants[:2]
        records = []
        for _, p in positions.iterrows():
            pid = str(p.ID_position)
            records.append({
                "Type": "TITULAIRE", "ID_position": pid,
                "Societe": p.Societe, "Ticker": p.Ticker, "Devise": p.Devise,
                "MCPA": 60 if pid == source else (90 if pid == destination else 80),
                "Decision": "VENDRE" if pid == source else ("RENFORCER" if pid == destination else "CONSERVER"),
                "Challengers_compares": "TEST_SYNTHETIQUE_NON_OFFICIEL",
            })
        records.append({
            "Type": "CHALLENGER", "ID_position": "TEST_ONLY_CHALLENGER",
            "Societe": "TEST SYNTHETIQUE", "Ticker": "TEST_ONLY", "Devise": "USD",
            "MCPA": 95, "Decision": "SONDE",
            "Challengers_compares": "TEST_SYNTHETIQUE_NON_OFFICIEL",
        })
        r = pd.DataFrame(records)
        r.to_csv(revue, index=False)
        duels = duel.calculer_duels(r)
        assert len(duels) == 1 and duels.iloc[0].ID_position_destination == "TEST_ONLY_CHALLENGER"
        replay.INITIAL = init
        replay.JOURNAL = journal
        replay.PARAMS_ARBITRAGE = params
        replay.OUTPUT = tmp / "REPLAY.csv"
        execu.JOURNAL = journal
        execu.REVUE = revue
        execu.PARAMS = params
        execu.COUVERTURE = tmp / "COUVERTURE_ARBITRAGE_GERE.csv"
        prix = SimpleNamespace(derniere_cloture_validee=lambda ticker, date: {"cours_cloture": 10.0})
        fx = SimpleNamespace(tous_les_fx=lambda date: {k: {"fx_vers_eur": 1.0}
                            for k in ("USD", "EUR", "GBP", "CAD", "SEK", "NOK", "CHF")})
        def charger(nom):
            if nom == "07AC_CONTROLER_T0.py":
                return SimpleNamespace(executer=lambda: True)
            if nom == "09B_DUEL_PROCHAIN_EURO.py":
                return SimpleNamespace(executer=lambda: duel.calculer_duels(pd.read_csv(revue)))
            if nom == "05C_REPLAY_PORTEFEUILLE_GERE.py":
                return replay
            if nom == "03A_MOTEUR_CLOTURES_V3.py":
                return prix
            if nom == "03B_MOTEUR_FX_V3.py":
                return fx
            raise AssertionError("Module non prevu dans ce test : " + nom)
        execu.charger = charger
        ancien_force = os.environ.get("MICRO_CAPS_FORCE_MENSUEL")
        os.environ["MICRO_CAPS_FORCE_MENSUEL"] = "1"
        try:
            # Sans revue valide : 40 lignes explicites EN_ATTENTE_DATA, zero ordre.
            pd.DataFrame(columns=r.columns).to_csv(revue, index=False)
            vide = execu.executer(dry_run=True)
            assert vide.empty
            couverture = pd.read_csv(execu.COUVERTURE)
            assert len(couverture) == 40
            assert set(couverture.Statut_MCPA) == {"EN_ATTENTE_DATA"}
            assert set(couverture.Operation_virtuelle) == {"NON"}
            assert journal.read_bytes() == original_journal
            r.to_csv(revue, index=False)
            operations = execu.executer(dry_run=True)
            assert len(operations) == 2, operations
            assert list(operations.Type_operation) == ["SORTIE", "ENTREE"]
            vente, achat = operations.iloc[0], operations.iloc[1]
            brut = float(vente.Quantite_vendue) * 10
            assert abs(float(vente.Frais_sortie_EUR) - brut * .025) < 1e-8
            net = brut * .975
            assert abs(float(vente.Capital_realise_EUR) - net) < 1e-8
            assert abs(float(achat.Montant_EUR) - net) < 1e-8
            assert abs(float(achat.Frais_entree_EUR) - net * .025 / 1.025) < 1e-8
            assert journal.read_bytes() == original_journal, "Dry run a modifie le journal"
            assert init.read_bytes() == original_initial, "Etat initial modifie"
            # Le replay du journal candidat est reel, sur une copie temporaire.
            pd.concat([pd.read_csv(journal), operations], ignore_index=True).to_csv(journal, index=False)
            etat = replay.executer()
            assert etat["nb_actives"] == 40 and etat["nb_sorties"] == 1
            assert len(etat["positions"]) == 41 and abs(etat["cash"]) < 0.01
            assert (etat["positions"].Ticker == "TEST_ONLY").sum() == 1
            assert init.read_bytes() == original_initial
            # Rotation inter-portefeuille : renforcer un titulaire, sans nouveau challenger.
            journal.write_bytes(original_journal)
            r[r.Type == "TITULAIRE"].to_csv(revue, index=False)
            intra = execu.executer(dry_run=True)
            assert len(intra) == 2 and list(intra.Type_operation) == ["SORTIE", "RENFORCEMENT"]
            assert str(intra.iloc[1].ID_ligne_entrante) == destination
            pd.concat([pd.read_csv(journal), intra], ignore_index=True).to_csv(journal, index=False)
            etat_intra = replay.executer()
            assert etat_intra["nb_actives"] == 39 and etat_intra["nb_sorties"] == 1
            q0 = float(positions.loc[positions.ID_position.astype(str) == destination, "Quantite"].iloc[0])
            q1 = float(etat_intra["positions"].loc[etat_intra["positions"].ID_position.astype(str) == destination, "Quantite"].iloc[0])
            assert q1 > q0 and abs(etat_intra["cash"]) < .01
            assert init.read_bytes() == original_initial
            r.to_csv(revue, index=False)
            # Cash preexistant positif : pas de blocage, mais pas d'investissement fictif de ce cash.
            journal.write_bytes(original_journal)
            execu.charger = lambda nom: (
                SimpleNamespace(executer=lambda: {"positions": positions, "cash": 5.0})
                if nom == "05C_REPLAY_PORTEFEUILLE_GERE.py" else charger(nom)
            )
            operations_cash = execu.executer(dry_run=True)
            assert len(operations_cash) == 2
            assert abs(float(operations_cash.iloc[1].Montant_EUR) - net) < 1e-8
            assert journal.read_bytes() == original_journal
            # Rejeter le cash negatif, jamais le normaliser en silence.
            execu.charger = lambda nom: (
                SimpleNamespace(executer=lambda: {"positions": positions, "cash": -1.0})
                if nom == "05C_REPLAY_PORTEFEUILLE_GERE.py" else charger(nom)
            )
            try:
                execu.executer(dry_run=True)
            except RuntimeError as exc:
                assert "negatif" in str(exc)
            else:
                raise AssertionError("Cash negatif non rejete")
            # Aucun RENFORCER ni SONDE admissible : 09B décide CASH.
            # 10 doit journaliser UNIQUEMENT la vente ; 05C conserve le cash.
            execu.charger = charger
            journal.write_bytes(original_journal)
            cash_revue = r[r.Type == "TITULAIRE"].copy()
            cash_revue.loc[cash_revue.ID_position != source, "Decision"] = "CONSERVER"
            cash_revue.to_csv(revue, index=False)
            cash_duel = duel.calculer_duels(cash_revue)
            assert len(cash_duel) == 1 and cash_duel.iloc[0].Statut_duel == "CASH"
            cash_ops = execu.executer(dry_run=True)
            assert len(cash_ops) == 1 and cash_ops.iloc[0].Type_operation == "SORTIE"
            assert journal.read_bytes() == original_journal
            pd.concat([pd.read_csv(journal), cash_ops], ignore_index=True).to_csv(journal, index=False)
            etat_cash = replay.executer()
            assert etat_cash["nb_actives"] == 39 and etat_cash["nb_sorties"] == 1
            assert abs(etat_cash["cash"] - net) < 1e-8
            assert init.read_bytes() == original_initial
            # Répartition incohérente : le module 10 doit refuser l'exécution.
            journal.write_bytes(original_journal)
            r.to_csv(revue, index=False)
            vrai_duel = duel.calculer_duels(r)
            faux_duel = vrai_duel.copy()
            faux_duel.loc[:, "Part_allocation"] = 0.5
            def charger_invalide(nom):
                if nom == "09B_DUEL_PROCHAIN_EURO.py":
                    return SimpleNamespace(executer=lambda: faux_duel)
                return charger(nom)
            execu.charger = charger_invalide
            try:
                execu.executer(dry_run=True)
            except RuntimeError as exc:
                assert "Répartition non équilibrée" in str(exc)
            else:
                raise AssertionError("Repartition incoherente non rejetee")
            assert journal.read_bytes() == original_journal
        finally:
            if ancien_force is None:
                os.environ.pop("MICRO_CAPS_FORCE_MENSUEL", None)
            else:
                os.environ["MICRO_CAPS_FORCE_MENSUEL"] = ancien_force
        print("09B -> 10 -> 05C OK : 40 positions, vente, entree, frais 2.5%, replay, cash residuel, refus cash negatif, aucune mutation officielle.")


    # Reception de la couverture reellement publiee, sans aucune note de test.
    couverture_officielle = ROOT / "DONNEES/COUVERTURE_ARBITRAGE_GERE.csv"
    revue_officielle = pd.read_csv(ROOT / "DONNEES/REVUE_HEBDOMADAIRE_MCPA_IPS.csv")
    journal_officiel = pd.read_csv(ROOT / "DONNEES/JOURNAL_ARBITRAGES_GERE.csv")
    if revue_officielle.empty and journal_officiel.empty and couverture_officielle.exists():
        couverture = pd.read_csv(couverture_officielle, dtype=str, keep_default_na=False)
        initiale = pd.read_csv(ROOT / "DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv", dtype=str)
        assert len(couverture) == 40
        assert set(couverture.ID_position) == set(initiale.ID_position)
        assert dict(zip(couverture.ID_position, couverture.Ticker)) == dict(zip(initiale.ID_position, initiale.Ticker))
        assert set(couverture.Statut_MCPA) == {"EN_ATTENTE_DATA"}
        assert set(couverture.Operation_virtuelle) == {"NON"}
        print("COUVERTURE REELLE VERIFIEE : 40 titulaires, aucune note ou operation inventee.")


if __name__ == "__main__":
    executer()

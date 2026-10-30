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
        finally:
            if ancien_force is None:
                os.environ.pop("MICRO_CAPS_FORCE_MENSUEL", None)
            else:
                os.environ["MICRO_CAPS_FORCE_MENSUEL"] = ancien_force
        print("09B -> 10 -> 05C OK : 40 positions, vente, entree, frais 2.5%, replay, cash residuel, refus cash negatif, aucune mutation officielle.")


if __name__ == "__main__":
    executer()

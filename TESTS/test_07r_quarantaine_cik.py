"""Regression 07R : quarantaine CIK prioritaire sur toute note SSI, sans mutation du dossier."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import importlib.util
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "SCRIPTS_ACTIFS/07R_VALIDER_NOTES_SSI.py"

def charger():
    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("ssi_07r_quarantaine_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def executer():
    module = charger()
    with TemporaryDirectory() as temp:
        data = Path(temp) / "DONNEES"
        data.mkdir()
        dossier = data / "DOSSIERS_SSI_A_QUALIFIER.csv"
        lignes = []
        for ticker, conflit, cik in [("COLLISION", "OUI", "0000000123"),
                                      ("SAIN", "NON", "0000000123"),
                                      ("SANS_CIK", "NON", ""),
                                      ("CIK_INVALIDE", "NON", "123")]:
            ligne = dict(Ticker=ticker, CIK=cik,
                         SCE_valide="OUI", Preuves_identite_SCE="ID1|ID2",
                         Decision_eliminatoire="NON", Motif_eliminatoire="EXCLUSION1",
                         Conflit_identite_CIK=conflit)
            for b in "B1 B2 B3 B4 B5 B6 B7".split():
                ligne["Note_" + b] = "10"
                ligne["Preuve_" + b] = "PREUVE_" + b
            lignes.append(ligne)
        pd.DataFrame(lignes).to_csv(dossier, index=False)
        avant = dossier.read_bytes()
        module.D = data
        module.SRC = dossier
        module.OUT = data / "RESULTATS_SSI.csv"
        module.AUD = data / "AUDIT_SSI.csv"
        appeles = []
        def valider(r, *args):
            appeles.append(r["Ticker"])
            return [10] * 7, []
        def bilan(*args):
            return {"Nombre_blocs_SSI_documentes": 7,
                    "Plafond_SSI_si_blocs_restants_maximaux": 70}
        with patch.object(module, "registre", return_value=pd.DataFrame()), \
             patch.object(module, "valider_dossier", side_effect=valider), \
             patch.object(module, "bilan_blocs_documentes", side_effect=bilan):
            module.executer()
        resultat = pd.read_csv(module.OUT, dtype=str, keep_default_na=False).set_index("Ticker")
        assert resultat.loc["COLLISION", "SSI"] == "MANQUANTE"
        assert resultat.loc["COLLISION", "Statut_SSI"] == "EN_ATTENTE_DATA_IDENTITE_CIK"
        for ticker in ("SANS_CIK", "CIK_INVALIDE"):
            assert resultat.loc[ticker, "SSI"] == "MANQUANTE"
            assert resultat.loc[ticker, "Statut_SSI"] == "EN_ATTENTE_DATA_IDENTITE_CIK"
        assert resultat.loc["SAIN", "SSI"] == "70"
        assert resultat.loc["SAIN", "Statut_SSI"] == "ADMIS_SSI"
        assert appeles == ["SAIN"], "Les dossiers sans CIK valide ou en collision ne doivent pas etre notes"
        audit = pd.read_csv(module.AUD)
        assert int(audit.loc[0, "Identites_CIK_en_quarantaine"]) == 3
        assert int(audit.loc[0, "Admis"]) == 1
        assert dossier.read_bytes() == avant, "07R ne doit pas modifier le registre source"
        # Une ancienne cohorte sans champs d'identite ne doit jamais contourner
        # verifier_identite_sce() ou le verrou Conflit_identite_CIK.
        sortie_avant = module.OUT.read_bytes()
        audit_avant = module.AUD.read_bytes()
        for champ in ("CIK", "SCE_valide", "Preuves_identite_SCE", "Conflit_identite_CIK"):
            pd.DataFrame(lignes).drop(columns=[champ]).to_csv(dossier, index=False)
            try:
                module.executer()
            except RuntimeError as exc:
                assert "Schema dossier SSI incomplet" in str(exc), (champ, str(exc))
                assert champ in str(exc), (champ, str(exc))
            else:
                raise AssertionError("07R a accepte un dossier sans " + champ)
            assert module.OUT.read_bytes() == sortie_avant, "Sortie modifiee malgre schema invalide"
            assert module.AUD.read_bytes() == audit_avant, "Audit modifie malgre schema invalide"
        # Defense en profondeur : le validateur commun ne doit pas sauter
        # l'identite SCE lorsqu'il est invoque sans passer par 07R.
        sans_sce = pd.Series({
            "Ticker": "SANS_SCE", "CIK": "0000000123",
            "Decision_eliminatoire": "NON", "Motif_eliminatoire": "MANQUANTE",
            **{"Preuve_" + b: "MANQUANTE" for b in "B1 B2 B3 B4 B5 B6 B7".split()},
        })
        _, erreurs = module.valider_dossier(
            sans_sce, pd.DataFrame(columns=["ID_preuve"]), Path(temp))
        assert "contrôles SCE non validés" in erreurs, erreurs
        # Defense en profondeur : un appel DIRECT au validateur commun ne
        # doit pas accepter une collision CIK, meme avec toutes les preuves
        # simulées comme valides. Les notes ci-dessous sont des fixtures de
        # test uniquement, sans rapport avec des societes ou des scores reels.
        lignes_preuves = [
            {"ID_preuve": ident, "Source_URL": "https://source.example/" + ident,
             "Identifiant_emetteur": "CIK:0000000123", "Note": "1"}
            for ident in ["SCE1", "SCE2", "EX1", "B1P", "B2P", "B3P",
                          "B4P", "B5P", "B6P", "B7P"]
        ]
        preuves_simulees = pd.DataFrame(lignes_preuves)
        dossier_direct = pd.Series({
            "Ticker": "FIXTURE", "CIK": "0000000123",
            "SCE_valide": "OUI", "Preuves_identite_SCE": "SCE1|SCE2",
            "Conflit_identite_CIK": "NON",
            "Decision_eliminatoire": "NON", "Motif_eliminatoire": "EX1",
            **{"Note_" + b: "1" for b in "B1 B2 B3 B4 B5 B6 B7".split()},
            **{"Preuve_" + b: b + "P" for b in "B1 B2 B3 B4 B5 B6 B7".split()},
        })
        with patch("preuves_ssi.verifier", return_value=[]):
            notes, erreurs = module.valider_dossier(
                dossier_direct, preuves_simulees, Path(temp))
            assert notes == [1] * 7 and not erreurs, (notes, erreurs)
            for statut in ("OUI", "", "INCONNU"):
                dossier_direct["Conflit_identite_CIK"] = statut
                _, erreurs = module.valider_dossier(
                    dossier_direct, preuves_simulees, Path(temp))
                assert any("collision CIK" in e for e in erreurs), (statut, erreurs)
            dossier_direct.drop(labels=["Conflit_identite_CIK"], inplace=True)
            _, erreurs = module.valider_dossier(
                dossier_direct, preuves_simulees, Path(temp))
            assert any("collision CIK" in e for e in erreurs), erreurs
        dossier.write_bytes(avant)
    print("07R OK : collision, CIK absent/invalide, schema SCE et validateur proteges")

if __name__ == "__main__":
    executer()

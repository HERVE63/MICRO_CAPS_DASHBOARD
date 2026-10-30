"""Regression SSI 07R : une exclusion ne peut viser un autre emetteur.
Fixtures artificielles, sans notation financiere ni effet sur le portefeuille.
"""
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
    spec = importlib.util.spec_from_file_location("test_07r_exclusion_cik", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test():
    m = charger()
    with TemporaryDirectory() as temp:
        d = Path(temp) / "DONNEES"
        d.mkdir()
        src = d / "DOSSIERS_SSI_A_QUALIFIER.csv"
        lignes = []
        for ticker in ("CIBLE_TEST", "AUTRE_TEST"):
            row = {
                "Ticker": ticker, "CIK": "0000000123",
                "SCE_valide": "OUI", "Preuves_identite_SCE": "ID_A|ID_B",
                "Conflit_identite_CIK": "NON",
                "Decision_eliminatoire": "OUI" if ticker == "CIBLE_TEST" else "A_VERIFIER",
                "Motif_eliminatoire": "EXCLUSION_TEST" if ticker == "CIBLE_TEST" else "MANQUANTE",
            }
            for bloc in ("B1", "B2", "B3", "B4", "B5", "B6", "B7"):
                row["Note_" + bloc] = "MANQUANTE"
                row["Preuve_" + bloc] = "MANQUANTE"
            lignes.append(row)
        preuve = {
            "ID_preuve": "EXCLUSION_TEST", "Ticker": "CIBLE_TEST",
            "Bloc": "EXCLUSIONS", "Identifiant_emetteur": "CIK:0000009999"
        }
        m.D, m.SRC, m.OUT, m.AUD = (
            d, src, d / "RESULTATS_SSI.csv", d / "AUDIT_SSI.csv"
        )

        def execution(identifiant, sce_valide=True, collision=False):
            lignes[0]["Conflit_identite_CIK"] = "OUI" if collision else "NON"
            pd.DataFrame(lignes).to_csv(src, index=False)
            avant = src.read_bytes()
            preuve["Identifiant_emetteur"] = identifiant
            reg = pd.DataFrame([preuve])
            with patch.object(m, "registre", return_value=reg), \\
                 patch.object(m, "valider_dossier", return_value=([], ["blocs incomplets"])), \\
                 patch.object(m, "bilan_blocs_documentes", return_value={
                     "Nombre_blocs_SSI_documentes": 0,
                     "Plafond_SSI_si_blocs_restants_maximaux": 100
                 }), \\
                 patch.object(m, "verifier_identite_sce",
                              return_value=[] if sce_valide else ["SCE non prouve"]), \\
                 patch("preuves_ssi.verifier", return_value=[]):
                m.executer()
            assert src.read_bytes() == avant, "Le registre source ne doit pas etre modifie"
            result = pd.read_csv(m.OUT, dtype=str, keep_default_na=False).set_index("Ticker")
            assert result.loc["AUTRE_TEST", "Statut_SSI"] == "A_COMPLETER_PREUVES_SSI"
            assert result.loc["AUTRE_TEST", "SSI"] == "MANQUANTE"
            return result.loc["CIBLE_TEST", "Statut_SSI"]

        assert execution("CIK:0000009999") == "A_COMPLETER_PREUVES_SSI"
        assert execution("CIK:0000000123", sce_valide=False) == "A_COMPLETER_PREUVES_SSI"
        assert execution("CIK:0000000123") == "ELIMINE"
        assert execution("CIK:0000000123", collision=True) == "EN_ATTENTE_DATA_IDENTITE_CIK"
    print("07R: exclusion exige CIK exact + SCE valide, quarantaine prioritaire, autres dossiers poursuivis")


if __name__ == "__main__":
    test()

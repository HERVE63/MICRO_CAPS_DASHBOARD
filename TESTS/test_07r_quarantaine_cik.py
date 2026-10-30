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
        for ticker, conflit in [("COLLISION", "OUI"), ("SAIN", "NON")]:
            ligne = dict(Ticker=ticker, CIK="0000000123",
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
        assert resultat.loc["SAIN", "SSI"] == "70"
        assert resultat.loc["SAIN", "Statut_SSI"] == "ADMIS_SSI"
        assert appeles == ["SAIN"], "Le dossier en quarantaine ne doit meme pas etre note"
        audit = pd.read_csv(module.AUD)
        assert int(audit.loc[0, "Identites_CIK_en_quarantaine"]) == 1
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
        dossier.write_bytes(avant)
    print("07R OK : collision bloquee, schema SCE/CIK obligatoire, sorties preservees")

if __name__ == "__main__":
    executer()

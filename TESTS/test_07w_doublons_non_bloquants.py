"""07W : les doublons SSI/SEC sont quarantaines, les dossiers valides continuent.
Test hors reseau, uniquement en repertoire temporaire, aucune note inventee.
"""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rapprochement_07w_isole", ROOT / "SCRIPTS_ACTIFS/07W_RAPPROCHER_PREUVES_SEC_SSI.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def executer():
    with TemporaryDirectory() as tmp:
        d = Path(tmp)
        dossiers = [
            {"Ticker":"BON", "CIK":"0000000123", "Societe":"Bon", "Note_B1":"MANQUANTE"},
            {"Ticker":"DUP", "CIK":"0000000222", "Societe":"Doublon A", "Note_B1":"MANQUANTE"},
            {"Ticker":"dup ", "CIK":"0000000333", "Societe":"Doublon B", "Note_B1":"MANQUANTE"},
            {"Ticker":"SEC_DUP", "CIK":"0000000444", "Societe":"SEC double", "Note_B1":"MANQUANTE"},
            {"Ticker":"CIK_FAUX", "CIK":"0000000555", "Societe":"CIK divergent", "Note_B1":"MANQUANTE"},
        ]
        sec = [
            {"Ticker":"BON", "CIK":"123", "Statut_SEC":"IDENTITE_VERIFIEE", "CIK_verifie":"OUI"},
            {"Ticker":"DUP", "CIK":"222", "Statut_SEC":"IDENTITE_VERIFIEE", "CIK_verifie":"OUI"},
            {"Ticker":"SEC_DUP", "CIK":"444", "Statut_SEC":"IDENTITE_VERIFIEE", "CIK_verifie":"OUI"},
            {"Ticker":"sec_dup ", "CIK":"666", "Statut_SEC":"IDENTITE_VERIFIEE", "CIK_verifie":"OUI"},
            {"Ticker":"CIK_FAUX", "CIK":"999", "Statut_SEC":"IDENTITE_VERIFIEE", "CIK_verifie":"OUI"},
        ]
        faits = []
        for ticker,cik in [("BON","123"),("DUP","222"),("SEC_DUP","444"),("CIK_FAUX","555")]:
            faits.append({"Ticker":ticker,"CIK":cik,"Concept":"Cash","Valeur":"100",
                "Unite":"USD","Fin_periode":"2026-06-30","Date_depot":"2026-08-01",
                "Source_officielle":"https://data.sec.gov/exemple",
                "Statut_comparabilite":"FORMAT_A_VERIFIER"})
        for name,rows in [
            ("DOSSIERS_SSI_A_QUALIFIER.csv",dossiers),
            ("PREUVES_SEC_EDGAR_SSI.csv",sec),
            ("FAITS_SEC_COMPARABLES_SSI.csv",faits),
        ]:
            pd.DataFrame(rows).to_csv(d/name,index=False)
        with patch.object(mod,"DOS",d/"DOSSIERS_SSI_A_QUALIFIER.csv"), \
             patch.object(mod,"SEC",d/"PREUVES_SEC_EDGAR_SSI.csv"), \
             patch.object(mod,"FACT",d/"FAITS_SEC_COMPARABLES_SSI.csv"), \
             patch.object(mod,"OUT",d/"RAPPROCHEMENT_PREUVES_SEC_SSI.csv"), \
             patch.object(mod,"AUD",d/"AUDIT_RAPPROCHEMENT_SEC_SSI.csv"), \
             patch.object(mod,"QUAR",d/"QUARANTAINE_RAPPROCHEMENT_SEC_SSI.csv"):
            valides=mod.executer()
        assert len(valides)==1 and valides[0]["Ticker"]=="BON"
        assert valides[0]["Note_SSI_attribuee"]=="NON"
        q=pd.read_csv(d/"QUARANTAINE_RAPPROCHEMENT_SEC_SSI.csv",dtype=str,keep_default_na=False)
        assert set(q.Ticker)=={"DUP","SEC_DUP","CIK_FAUX"}
        assert set(q.loc[q.Statut=="EN_ATTENTE_DATA_IDENTITE_AMBIGUE","Ticker"])=={"DUP","SEC_DUP"}
        assert set(q.loc[q.Statut=="EN_ATTENTE_DATA_IDENTITE_CIK","Ticker"])=={"CIK_FAUX"}
        audit=pd.read_csv(d/"AUDIT_RAPPROCHEMENT_SEC_SSI.csv")
        assert int(audit.at[0,"Faits_en_quarantaine_identite_ambigue"])==2
        assert int(audit.at[0,"Faits_en_quarantaine_identite_CIK"])==1
        assert int(audit.at[0,"Dossiers_identite_ambigue"])==1
        assert int(audit.at[0,"Registre_SEC_identite_ambigue"])==1
        assert int(audit.at[0,"Notes_SSI_attribuees"])==0
        originaux=pd.read_csv(d/"DOSSIERS_SSI_A_QUALIFIER.csv",dtype=str,keep_default_na=False)
        assert len(originaux)==5 and originaux.Note_B1.eq("MANQUANTE").all()
        print("07W OK : 1 valide, 2 identites ambigues et 1 CIK divergent en quarantaine ; aucune note.")


if __name__=="__main__":
    executer()

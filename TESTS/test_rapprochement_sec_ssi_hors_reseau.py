"""Test hors reseau: rapprochement SEC vers blocs SSI, sans notation."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("sec_rapprochement",ROOT/"SCRIPTS_ACTIFS/07W_RAPPROCHER_PREUVES_SEC_SSI.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test():
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  pd.DataFrame([{"Ticker":"TEST","Societe":"Test Inc","Note_B1":"MANQUANTE"},
                {"Ticker":"AUTRE","Societe":"Autre Inc","Note_B1":"MANQUANTE"}]).to_csv(d/"DOSSIERS_SSI_A_QUALIFIER.csv",index=False)
  pd.DataFrame([{"Ticker":"TEST","CIK":"0000001234","Statut_SEC":"A_VERIFIER_IDENTITE_ET_CONTENU","CIK_verifie":"NON"},
                {"Ticker":"AUTRE","CIK":"0000009876","Statut_SEC":"NON_COUVERT","CIK_verifie":"NON"}]).to_csv(d/"PREUVES_SEC_EDGAR_SSI.csv",index=False)
  pd.DataFrame([
   {"Ticker":"TEST","CIK":"0000001234","Concept":"Cash","Valeur":"120000","Unite":"USD",
    "Fin_periode":"2025-12-31","Date_depot":"2026-02-01","Source_officielle":"https://data.sec.gov/a",
    "Statut_comparabilite":"FORMAT_PERIODE_PLAUSIBLE_A_VERIFIER"},
   {"Ticker":"TEST","CIK":"0000009999","Concept":"Revenues","Valeur":"999","Unite":"USD",
    "Fin_periode":"2025-12-31","Date_depot":"2026-02-01","Source_officielle":"https://data.sec.gov/b",
    "Statut_comparabilite":"FORMAT_PERIODE_PLAUSIBLE_A_VERIFIER"},
   {"Ticker":"INCONNU","CIK":"0000003333","Concept":"Cash","Valeur":"5","Unite":"USD",
    "Fin_periode":"2025-12-31","Date_depot":"2026-02-01","Source_officielle":"https://data.sec.gov/c",
    "Statut_comparabilite":"FORMAT_PERIODE_PLAUSIBLE_A_VERIFIER"}]).to_csv(d/"FAITS_SEC_COMPARABLES_SSI.csv",index=False)
  with patch.object(mod,"D",d),patch.object(mod,"DOS",d/"DOSSIERS_SSI_A_QUALIFIER.csv"),patch.object(mod,"SEC",d/"PREUVES_SEC_EDGAR_SSI.csv"),patch.object(mod,"FACT",d/"FAITS_SEC_COMPARABLES_SSI.csv"),patch.object(mod,"OUT",d/"RAPPROCHEMENT_PREUVES_SEC_SSI.csv"),patch.object(mod,"AUD",d/"AUDIT_RAPPROCHEMENT_SEC_SSI.csv"):
   result=mod.executer()
  assert len(result)==1
  assert result[0]["Bloc_SSI_cible"]=="B1"
  assert result[0]["Statut_preuve"]=="A_VERIFIER_IDENTITE_ET_DOCUMENT"
  assert result[0]["Note_SSI_attribuee"]=="NON"
  assert pd.read_csv(d/"DOSSIERS_SSI_A_QUALIFIER.csv",dtype=str).loc[0,"Note_B1"]=="MANQUANTE"
  print("TEST RAPPROCHEMENT OK: CIK coherent, bloc B1, aucune note, dossier intact")
if __name__=="__main__":test()

"""Tests hors reseau du filtre de comparabilite SEC, sans score SSI."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("sec_normalisation",ROOT/"SCRIPTS_ACTIFS/07V_NORMALISER_FAITS_SEC.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def test():
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  base={"Ticker":"TEST","CIK":"0000001234","Concept":"Revenues",
   "Tag_SEC":"Revenues","Unite":"USD","Debut_periode":"2025-01-01",
   "Fin_periode":"2025-12-31","Formulaire":"10-K","Accession":"A1",
   "Exercice":"2025","Periode":"FY","Source_officielle":"https://data.sec.gov/example",
   "Date_collecte_UTC":"2026-10-01T00:00:00+00:00","Statut_preuve":"A_VERIFIER"}
  rows=[
   dict(base,Valeur="100",Date_depot="2026-02-01"),
   dict(base,Valeur="110",Date_depot="2026-03-01",Accession="A2"),
   dict(base,Valeur="999",Date_depot="2026-03-02",Debut_periode="2025-01-01",Fin_periode="2025-06-30"),
   dict(base,Valeur="1",Date_depot="2026-03-03",Unite="shares")]
  pd.DataFrame(rows).to_csv(d/"FAITS_FINANCIERS_SEC_SSI.csv",index=False)
  with patch.object(mod,"D",d),patch.object(mod,"SRC",d/"FAITS_FINANCIERS_SEC_SSI.csv"),patch.object(mod,"OUT",d/"FAITS_SEC_COMPARABLES_SSI.csv"),patch.object(mod,"AUD",d/"AUDIT_COMPARABILITE_SEC_SSI.csv"),patch.object(mod,"SRC",d/"FAITS_FINANCIERS_SEC_SSI.csv"),patch.object(mod,"OUT",d/"FAITS_SEC_COMPARABLES_SSI.csv"),patch.object(mod,"AUD",d/"AUDIT_COMPARABILITE_SEC_SSI.csv"):
   result=mod.executer()
  assert len(result)==1
  assert result.iloc[0]["Valeur"]=="110"
  assert result.iloc[0]["Cadence"]=="ANNUEL"
  assert result.iloc[0]["Statut_comparabilite"]=="FORMAT_PERIODE_PLAUSIBLE_A_VERIFIER"
  a=pd.read_csv(d/"AUDIT_COMPARABILITE_SEC_SSI.csv")
  assert int(a.iloc[0]["Faits_ecartes"])==3
  print("TEST NORMALISATION OK: periode, unite, doublon, provenance, aucune note SSI")
if __name__=="__main__":test()

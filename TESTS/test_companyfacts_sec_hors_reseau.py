"""Test hors reseau de la collecte XBRL SEC, periodes, unites et identite."""
import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("companyfacts_ssi",ROOT/"SCRIPTS_ACTIFS/07U_COLLECTE_COMPANYFACTS_SEC.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def faux_json(url,agent):
 if "CIK0000001234.json" not in url: raise AssertionError(url)
 return {"cik":1234,"facts":{"us-gaap":{
  "CashAndCashEquivalentsAtCarryingValue":{"units":{"USD":[
   {"val":250000,"end":"2026-06-30","filed":"2026-08-01","form":"10-Q","accn":"0001"},
   {"val":200000,"end":"2025-12-31","filed":"2026-01-01","form":"10-K","accn":"0002"},
   {"val":100,"end":"2024-12-31","filed":"2025-01-01","form":"OTHER"}]}}}}}

def test():
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  pd.DataFrame([
   {"Ticker":"TEST","CIK":"0000001234","Statut_SEC":"A_VERIFIER_IDENTITE_ET_CONTENU"},
   {"Ticker":"UNKNOWN","CIK":"MANQUANTE","Statut_SEC":"NON_COUVERT"}]).to_csv(d/"PREUVES_SEC_EDGAR_SSI.csv",index=False)
  with patch.object(mod,"D",d),patch.object(mod,"lire_json",side_effect=faux_json),patch.object(mod.time,"sleep"),patch.dict(os.environ,{"SEC_USER_AGENT":"Research contact@example.org"}):
   rows=mod.executer()
  assert len(rows)==2
  assert all(r["Unite"]=="USD" for r in rows)
  assert all(r["Statut_preuve"]=="A_VERIFIER_IDENTITE_ET_PERIODE" for r in rows)
  assert {r["Fin_periode"] for r in rows}=={"2026-06-30","2025-12-31"}
  audit=pd.read_csv(d/"AUDIT_FAITS_FINANCIERS_SEC_SSI.csv")
  assert audit.set_index("Ticker").loc["UNKNOWN","Statut"]=="NON_COUVERT_OU_IDENTITE_AMBIGUE"
  print("TEST XBRL OK: 2 faits, unites, periodes, source, non-couverture")
if __name__=="__main__": test()

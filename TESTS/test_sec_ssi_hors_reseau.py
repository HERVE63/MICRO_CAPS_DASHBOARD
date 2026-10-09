"""Tests hors reseau du raccordement SEC: aucune cle ni donnee reelle requise."""
import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sec_ssi",ROOT/"SCRIPTS_ACTIFS/07T_ENRICHIR_PREUVES_SEC_EDGAR.py")
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

def faux_json(url,agent):
 if "company_tickers.json" in url:
  return {"0":{"ticker":"TEST","cik_str":1234},"1":{"ticker":"DUP","cik_str":1235},"2":{"ticker":"DUP","cik_str":1236}}
 if "CIK0000001234.json" in url:
  return {"cik":1234,"name":"TEST INC","filings":{"recent":{"form":["10-K","8-K","OTHER"],"filingDate":["2026-01-01","2026-02-01","2026-02-02"],"accessionNumber":["0000001234-26-000001","0000001234-26-000002","0000001234-26-000003"]}}}
 raise AssertionError("Unexpected URL: "+url)

def test():
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  pd.DataFrame([{"Ticker":"TEST","Societe":"Test Inc"},{"Ticker":"DUP","Societe":"Ambigue"},{"Ticker":"UNKNOWN","Societe":"Inconnue"}]).to_csv(d/"DOSSIERS_SSI_A_QUALIFIER.csv",index=False)
  with patch.object(mod,"D",d),patch.object(mod,"SRC",d/"DOSSIERS_SSI_A_QUALIFIER.csv"),patch.object(mod,"OUT",d/"PREUVES_SEC_EDGAR_SSI.csv"),patch.object(mod,"AUD",d/"AUDIT_PREUVES_SEC_SSI.csv"),patch.object(mod,"lire_json",side_effect=faux_json),patch.object(mod.time,"sleep"),patch.dict(os.environ,{"SEC_USER_AGENT":"MicroCaps research contact@example.org"}):
   result=mod.executer()
  by=result.set_index("Ticker")
  assert by.loc["TEST","Statut_SEC"]=="A_VERIFIER_IDENTITE_ET_CONTENU"
  assert by.loc["TEST","Nb_depots"]==2
  depots=json.loads(by.loc["TEST","Depots"])
  assert len(depots)==2
  assert depots[0]["url_archive_officielle"]=="https://www.sec.gov/Archives/edgar/data/1234/000000123426000001/"
  assert depots[0]["statut_preuve"]=="DOCUMENT_A_LIRE"
  assert by.loc["DUP","Statut_SEC"]=="IDENTITE_AMBIGUE"
  assert by.loc["UNKNOWN","Statut_SEC"]=="NON_COUVERT"
  assert (d/"AUDIT_PREUVES_SEC_SSI.csv").exists()
  print("TEST SEC OK: rapprochement, ambiguite, non-couverture, depots, audit")

if __name__=="__main__": test()

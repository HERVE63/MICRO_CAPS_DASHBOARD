"""Test hors reseau de l'index SEC B4/B5, sans notation ni interpretation."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("gouv_sec",ROOT/"SCRIPTS_ACTIFS/07X_INDEX_GOUVERNANCE_SEC.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def test():
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  depots=[
   {"form":"4","date":"2026-08-10","accession":"0001","url_archive_officielle":"https://www.sec.gov/Archives/edgar/data/1234/0001/"},
   {"form":"DEF 14A","date":"2026-05-10","accession":"0002","url_archive_officielle":"https://www.sec.gov/Archives/edgar/data/1234/0002/"},
   {"form":"8-K","date":"2026-06-01","accession":"0003","url_archive_officielle":"https://www.sec.gov/Archives/edgar/data/1234/0003/"},
   {"form":"3","date":"2026-07-01","accession":"0004","url_archive_officielle":"https://invalid.example/"}
  ]
  pd.DataFrame([
   {"Ticker":"TEST","Societe":"Test Inc","CIK":"0000001234","Statut_SEC":"A_VERIFIER_IDENTITE_ET_CONTENU","Depots":json.dumps(depots)},
   {"Ticker":"NON","Societe":"Non couvert","CIK":"MANQUANTE","Statut_SEC":"NON_COUVERT","Depots":"[]"}]).to_csv(d/"PREUVES_SEC_EDGAR_SSI.csv",index=False)
  with patch.object(mod,"D",d),patch.object(mod,"SRC",d/"PREUVES_SEC_EDGAR_SSI.csv"),patch.object(mod,"OUT",d/"PISTES_GOUVERNANCE_SEC_SSI.csv"),patch.object(mod,"AUD",d/"AUDIT_GOUVERNANCE_SEC_SSI.csv"):rows=mod.executer()
  assert len(rows)==2
  assert {r["Bloc_SSI_cible"] for r in rows}=={"B4","B4_B5"}
  assert all(r["Note_SSI_attribuee"]=="NON" for r in rows)
  assert all(r["Participation_dirigeants_pct"]=="MANQUANTE" for r in rows)
  assert all(r["Statut_contenu"]=="A_LIRE" for r in rows)
  audit=pd.read_csv(d/"AUDIT_GOUVERNANCE_SEC_SSI.csv")
  assert int(audit.iloc[0]["Anomalies"])==1
  print("TEST GOUVERNANCE OK: formulaires, URL, exclusion, pas de note")
if __name__=="__main__":test()

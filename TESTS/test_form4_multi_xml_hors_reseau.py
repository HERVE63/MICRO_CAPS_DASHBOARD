"""Tests Form 4: depot contenant plusieurs XML et un seul ownershipDocument."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from io import BytesIO
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("form4_multi",ROOT/"SCRIPTS_ACTIFS/07Y_EXTRAIRE_FORM4_SEC.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class Reponse(BytesIO):
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
def test():
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  pd.DataFrame([{"Ticker":"TEST","CIK":"0000001234","Accession":"0000001234-26-000001","Formulaire":"4"}]).to_csv(d/"PISTES_GOUVERNANCE_SEC_SSI.csv",index=False)
  ownership=b'<ownershipDocument><issuer><issuerCik>0000001234</issuerCik></issuer><reportingOwner><reportingOwnerId><rptOwnerName>Test</rptOwnerName></reportingOwnerId></reportingOwner><nonDerivativeTable><nonDerivativeTransaction><transactionCoding><transactionCode>P</transactionCode></transactionCoding></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>'
  index=json.dumps({"directory":{"item":[{"name":"xbrl.xml"},{"name":"ownership.xml"}]}}).encode()
  def fake_urlopen(req,timeout=25):
   url=req.full_url
   if url.endswith("index.json"):return Reponse(index)
   if url.endswith("xbrl.xml"):return Reponse(b"<xbrl/>")
   if url.endswith("ownership.xml"):return Reponse(ownership)
   raise AssertionError(url)
  with patch.object(mod,"D",d),patch.object(mod,"urlopen",side_effect=fake_urlopen),patch.object(mod.time,"sleep"),patch.dict(mod.os.environ,{"SEC_USER_AGENT":"Research contact@example.org"}):
   rows=mod.executer()
  assert len(rows)==1
  assert rows[0]["Code_transaction"]=="P"
  assert rows[0]["Source_XML"].endswith("ownership.xml")
  # Un CIK different dans le document officiel doit interdire l'attribution.
  ownership_faux=ownership.replace(b"0000001234",b"0000009999")
  def faux_urlopen(req,timeout=25):
   if req.full_url.endswith("index.json"):return Reponse(index)
   if req.full_url.endswith("xbrl.xml"):return Reponse(b"<xbrl/>")
   if req.full_url.endswith("ownership.xml"):return Reponse(ownership_faux)
   raise AssertionError(req.full_url)
  with patch.object(mod,"D",d),patch.object(mod,"urlopen",side_effect=faux_urlopen),patch.object(mod.time,"sleep"),patch.dict(mod.os.environ,{"SEC_USER_AGENT":"Research contact@example.org"}):
   refuse=mod.executer()
  assert len(refuse)==0
  audit=pd.read_csv(d/"AUDIT_TRANSACTIONS_DIRIGEANTS_SEC_SSI.csv")
  assert audit.loc[0,"Statut"]=="CIK_EMETTEUR_FORM4_INCOHERENT"
  print("TEST FORM 4 MULTI XML OK")
if __name__=="__main__":test()

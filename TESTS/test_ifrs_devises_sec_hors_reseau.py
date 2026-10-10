"""Les normes et devises sont conservées sans conversion ni fusion de valeurs."""
import importlib.util,os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def charger(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'SCRIPTS_ACTIFS'/n)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
u=charger('07U_COLLECTE_COMPANYFACTS_SEC.py');v=charger('07V_NORMALISER_FAITS_SEC.py')
def test():
 f={'val':10,'end':'2026-06-30','filed':'2026-08-01','form':'20-F','accn':'0000000001-26-000001'}
 obj={'cik':1,'facts':{'ifrs-full':{
  'CashAndCashEquivalents':{'units':{'CAD':[f,dict(f,val=999,filed='2026-11-01')]}},
  'Assets':{'units':{'CAD':[f],'pure':[f]}},
  'NumberOfSharesIssued':{'units':{'shares':[f]}}},
  'us-gaap':{'Assets':{'units':{'CAD':[dict(f,val=20)]}}}}}
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  pd.DataFrame([{'Ticker':'TEST.F','CIK':'0000000001','Statut_SEC':'A_VERIFIER_IDENTITE_ET_CONTENU'}]).to_csv(d/'in.csv',index=False)
  with patch.object(u,'SRC',d/'in.csv'),patch.object(u,'OUT',d/'raw.csv'),patch.object(u,'AUD',d/'audit.csv'),patch.object(u,'lire_json',return_value=obj),patch.object(u.time,'sleep'),patch.dict(os.environ,{'SEC_USER_AGENT':'fixture contact@example.org','MICRO_CAPS_AS_OF':'2026-10-10'}):
   rows=u.executer()
  assert len(rows)==4 and not any(r['Valeur']==999 for r in rows)
  assert not any(r['Concept']=='Shares' for r in rows)
  with patch.object(v,'SRC',d/'raw.csv'),patch.object(v,'OUT',d/'normal.csv'),patch.object(v,'AUD',d/'audit_normal.csv'),patch.dict(os.environ,{'MICRO_CAPS_AS_OF':'2026-10-10'}):
   out=v.executer()
  assert len(out)==3 and set(out.Unite)=={'CAD'}
  assets=out[out.Concept.eq('Assets')]
  assert len(assets)==2 and set(assets.Taxonomie_SEC)=={'us-gaap','ifrs-full'}
  assert set(assets.Valeur.astype(int))=={10,20}
  assert all(out.Statut_preuve.eq('A_VERIFIER_IDENTITE_ET_PERIODE'))
 print('IFRS/DEVISES SEC: normes distinctes, CAD conservé, futur et pure exclus, actions émises non assimilées aux actions en circulation')
if __name__=='__main__':test()

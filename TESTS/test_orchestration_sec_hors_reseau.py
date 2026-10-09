"""Chaîne 07T→07Y réelle sur réponses SEC factices et archive isolée."""
import importlib.util,json,shutil
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('runner_sec',ROOT/'SCRIPTS_ACTIFS/07Z_EXECUTION_SEC_AUDITEE.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class R(BytesIO):
 def __enter__(self):return self
 def __exit__(self,*a):self.close()
def test():
 with TemporaryDirectory() as tmp:
  b=Path(tmp);(b/'DONNEES').mkdir();(b/'SCRIPTS_ACTIFS').mkdir()
  for name in m.MODULES:shutil.copy2(ROOT/'SCRIPTS_ACTIFS'/name,b/'SCRIPTS_ACTIFS'/name)
  fixture=pd.DataFrame([{'Ticker':'TEST','Societe':'TEST FIXTURE','Pays':'USA'}])
  for name in ['DOSSIERS_SSI_A_QUALIFIER.csv','UNIVERS_INVESTISSABLE_MICRO_CAPS.csv']:fixture.to_csv(b/'DONNEES'/name,index=False)
  before={p.name:p.read_bytes() for p in (b/'DONNEES').glob('*')}
  def faux(req,timeout=25):
   url=req.full_url
   if 'company_tickers.json' in url:o={'0':{'ticker':'TEST','cik_str':1234}}
   elif '/submissions/' in url:o={'cik':1234,'name':'TEST FIXTURE','filings':{'recent':{'form':['10-K','4'],'filingDate':['2026-02-01','2026-02-02'],'accessionNumber':['0000001234-26-000001','0000001234-26-000002']}}}
   elif '/companyfacts/' in url:o={'cik':1234,'facts':{'us-gaap':{'CashAndCashEquivalentsAtCarryingValue':{'units':{'USD':[{'val':100,'end':'2025-12-31','filed':'2026-02-01','form':'10-K','accn':'0000001234-26-000001'}]}}}}}
   elif url.endswith('index.json'):o={'directory':{'item':[{'name':'ownership.xml'}]}}
   elif url.endswith('ownership.xml'):
    return R(b'<ownershipDocument><issuer><issuerCik>1234</issuerCik></issuer><nonDerivativeTable><nonDerivativeTransaction><transactionCoding><transactionCode>P</transactionCode></transactionCoding></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>')
   else:raise AssertionError(url)
   return R(json.dumps(o).encode())
  env={'GITHUB_SHA':'TEST_FIXTURE','GITHUB_RUN_ID':'TEST_FIXTURE','GITHUB_RUN_ATTEMPT':'1',
       'SEC_USER_AGENT':'TEST research contact@example.org','SEC_BATCH_SIZE':'100','SEC_BATCH_OFFSET':'0'}
  with patch.object(m,'BASE',b),patch.object(m,'urlopen',side_effect=faux),patch.object(m.time,'sleep'),patch.dict(m.os.environ,env):
   assert m.executer()==0
  out=b/'AUDITS/SEC/RUN_TEST_FIXTURE_1';manifest=json.loads((out/'MANIFESTE.json').read_text())
  assert len(manifest['etapes'])==6 and manifest['notes_attribuees']==0
  assert manifest['integrite_entrees']=='OK' and manifest['statut']=='LOT_COLLECTE_A_VERIFIER'
  assert len(list((out/'BRUTS').glob('*')))==5
  assert {p.name:p.read_bytes() for p in (b/'DONNEES').glob('*')}==before
  assert len(pd.read_csv(out/'DONNEES/TRANSACTIONS_DIRIGEANTS_SEC_SSI.csv'))==1
  with patch.object(m,'BASE',b),patch.dict(m.os.environ,dict(env,GITHUB_RUN_ID='NO_SECRET',SEC_USER_AGENT='')):
   assert m.executer()==1
  blocked=json.loads((b/'AUDITS/SEC/RUN_NO_SECRET_1/MANIFESTE.json').read_text())
  assert blocked['statut']=='BLOQUE' and blocked['etapes']==[] and not blocked['secret_contact_valide']
 print('ORCHESTRATION SEC: six modules exécutés, bruts archivés, entrées intactes et secret absent bloquant (fixtures)')
if __name__=='__main__':test()

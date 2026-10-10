"""La découverte par nom conserve les ambiguïtés et ne valide jamais l'identité."""
import importlib.util,json,os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('multicotation',ROOT/'SCRIPTS_ACTIFS/07T_ENRICHIR_PREUVES_SEC_EDGAR.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 reg={'0':{'ticker':'ALFA','title':'Alpha Corp','cik_str':1},
      '1':{'ticker':'ALFAF','title':'Alpha Corp','cik_str':1},
      '2':{'ticker':'BETA','title':'Beta Inc','cik_str':2},
      '3':{'ticker':'GAM1','title':'Gamma Ltd','cik_str':3},
      '4':{'ticker':'GAM2','title':'Gamma Ltd','cik_str':4}}
 calls=[]
 def faux(url,agent):
  if 'company_tickers.json' in url:return reg
  calls.append(url)
  return {'cik':1,'name':'Alpha Corp','filings':{'recent':{}}}
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  df=pd.DataFrame([{'Ticker':'A.F','Societe':'Alpha Corp.       R','Pays':'Allemagne'},
                   {'Ticker':'B.F','Societe':'Beta Inc.        R','Pays':'Allemagne'},
                   {'Ticker':'G.F','Societe':'Gamma Ltd','Pays':'Allemagne'},
                   {'Ticker':'ALFA.F','Societe':'Unrelated Holdings','Pays':'Allemagne'},
                   {'Ticker':'X.F','Societe':'Alpha Corp Subsidiary','Pays':'Allemagne'}])
  df.to_csv(d/'in.csv',index=False);before=(d/'in.csv').read_bytes()
  with patch.object(m,'SRC',d/'in.csv'),patch.object(m,'OUT',d/'out.csv'),patch.object(m,'AUD',d/'audit.csv'),patch.object(m,'lire_json',side_effect=faux),patch.object(m.time,'sleep'),patch.dict(os.environ,{'SEC_USER_AGENT':'fixture contact@example.org','SEC_BATCH_SIZE':'1','SEC_BATCH_OFFSET':'0'}):
   out=m.executer().set_index('Ticker')
  assert out.loc['A.F','Statut_SEC']=='A_VERIFIER_IDENTITE_ET_CONTENU'
  assert out.loc['A.F','CIK']=='0000000001'
  assert out.loc['A.F','CIK_verifie']=='NON'
  assert out.loc['A.F','Tickers_SEC']=='ALFA;ALFAF'
  assert out.loc['B.F','Statut_SEC']=='PISTE_SEC_HORS_LOT'
  assert out.loc['G.F','Statut_SEC']=='IDENTITE_AMBIGUE'
  assert out.loc['ALFA.F','Statut_SEC']=='NON_COUVERT'
  assert out.loc['X.F','Statut_SEC']=='NON_COUVERT'
  assert calls==['https://data.sec.gov/submissions/CIK0000000001.json']
  assert (d/'in.csv').read_bytes()==before
 print('MULTICOTATION SEC: noms exacts, ambiguïtés, alias, lot borné et identité non validée')
if __name__=='__main__':test()

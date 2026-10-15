"""Pièces SEC : refus des dates futures, traversées et redirections étrangères."""
from pathlib import Path
import importlib.util,json,hashlib
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd
s=importlib.util.spec_from_file_location('doc_us',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AF_COLLECTER_DOCUMENTS_US.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 assert m.url_document('0001328792','0001328792-26-000001','annual.htm')=='https://www.sec.gov/Archives/edgar/data/1328792/000132879226000001/annual.htm'
 for doc in ['../annual.htm','/annual.htm','https://evil.test/a','a?password=x']:
  try:m.url_document('1','0001328792-26-000001',doc)
  except ValueError:pass
  else:raise AssertionError('Chemin dangereux accepté')
 q={'filings':{'recent':{'form':['10-K','10-K','DEF 14A'],'filingDate':['2026-08-01','2026-11-01','2026-09-01'],
     'accessionNumber':['0001328792-26-000001','0001328792-26-000002','0001328792-26-000003'],'primaryDocument':['old.htm','future.htm','proxy.htm']}}}
 r=m.choisir(q,'2026-10-15');assert r['10-K']['Document_primaire']=='old.htm' and r['10-Q'] is None
 try:m.RedirectionsSEC().redirect_request(None,None,302,'',{},'https://evil.test/a')
 except ValueError:pass
 else:raise AssertionError('Redirection externe acceptée')
 with TemporaryDirectory() as tmp:
  b=Path(tmp);a=b/'AUDITS/UNIVERS_US/20261015';a.mkdir(parents=True)
  profile=b/'profile.json';profile.write_text(json.dumps(dict(q,cik='0001328792')))
  us=a/'UNIVERS_US_PROVISOIRE.csv'
  pd.DataFrame([{'CIK':'0001328792','Ticker_cotation':'TEST.F','Nom_SEC':'FIXTURE','Statut_identite':'A_VERIFIER',
   'Fichier_brut':'profile.json','SHA256':hashlib.sha256(profile.read_bytes()).hexdigest()}]).to_csv(us,index=False)
  (a/'MANIFESTE.json').write_text(json.dumps({'fichiers':{us.name:hashlib.sha256(us.read_bytes()).hexdigest()}}))
  class Response:
   headers={'Content-Type':'text/html'}
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,n):return b'<html><body>Fixture annual or proxy document</body></html>'
   def geturl(self):return 'https://www.sec.gov/Archives/edgar/data/1328792/fixture.htm'
  class Opener:
   def open(self,*a,**kw):return Response()
  with patch.object(m,'BASE',b),patch.dict(m.os.environ,{'SEC_USER_AGENT':'fixture fixture@example.org'}),patch.object(m,'build_opener',return_value=Opener()),patch.object(m.time,'sleep'):
   result=m.executer()
   assert result['documents_collectes']==2 and result['emetteurs_trois_documents_collectes']==0
   assert result['notes_attribuees']==0 and result['qualification_SSI_effectuee'] is False
   # Le deuxième passage doit fonctionner sans téléchargement et conserver la date d'origine.
   audits=sorted((b/'AUDITS/DOCUMENTS_US').glob('*/AUDIT_DOCUMENTS.csv'))
   old=pd.read_csv(audits[-1]).query("Statut=='DOCUMENT_COLLECTE_A_VERIFIER'")
   with patch.object(Opener,'open',side_effect=AssertionError('Réseau inattendu')):result=m.executer()
   new=pd.read_csv(sorted((b/'AUDITS/DOCUMENTS_US').glob('*/AUDIT_DOCUMENTS.csv'))[-1]).query("Statut=='DOCUMENT_COLLECTE_A_VERIFIER'")
   assert list(old.Date_collecte_UTC)==list(new.Date_collecte_UTC)
   assert new.Reutilise.eq('OUI').all()
   raw=b/new.Fichier_brut.iloc[0];raw.write_bytes(b'CORROMPU')
   try:m.executer()
   except RuntimeError as e:assert 'CORROMPU' in str(e)
   else:raise AssertionError('Document cache altéré accepté')
 print('DOCUMENTS US: dépôt connu, date limite, chemins et redirections contrôlés')
if __name__=='__main__':test()

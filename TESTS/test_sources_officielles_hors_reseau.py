"""Téléchargement hors SEC : bruts hashés, redirection et domaine contrôlés."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from io import BytesIO
import importlib.util,json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('sources_officielles',ROOT/'SCRIPTS_ACTIFS/07AA_COLLECTE_DOCUMENTS_OFFICIELS.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class R(BytesIO):
 headers={'Content-Type':'application/pdf'}
 def geturl(self):return 'https://issuer.example/doc.pdf'
 def __enter__(self):return self
 def __exit__(self,*a):self.close()
class O:
 def open(self,*a,**k):return R(b'TEST FIXTURE DOCUMENT')
def test():
 with TemporaryDirectory() as tmp:
  b=Path(tmp);(b/'DONNEES').mkdir();(b/'CONFIG').mkdir()
  pd.DataFrame([{'Ticker':'TEST','Societe':'TEST FIXTURE','Pays':'France'}]).to_csv(b/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv',index=False)
  row={'ID_document':'TEST_DOC','Ticker':'TEST','Identifiant_emetteur':'ISIN:FR0011271600','Source_URL':'https://issuer.example/doc.pdf',
       'Type_source':'PUBLICATION_EMETTEUR','Date_publication':'2026-01-01','Domaine_autorise':'issuer.example',
       'Source_habilitation_domaine':'https://issuer.example/investors','Statut_identite':'A_VERIFIER'}
  reg=b/'CONFIG/DOCUMENTS.csv';pd.DataFrame([row]).to_csv(reg,index=False)
  dns=[(None,None,None,None,('93.184.216.34',443))]
  with patch.object(m,'BASE',b),patch.object(m,'REG',reg),patch.object(m.socket,'getaddrinfo',return_value=dns),patch.object(m,'build_opener',return_value=O()):
   rows=m.executer();assert rows[0]['Statut']=='DOCUMENT_COLLECTE_A_VERIFIER'
   assert rows[0]['Notes_attribuees']==0 and (b/rows[0]['Fichier_brut']).read_bytes()==b'TEST FIXTURE DOCUMENT'
   try:m.verifier_url('https://other.example/file',{'issuer.example'})
   except ValueError:pass
   else:raise AssertionError('Domaine extérieur accepté')
   try:m.verifier_url('http://issuer.example/file',{'issuer.example'})
   except ValueError:pass
   else:raise AssertionError('HTTP accepté')
  with patch.object(m.socket,'getaddrinfo',return_value=[(None,None,None,None,('127.0.0.1',443))]):
   try:m.verifier_url('https://issuer.example/file',{'issuer.example'})
   except ValueError:pass
   else:raise AssertionError('Adresse privée acceptée')
 print('SOURCES NON-US: archive brute, statut non validé, domaines/HTTPS/adresses publiques contrôlés')
if __name__=='__main__':test()

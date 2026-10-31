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
   unknown=dict(row,Date_publication='',Date_publication_inconnue='OUI',Periode_comptable='2025-12-31')
   pd.DataFrame([unknown]).to_csv(reg,index=False)
   full=b/'univers.csv';pd.DataFrame([{'Ticker_US':'TEST'},{'Ticker_US':'MISSING'}]).to_csv(full,index=False)
   result=m.executer(reg,full)[0]
   assert result['Statut']=='DOCUMENT_COLLECTE_A_VERIFIER' and result['Date_publication']==''
   assert result['Statut_date_publication'].startswith('INCONNUE') and result['Periode_comptable']=='2025-12-31'
   out=b/result['Fichier_brut'];manifest=json.loads((out.parent/'MANIFESTE.json').read_text())
   assert manifest['dossiers_univers']==2 and manifest['dossiers_sans_document_configure']==1
   assert manifest['fichiers'][out.name]==result['SHA256'] and manifest['notes_attribuees']==0
   # Fiche d'operateur de marche : capture documentaire uniquement,
   # jamais une certification d'identite ou une note.
   marche=dict(unknown,Type_source='DONNEE_MARCHE_IDENTITE',
               Statut_identite='A_VERIFIER_COTATION_TEST')
   pd.DataFrame([marche]).to_csv(reg,index=False)
   capture=m.executer(reg,full)[0]
   assert capture['Statut']=='DOCUMENT_COLLECTE_A_VERIFIER'
   assert capture['Notes_attribuees']==0
   assert capture['Statut_identite']=='A_VERIFIER_COTATION_TEST'
   pd.DataFrame([dict(marche,Statut_identite='VERIFIEE')]).to_csv(reg,index=False)
   assert m.executer(reg,full)[0]['Statut']=='BLOQUE_SOURCE'
   pd.DataFrame([dict(marche,Type_source='DONNEE_MARCHE')]).to_csv(reg,index=False)
   assert m.executer(reg,full)[0]['Statut']=='BLOQUE_SOURCE'
   for invalid in [dict(unknown,Date_publication_inconnue=''),dict(unknown,Date_publication='2999-01-01'),dict(unknown,Date_publication='date erronée')]:
    pd.DataFrame([invalid]).to_csv(reg,index=False)
    assert m.executer(reg,full)[0]['Statut']=='BLOQUE_SOURCE'

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
 # Le registre reel de collecte ICAPE n'est qu'un inventaire de pistes :
 # deux sources datees, deux pages a publication inconnue, aucune certification.
 reg_reel=pd.read_csv(ROOT/'CONFIG/DOCUMENTS_OFFICIELS_ICAPE_A_COLLECTER.csv',
                      dtype=str,keep_default_na=False)
 assert len(reg_reel)==4 and reg_reel.ID_document.is_unique
 assert reg_reel.Statut_identite.str.startswith('A_VERIFIER').all()
 assert reg_reel.Identifiant_emetteur.eq('ISIN:FR001400A3Q3').all()
 assert reg_reel.Source_URL.str.startswith('https://').all()
 dates=reg_reel[reg_reel.Date_publication.ne('')]
 assert set(dates.ID_document)=={
  'ICAPE_RFS_S1_2026_OFFICIEL','ICAPE_RESULTATS_S1_2026_EURONEXT'}
 assert pd.to_datetime(dates.Date_publication,utc=True,format='mixed',errors='coerce').notna().all()
 assert dates.Source_date_publication.str.startswith('https://').all()
 assert reg_reel.loc[reg_reel.Date_publication.eq(''),'Date_publication_inconnue'].eq('OUI').all()
 assert not any(c.startswith('Note_') for c in reg_reel.columns)
 print('SOURCES NON-US: archive brute, statut non validé, domaines/HTTPS/adresses publiques contrôlés')
if __name__=='__main__':test()

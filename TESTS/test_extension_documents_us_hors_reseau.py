"""Le raccordement documentaire prend le recensement complet, conserve les absents."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import importlib.util,json,hashlib,gzip
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def charger(nom):
 s=importlib.util.spec_from_file_location(nom,ROOT/'SCRIPTS_ACTIFS'/nom)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def test():
 m=charger('07AJ_ETENDRE_DOCUMENTS_SEC_UNIVERS_US.py');af=charger('07AF_COLLECTER_DOCUMENTS_US.py')
 with TemporaryDirectory() as tmp:
  root=Path(tmp);source=root/'AUDITS/RECENSEMENT_US_EODHD/FIXTURE';source.mkdir(parents=True)
  pd.DataFrame([{'Ticker_US':'TEST.US','CIK':'0000000001','Statut_origine':'PISTE_US_CONCORDANTE'},
                {'Ticker_US':'TESTB.US','CIK':'0000000001','Statut_origine':'PISTE_US_CONCORDANTE'},
                {'Ticker_US':'INCONNU.US','CIK':'','Statut_origine':'CIK_NON_RESOLU_OU_AMBIGU'}]).to_csv(source/'COUVERTURE_PREUVES_SEC.csv',index=False)
  (source/'archive.enc.json').write_text('{"fixture":1}')
  url='https://data.sec.gov/submissions/CIK0000000001.json'
  (source/'INDEX_REQUETES.json').write_text(json.dumps([{'route':'SEC:'+url,'archive_chiffree':'archive.enc.json','date_collecte_utc':'2026-10-15T00:00:00Z'}]))
  (source/'MANIFESTE.json').write_text(json.dumps({'recensement_termine':True,'fichiers':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()}}))
  raw=b'{"cik":1,"name":"Fixture SEC","filings":{"recent":{}}}'
  with patch.object(m,'BASE',root),patch.object(m,'charger',side_effect=charger):
   univers=m.preparer(source,'fixture',lambda a,k:raw)
  tab=pd.read_csv(univers,dtype=str)
  assert len(tab)==1 and tab.iloc[0]['Tickers_recenses']=='TEST.US|TESTB.US'
  assert len(pd.read_csv(univers.parent/'TOUTES_COTATIONS_RECENSEES.csv'))==3
  assert json.loads((univers.parent/'MANIFESTE.json').read_text())['notes_SSI_attribuees']==0
  with patch.object(m,'BASE',root),patch.object(m,'charger',side_effect=charger):
   # Un profil au CIK divergent n'est jamais transformé en identité valide.
   try:m.preparer(source,'fixture',lambda a,k:b'{"cik":999,"name":"autre"}')
   except RuntimeError as e:assert 'AUCUN_PROFIL_RESOLU' in str(e)
   else:raise AssertionError('Profil au CIK divergent accepté')
  document='<!doctype html><html><ix:nonNumeric name="dei:EntityCentralIndexKey">0000000001</ix:nonNumeric>Fixture, pas un document financier réel</html>'.encode('utf-8')
  archive=root/'preuve.bin.gz';archive.write_bytes(gzip.compress(document,mtime=0))
  assert af.lire_document(archive)==document
  plain=root/'preuve.bin';plain.write_bytes(document);assert af.lire_document(plain)==document
  # Le contrôleur réel doit vérifier les octets décompressés et l'archive.
  dossier=root/'AUDITS/DOCUMENTS_US/FIXTURE';dossier.mkdir(parents=True)
  brut=dossier/'preuve.bin.gz';brut.write_bytes(archive.read_bytes())
  pd.DataFrame([{'CIK':'0000000001','Ticker_cotation':'TEST.US','Formulaire':'10-K',
    'Source_URL':'https://www.sec.gov/Archives/edgar/data/1/000000000126000001/fixture.htm',
    'Date_depot':'2026-10-15','Date_collecte_UTC':'2026-10-15T12:00:00+00:00',
    'Fichier_brut':str(brut.relative_to(root)),'SHA256':hashlib.sha256(document).hexdigest(),
    'SHA256_archive':hashlib.sha256(brut.read_bytes()).hexdigest(),
    'Statut':'DOCUMENT_COLLECTE_A_VERIFIER'}]).to_csv(dossier/'AUDIT_DOCUMENTS.csv',index=False)
  (dossier/'MANIFESTE.json').write_text(json.dumps({'date_limite':'2026-10-15',
    'fichiers':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dossier.iterdir()}}))
  ag=charger('07AG_CONTROLER_DOCUMENTS_US.py')
  with patch.object(ag,'BASE',root):resultat=ag.executer()
  assert resultat['repartition_controles']=={'CIK_XBRL_CONCORDANT':1}
 print('Extension documentaire : dénominateur conservé, classes dédoublonnées, profils SEC et archives gzip/anciennes contrôlés')

if __name__=='__main__':test()

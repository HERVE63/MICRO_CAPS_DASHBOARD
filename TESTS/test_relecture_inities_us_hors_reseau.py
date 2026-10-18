"""Lot SEC actualisé, XML archivés, qualités/notes conservées, aucune auto-notation."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import importlib.util,json,gzip,hashlib,os,shutil
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('lot_inities',ROOT/'SCRIPTS_ACTIFS/07AP_RELECTURE_INITIES_LOT_US.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 y=m.charger('07Y_EXTRAIRE_FORM4_SEC.py')
 xml=b'''<ownershipDocument><issuer><issuerCik>0000001234</issuerCik></issuer><reportingOwner><reportingOwnerId><rptOwnerCik>0000004321</rptOwnerCik><rptOwnerName>EXAMPLE ONLY</rptOwnerName></reportingOwnerId><reportingOwnerRelationship><isOfficer>1</isOfficer><isDirector>0</isDirector></reportingOwnerRelationship></reportingOwner><nonDerivativeTable><nonDerivativeTransaction><securityTitle><value>Common Stock</value></securityTitle><transactionDate><value>2026-10-01</value></transactionDate><transactionCoding><transactionCode>P</transactionCode></transactionCoding><transactionAmounts><transactionShares><value>3</value></transactionShares><transactionPricePerShare><value>2</value></transactionPricePerShare><transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode><footnoteId id="F1"/></transactionAmounts><ownershipNature><directOrIndirectOwnership><value>D</value></directOrIndirectOwnership></ownershipNature></nonDerivativeTransaction></nonDerivativeTable><footnotes><footnote id="F1">Purchase under an automatic plan; interpretation required.</footnote></footnotes></ownershipDocument>'''
 row=y.analyser_xml(xml)[0]
 assert row['Nombre_declarants']==1 and row['Titre_valeur']=='Common Stock' and row['CIK_declarants']=='0000004321'
 assert json.loads(row['Qualites_declarants_JSON'])[0]['isOfficer']=='1'
 assert 'automatic plan' in row['Footnotes_ligne_JSON'] and row['Plan_10b5_1_declare']==''
 joint=xml.replace(b'</reportingOwner><nonDerivativeTable>',b'</reportingOwner><reportingOwner><reportingOwnerId><rptOwnerCik>0000004444</rptOwnerCik><rptOwnerName>JOINT EXAMPLE</rptOwnerName></reportingOwnerId></reportingOwner><nonDerivativeTable>')
 assert y.analyser_xml(joint)[0]['Nombre_declarants']==2 # une ligne XML, pas deux achats
 assert len(y.analyser_xml(joint))==1
 with TemporaryDirectory() as tmp:
  root=Path(tmp);p=root/'AUDITS/RECHERCHE_COMPLEMENTS_US/2026-10-18_LOT_ORDRE_SCE';p.mkdir(parents=True)
  lot=p/'LOT_PRIORISATION.csv';pd.DataFrame([{'Ticker':'FIXTURE.US','CIK':'0000001234'}]).to_csv(lot,index=False)
  (p/'MANIFESTE.json').write_text(json.dumps({'fichiers':{lot.name:hashlib.sha256(lot.read_bytes()).hexdigest()}}))
  (root/'SCRIPTS_ACTIFS').mkdir();shutil.copy2(ROOT/'SCRIPTS_ACTIFS/07Y_EXTRAIRE_FORM4_SEC.py',root/'SCRIPTS_ACTIFS/07Y_EXTRAIRE_FORM4_SEC.py')
  profile={'cik':1234,'tickers':['FIXTURE'],'name':'TEST FIXTURE','filings':{'recent':{'form':['4'],'filingDate':['2026-10-01'],'accessionNumber':['0000001234-26-000001'],'primaryDocument':['ownership.xml']}}}
  class Opener:
   def open(self,req,**kwargs):
    url=req.full_url
    if url.endswith('CIK0000001234.json'):raw=json.dumps(profile).encode()
    elif url.endswith('index.json'):raw=json.dumps({'directory':{'item':[{'name':'ownership.xml'}]}}).encode()
    elif url.endswith('ownership.xml'):raw=xml
    else:raise AssertionError(url)
    return m.Reponse(raw)
  orig=m.charger
  def charger(nom):
   with patch.object(m,'BASE',ROOT):return orig(nom)
  with patch.object(m,'BASE',root),patch.object(m,'charger',side_effect=charger),patch.object(m,'build_opener',return_value=Opener()),patch.object(m.time,'sleep'),patch.dict(os.environ,{'SEC_USER_AGENT':'TEST contact@example.org'}):
   bilan=m.executer()
  assert bilan['profils_concordants']==1 and bilan['transactions_non_derivees_extraites']==1 and bilan['reponses_HTTP_archivees']==3
  assert bilan['notes_SSI_attribuees']==0 and not bilan['detentions_actuelles_reconstituees']
  out=next((root/'AUDITS/RELECTURE_INITIES_US').iterdir());sources=json.loads((out/'BRUTS/SOURCES_HTTP.json').read_text())
  for r in sources:
   path=root/r['Fichier_brut'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['SHA256_archive'];assert hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()==r['SHA256_brut']
  data=pd.read_csv(out/'TRANSACTIONS_FORM4_LOT.csv');assert data.loc[0,'Nombre_declarants']==1 and data.loc[0,'Note_SSI_attribuee']=='NON'
  am=m.charger('07AM_CONSOLIDER_PREUVES_US.py');util=m.charger('07AI_RACCORDER_COMPTES_US_SSI.py')
  with patch.object(am,'BASE',root):
   mapping,mp=am.lot_inities(util)
   assert mapping['FIXTURE.US']['lignes']==1 and mapping['FIXTURE.US']['CIK']=='0000001234'
   # Un nouveau lot ne supprime pas les émetteurs du lot précédent.
   second=out.parent/'ZZZZ_LOT_02';shutil.copytree(out,second)
   for nom in ['PROFILS_ACTUALISES.csv','TRANSACTIONS_FORM4_LOT.csv']:
    table=pd.read_csv(second/nom,dtype=str,keep_default_na=False);table['Ticker']='AUTRE.US';table['CIK']='0000004321';table.to_csv(second/nom,index=False)
   meta=json.loads((second/'MANIFESTE.json').read_text());meta['source_lot_SHA256']='LOT_02_FIXTURE';meta['fichiers']={str(p.relative_to(second)):hashlib.sha256(p.read_bytes()).hexdigest() for p in second.rglob('*') if p.is_file() and p.name!='MANIFESTE.json'};(second/'MANIFESTE.json').write_text(json.dumps(meta))
   mapping,_=am.lot_inities(util);assert set(mapping)=={'FIXTURE.US','AUTRE.US'} and mapping['AUTRE.US']['CIK']=='0000004321'
   with (out/'TRANSACTIONS_FORM4_LOT.csv').open('a') as f:f.write('corruption')
   try:am.lot_inities(util)
   except RuntimeError:pass
   else:raise AssertionError('Lot Form 4 corrompu raccordé à la matrice')

  # Les XML archivés sont réutilisés avec leur date réelle ; les profils restent frais.
  nouveau=root/'REPRISE/BRUTS';nouveau.mkdir(parents=True)
  class Interdit:
   def open(self,*a,**kw):raise AssertionError('HTTP sur XML déjà archivé')
  with patch.object(m,'BASE',root),patch.object(m,'charger',side_effect=charger),patch.object(m,'build_opener',return_value=Interdit()):
   client=m.ClientSEC(nouveau,'TEST contact@example.org')
   url='https://www.sec.gov/Archives/edgar/data/1234/000000123426000001/ownership.xml'
   with client.open(m.Request(url)) as response:assert response.read()==xml
   assert client.sources[0]['Reutilise']=='OUI' and client.sources[0]['Date_collecte_UTC']==next(r['Date_collecte_UTC'] for r in sources if r['URL']==url)
   with patch.object(client.opener,'open',side_effect=[TimeoutError('EXEMPLE interruption'),m.Reponse(b'{}')]) as calls,patch.object(m.time,'sleep'):
    with client.open(m.Request('https://data.sec.gov/submissions/CIK0000009999.json')) as response:assert response.read()==b'{}'
    assert calls.call_count==2 and client.sources[-1]['Reutilise']=='NON'
   original=root/client.cache[url]['Fichier_brut'];original.write_bytes(b'CORROMPU')
   try:client.open(m.Request(url))
   except RuntimeError as exc:assert 'CORROMPU' in str(exc)
   else:raise AssertionError('Cache XML corrompu réutilisé')
 print('Relecture lot : profils CIK/ticker, XML et index hashés, fonctions des déclarants, déclarations conjointes et notes de bas de page préservés, aucune note SSI')
if __name__=='__main__':test()

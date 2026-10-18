"""Tous les dépôts recent éligibles, aucune troncature ni transaction inventée."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import importlib.util,json,hashlib
import pandas as pd
s=importlib.util.spec_from_file_location('gouv_us',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AM_CONSOLIDER_PREUVES_US.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 q={'form':['4']*40+['4'],'filingDate':['2026-10-01']*40+['2026-11-01'],
    'accessionNumber':['0000000001-26-'+str(i).zfill(6) for i in range(41)]}
 rows=m.depots({'filings':{'recent':q}},'0000000001','2026-10-15',{'4':'B4'})
 assert len(rows)==40 and all(r['date']=='2026-10-01' for r in rows)
 assert all(r['url_archive_officielle'].startswith('https://www.sec.gov/Archives/edgar/data/1/') for r in rows)
 assert all('transaction' not in r and 'Note_SSI' not in r for r in rows)
 q['filingDate']=q['filingDate'][:1]
 try:m.depots({'filings':{'recent':q}},'0000000001','2026-10-15',{'4':'B4'})
 except RuntimeError as e:assert 'PARSING_INDEX_INCOMPLET' in str(e)
 else:raise AssertionError('Parsing incomplet accepté')
 # Assemblage complet : deux cotations restent visibles, dont une sans profil.
 with TemporaryDirectory() as tmp:
  root=Path(tmp)
  def dossier(nom):
   p=root/'AUDITS'/nom/'FIXTURE';p.mkdir(parents=True);return p
  def manifeste(p,meta):
   meta=dict(meta,fichiers={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir() if f.is_file()})
   (p/'MANIFESTE.json').write_text(json.dumps(meta))
  p=dossier('PROFILS_SEC_UNIVERS_US');d=dossier('DOCUMENTS_US');f=dossier('QUALIFICATION_US');a=dossier('SCE_DISCOVERY_US');c=dossier('CONTROLE_DOCUMENTS_US')
  raw=p/'CIK0000000001.json';raw.write_text(json.dumps({'cik':1,'filings':{'recent':{
    'form':['4'],'filingDate':['2026-10-01'],'accessionNumber':['0000000001-26-000001']},'files':[]}}))
  pd.DataFrame([{'CIK':'0000000001','Ticker_cotation':'FIXTURE.US','Fichier_brut':str(raw.relative_to(root)),
    'SHA256':hashlib.sha256(raw.read_bytes()).hexdigest(),'Nom_SEC':'Fixture','Date_source_UTC':'2026-10-15T00:00:00Z'}]).to_csv(p/'UNIVERS_SEC_COTATIONS_US.csv',index=False)
  pd.DataFrame([{'Ticker_US':'FIXTURE.US','CIK':'0000000001','Statut_origine':'PISTE_US_CONCORDANTE'},
                {'Ticker_US':'INCONNU.US','CIK':'','Statut_origine':'CIK_NON_RESOLU_OU_AMBIGU'}]).to_csv(p/'TOUTES_COTATIONS_RECENSEES.csv',index=False)
  manifeste(p,{'source_recensement':'AUDITS/RECENSEMENT_US_EODHD/FIXTURE'})
  pd.DataFrame([{'CIK':'0000000001','Statut':'DOCUMENT_COLLECTE_A_VERIFIER','Formulaire':x} for x in ('10-K','10-Q','DEF 14A')]).to_csv(d/'AUDIT_DOCUMENTS.csv',index=False)
  manifeste(d,{'univers_source':str((p/'UNIVERS_SEC_COTATIONS_US.csv').relative_to(root))})
  pd.DataFrame([{'Ticker_US':'FIXTURE.US','Faits_comparables':2,'Concepts_comparables':'Assets;Cash',
    'Dernier_depot_comparable':'2026-10-01'}]).to_csv(f/'COUVERTURE_QUALIFICATION_US.csv',index=False)
  manifeste(f,{'source_recensement':'AUDITS/RECENSEMENT_US_EODHD/FIXTURE'})
  pd.DataFrame([{'Ticker':'FIXTURE.US','SSI':'MANQUANTE','Statut_SSI':'A_COMPLETER_PREUVES_SSI','SCE_valide':'NON'}]).to_csv(a/'RESULTATS_SSI.csv',index=False)
  pd.DataFrame([{'Ticker':'FIXTURE.US','Statut_instrument':'ACTION_ORDINAIRE_LIBELLE_OFFICIEL'}]).to_csv(a/'ORDRE_CONTROLES_SCE.csv',index=False)
  manifeste(a,{'source_recensement':'AUDITS/RECENSEMENT_US_EODHD/FIXTURE/MANIFESTE.json'})
  pd.DataFrame([{'CIK':'0000000001','Controle_document':'CIK_XBRL_CONCORDANT'}]).to_csv(c/'CONTROLES_DOCUMENTS.csv',index=False)
  manifeste(c,{'archive_source':str((d/'MANIFESTE.json').relative_to(root))})
  ir=dossier('SOURCES_OFFICIELLES');doc=ir/'fixture.bin';doc.write_bytes(b'ANNUAL REPORT TEST FIXTURE')
  pd.DataFrame([{'Ticker':'FIXTURE.US','Identifiant_emetteur':'CIK:0000000001','Statut':'DOCUMENT_COLLECTE_A_VERIFIER',
    'Nature_document':'COMPTES_ANNUELS_AUDITES','Fichier_brut':str(doc.relative_to(root)),
    'SHA256':hashlib.sha256(doc.read_bytes()).hexdigest(),'Source_URL':'https://issuer.example/annual.pdf','Date_publication':''}]).to_csv(ir/'AUDIT_DOCUMENTS.csv',index=False)
  manifeste(ir,{'registre_source':'CONFIG/DOCUMENTS_OFFICIELS_US_A_COLLECTER.csv',
    'couverture_source_SHA256':hashlib.sha256((p/'TOUTES_COTATIONS_RECENSEES.csv').read_bytes()).hexdigest()})
  comp=dossier('MARCHE_US_EODHD')
  pd.DataFrame([{'Ticker':'FIXTURE.US','Volume_monetaire_63s_disponible':'OUI'},
                {'Ticker':'INCONNU.US','Volume_monetaire_63s_disponible':'NON'}]).to_csv(comp/'COUVERTURE_MARCHE_US.csv',index=False)
  manifeste(comp,{'volumes_monetaires_corriges_splits':True,'source_univers_SHA256':hashlib.sha256((p/'TOUTES_COTATIONS_RECENSEES.csv').read_bytes()).hexdigest()})
  chargeur=m.charger
  def lire_module(nom):
   with patch.object(m,'BASE',Path(__file__).resolve().parents[1]):return chargeur(nom)
  with patch.object(m,'BASE',root),patch.object(m,'charger',side_effect=lire_module):bilan=m.executer()
  assert bilan['cotations_conservees']==2 and bilan['cotations_avec_trois_documents']==1
  assert bilan['Form4_references_non_extraits']==1 and bilan['candidats_selection_autorises']==0
  assert bilan['cotations_volumes_63s_disponibles']==1 and bilan['cotations_passages_detention_groupe']==0
  assert bilan['documents_IR_hors_index_a_verifier']==1 and bilan['index_IR_sans_comptes']==0
  doc.write_bytes(b'CORRUPTED FIXTURE')
  with patch.object(m,'BASE',root),patch.object(m,'charger',side_effect=lire_module):
   try:m.sources_ir(lire_module('07AI_RACCORDER_COMPTES_US_SSI.py'),p/'TOUTES_COTATIONS_RECENSEES.csv')
   except RuntimeError as exc:assert 'EMPREINTE_SOURCE_INCOHERENTE' in str(exc)
   else:raise AssertionError('Document IR corrompu accepté')
 print('Gouvernance US : plus de 30 références conservées, dates futures écartées, parsing incomplet bloqué, aucune transaction inventée')
if __name__=='__main__':test()

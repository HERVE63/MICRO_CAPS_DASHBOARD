"""Consolidation additive, provenance et refus d'une archive altérée."""
import importlib.util,json,hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('consolidation',ROOT/'SCRIPTS_ACTIFS/07AD_CONSOLIDER_COLLECTES_SEC.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 with TemporaryDirectory() as tmp:
  b=Path(tmp);(b/'DONNEES').mkdir()
  pd.DataFrame([{'Ticker':'A.F','Societe':'Fixture','Pays':'Allemagne'}]).to_csv(b/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv',index=False)
  f={k:'' for k in m.KEYS};f.update(Ticker='A.F',CIK='0000000001',Taxonomie_SEC='ifrs-full',Concept='Assets',Tag_SEC='Assets',Unite='CAD',Fin_periode='2026-06-30',Date_depot='2026-08-01',Accession='0000000001-26-000001',Valeur='10')
  for name,rows in [('RUN_A',[f]),('RUN_B',[dict(f,Valeur='10.0'),dict(f,Valeur='20')])]:
   a=b/'AUDITS/SEC'/name;(a/'DONNEES').mkdir(parents=True)
   pd.DataFrame(rows).to_csv(a/'DONNEES/FAITS_FINANCIERS_SEC_SSI.csv',index=False)
   pd.DataFrame([{'Ticker':'A.F','CIK':'0000000001'}]).to_csv(a/'DONNEES/PREUVES_SEC_EDGAR_SSI.csv',index=False)
   hashes={str(p.relative_to(a)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a/'DONNEES').glob('*')}
   (a/'MANIFESTE.json').write_text(json.dumps({'fichiers':hashes}))
  # Quarante titulaires reels en forme, dont un ticker US sans faits :
  # le raccordement doit les couvrir sans leur inventer de note.
  cohort=[{'ID_ligne':str(i),'Ticker_cotation':('A.F' if i==1 else 'INFU' if i==2 else 'X'+str(i)+'.F'),
           'Societe':'Titulaire '+str(i),'Pays':'USA' if i==2 else 'Allemagne'} for i in range(1,41)]
  pd.DataFrame(cohort).to_csv(b/'DONNEES/COHORTE_MICRO_CAPS_T0.csv',index=False)
  # Reutilisation de la qualification US 07U, avec verification SHA256.
  us=b/'AUDITS/QUALIFICATION_US/20261016T000000Z'
  us.mkdir(parents=True)
  us_bruts=us/'BRUTS.csv.gz'
  pd.DataFrame([dict(f,Ticker='INFU.US',CIK='0000000022',Valeur='30')]).to_csv(us_bruts,index=False,compression='gzip')
  pd.DataFrame([{'Ticker_US':'INFU.US','CIK':'0000000022','Statut_origine':'PISTE_US_CONCORDANTE'}]).to_csv(us/'COUVERTURE_QUALIFICATION_US.csv',index=False)
  us_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (us_bruts,us/'COUVERTURE_QUALIFICATION_US.csv')}
  (us/'MANIFESTE.json').write_text(json.dumps({'fichiers':us_hashes}))
  before=(b/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv').read_bytes()
  with patch.object(m,'BASE',b):result=m.executer()
  assert result['archives_controlees']==2 and result['archives_qualification_us_controlees']==1
  assert result['observations_brutes_distinctes']==3
  assert result['observations_valeurs_divergentes']==1 and result['notes_attribuees']==0
  out=next((b/'AUDITS/SEC_CONSOLIDE').glob('*/FAITS_SEC_BRUTS_CONSOLIDES.csv'))
  d=pd.read_csv(out)
  assert all(d.loc[d.Ticker.eq('A.F'),'Statut_observation'].eq('VALEURS_DIVERGENTES_A_RELIRE'))
  assert d.loc[d.Ticker.eq('INFU.US'),'Statut_observation'].iloc[0]=='BRUT_A_VERIFIER'
  assert d.loc[d.Valeur.eq(10),'Archives_sources'].iloc[0]=='AUDITS/SEC/RUN_A|AUDITS/SEC/RUN_B'
  assert d.loc[d.Valeur.eq(10),'Representations_brutes'].iloc[0]=='10|10.0'
  couverture=pd.read_csv(out.parent/'COUVERTURE_TITULAIRES.csv')
  assert len(couverture)==40
  assert couverture.loc[couverture.ID_position.eq(1),'Nb_faits_bruts'].iloc[0]==2
  assert couverture.loc[couverture.ID_position.eq(2),'Ticker'].iloc[0]=='INFU.US'
  assert couverture.loc[couverture.ID_position.eq(2),'Nb_faits_bruts'].iloc[0]==1
  assert str(couverture.loc[couverture.ID_position.eq(2),'CIK_pistes'].iloc[0]).zfill(10)=='0000000022'
  assert couverture.Statut_SSI.eq('EN_ATTENTE_DATA').all()
  assert couverture.Statut_MCPA.eq('EN_ATTENTE_DATA').all()
  assert result['titulaires_couverts']==40 and result['titulaires_avec_pistes_SEC']==2
  assert (b/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv').read_bytes()==before
  contenu_us=us_bruts.read_bytes()
  us_bruts.write_bytes(b'CORROMPU')
  with patch.object(m,'BASE',b):
   try:m.executer()
   except RuntimeError as e:assert 'ARCHIVE_QUALIFICATION_US_SHA256_DIVERGENT' in str(e)
   else:raise AssertionError('Archive qualification US corrompue acceptee')
  us_bruts.write_bytes(contenu_us)
  (b/'AUDITS/SEC/RUN_A/DONNEES/FAITS_FINANCIERS_SEC_SSI.csv').write_bytes(b'CORROMPU')
  with patch.object(m,'BASE',b):
   try:m.executer()
   except RuntimeError as e:assert 'SHA256_DIVERGENT' in str(e)
   else:raise AssertionError('Archive corrompue acceptée')
 print('CONSOLIDATION SEC: provenance complète, valeurs divergentes conservées, corruption refusée')
if __name__=='__main__':test()

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
  for name,rows in [('RUN_A',[f]),('RUN_B',[f,dict(f,Valeur='20')])]:
   a=b/'AUDITS/SEC'/name;(a/'DONNEES').mkdir(parents=True)
   pd.DataFrame(rows).to_csv(a/'DONNEES/FAITS_FINANCIERS_SEC_SSI.csv',index=False)
   pd.DataFrame([{'Ticker':'A.F','CIK':'0000000001'}]).to_csv(a/'DONNEES/PREUVES_SEC_EDGAR_SSI.csv',index=False)
   hashes={str(p.relative_to(a)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a/'DONNEES').glob('*')}
   (a/'MANIFESTE.json').write_text(json.dumps({'fichiers':hashes}))
  before=(b/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv').read_bytes()
  with patch.object(m,'BASE',b):result=m.executer()
  assert result['archives_controlees']==2 and result['observations_brutes_distinctes']==2
  assert result['observations_valeurs_divergentes']==1 and result['notes_attribuees']==0
  out=next((b/'AUDITS/SEC_CONSOLIDE').glob('*/FAITS_SEC_BRUTS_CONSOLIDES.csv'))
  d=pd.read_csv(out)
  assert all(d.Statut_observation.eq('VALEURS_DIVERGENTES_A_RELIRE'))
  assert d.loc[d.Valeur.eq(10),'Archives_sources'].iloc[0]=='AUDITS/SEC/RUN_A|AUDITS/SEC/RUN_B'
  assert (b/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv').read_bytes()==before
  (b/'AUDITS/SEC/RUN_A/DONNEES/FAITS_FINANCIERS_SEC_SSI.csv').write_bytes(b'CORROMPU')
  with patch.object(m,'BASE',b):
   try:m.executer()
   except RuntimeError as e:assert 'SHA256_DIVERGENT' in str(e)
   else:raise AssertionError('Archive corrompue acceptée')
 print('CONSOLIDATION SEC: provenance complète, valeurs divergentes conservées, corruption refusée')
if __name__=='__main__':test()

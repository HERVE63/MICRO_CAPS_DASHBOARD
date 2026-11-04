"""Financial data semantics and safe adapter admission; fixtures never reach live CSV."""
import copy,importlib.util,json,unittest
from pathlib import Path
B=Path(__file__).resolve().parents[1]
def module(n,p):
 s=importlib.util.spec_from_file_location(n,B/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=module('adapter','SCRIPTS_ACTIFS/09S_ADAPTATEUR_FICHES_MCPA_40.py')
E=module('continued','SCRIPTS_ACTIFS/10B_COMPLETER_CALCULS_ET_STATUTS_40.py')
class Continuation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.docs={x['ticker']:x for x in (json.loads(p.read_text()) for p in (B/'DOSSIERS_MCPA_IPS_40').glob('*.json'))}
 def test_counts_distinguish_na_and_missing(self):
  for d in self.docs.values():
   c=d['audit_poursuite']['comptage'];self.assertEqual(sum(c.values()),108)
   cells=[x for block in d['blocs'].values() for x in block.values()]
   self.assertEqual(c['NON_APPLICABLE'],sum(x['statut']=='NON_APPLICABLE' for x in cells))
   self.assertEqual(c['RENSEIGNE'],sum(x['valeur'] is not None for x in cells))
 def test_negative_denominator_is_not_zero_ratio(self):
  d=copy.deepcopy(self.docs['IDN']);d['blocs']['valorisation']['pe']['valeur']=None
  E.na(d,'valorisation','pe','Loss denominator','https://example.invalid/fixture','fixture')
  self.assertIsNone(d['blocs']['valorisation']['pe']['valeur']);self.assertEqual(d['blocs']['valorisation']['pe']['statut'],'NON_APPLICABLE')
 def test_idn_dilution_is_three_years(self):
  self.assertAlmostEqual(self.docs['IDN']['blocs']['risque']['dilution_3a_pct']['valeur'],(20.23/18.96-1)*100)
 def test_proxy_correlation_disclosed_and_finite(self):
  for d in self.docs.values():
   c=d['blocs']['diversification']['correlation_portefeuille']
   self.assertLessEqual(abs(c['valeur']),1);self.assertIn('39 autres',c['commentaire']);self.assertIn('FX',c['commentaire'])
 def test_eod_denial_not_final_unavailability(self):
  for d in self.docs.values():
   r=next(r for r in d['journal_recherches'] if r['famille']=='EODHD_fondamentaux_execution_GitHub')
   self.assertIn(r['http'],('403','404'));self.assertIn('pas preuve',r['limite'])
 def fixture(self):
  d=copy.deepcopy(self.docs['IDN']);d['date_revue']='2026-11-03';n=d['notation'];n['notes']={b:0 for b in n['bareme']};n['total_mcpa']=0;n['justifications']={b:'FIXTURE TECHNIQUE, AUCUNE NOTE FINANCIERE' for b in n['bareme']}
  c=d['blocs']['complements']
  for k in c:c[k]['valeur']='FIXTURE'
  for k,v in [('ssi',65),('ic_sur_5',0),('cx_sur_5',0),('wwws',0),('delta',0),('decision','ATTENTE')]:c[k]['valeur']=v
  for h in ('3m','6m'):
   for case,p in [('bear',25),('central',50),('bull',25)]:c['prob_'+case+'_'+h+'_pct']['valeur']=p;c['scenario_'+case+'_'+h+'_pct']['valeur']=0
  for block in d['blocs'].values():
   for c in block.values():c['date_source']='2026-11-03'
  d['blocs']['risque']['risque_gouvernance']['valeur']='FIXTURE';d['blocs']['croissance']['catalyseurs_dates']['valeur']='FIXTURE'
  return d
 def test_complete_fixture_accepted_by_numeric_gate(self):self.assertEqual(A.validation_individuelle(self.fixture()),[])
 def test_invalid_probabilities_and_scores_rejected(self):
  d=self.fixture();d['notation']['notes']['qualite']=31;d['blocs']['complements']['prob_bear_6m_pct']['valeur']=51
  issues=A.validation_individuelle(d);self.assertIn('SOUS_NOTE_INVALIDE:qualite',issues);self.assertIn('PROBABILITES_INCOHERENTES:6m',issues)
 def test_low_ssi_and_future_sources_rejected(self):
  d=self.fixture();d['blocs']['complements']['ssi']['valeur']=64;d['blocs']['qualite']['ca_ttm']['date_source']='2026-11-04'
  issues=A.validation_individuelle(d);self.assertIn('SSI_SOUS_SEUIL_65',issues);self.assertIn('SOURCES_POSTERIEURES_A_REVUE',issues)
if __name__=='__main__':unittest.main()

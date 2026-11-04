#!/usr/bin/env python3
"""Audit evidence retention, units, windows and safe filtering on forty real dossiers."""
import csv,hashlib,importlib.util,json,math,subprocess,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];F=BASE/'DOSSIERS_MCPA_IPS_40';D=BASE/'DONNEES'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,BASE/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=module('enrich','SCRIPTS_ACTIFS/09X_ENRICHIR_AUDITER_40.py')
class Audit40(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.paths=sorted(F.glob('*.json'));cls.docs={x['ticker']:x for x in map(lambda p:json.loads(p.read_text()),cls.paths)}
 def test_01_exact_cohort(self):
  with (D/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv').open() as f:holdings=list(csv.DictReader(f))
  self.assertEqual(len(self.paths),40)
  self.assertEqual({(x['ticker'],x['societe'],x['devise'],x['id_position']) for x in self.docs.values()},{(r['Ticker'],r['Societe'],r['Devise'],int(r['ID_position'])) for r in holdings})
 def test_02_original_verified_cells_unchanged(self):
  for p in self.paths:
   before=json.loads(subprocess.check_output(['git','show',M.BASELINE_COMMIT+':'+str(p.relative_to(BASE))],cwd=BASE,text=True));after=self.docs[before['ticker']]
   for b,block in before['blocs'].items():
    for k,c in block.items():
     if c['valeur'] is not None:self.assertEqual(c,{key:after['blocs'][b][k][key] for key in c},(before['ticker'],b,k))
   self.assertEqual(before['notation'],after['notation'])
 def test_03_complete_metadata_for_values(self):
  for x in self.docs.values():
   for b,block in x['blocs'].items():
    for k,c in block.items():
     self.assertTrue({'valeur','unite','periode','date_source','source_url','statut','commentaire'}<=c.keys())
     if c['valeur'] is not None:
      for name in ('unite','periode','date_source','source_url','statut'):self.assertTrue(c[name],(x['ticker'],b,k,name))
      self.assertNotIn('recherche',c)
 def test_04_missing_is_explicit_never_final_unavailability(self):
  for x in self.docs.values():
   for block in x['blocs'].values():
    for c in block.values():
     if c['valeur'] is None:self.assertEqual(c['recherche']['statut'],'MANQUANT_RECHERCHE_NON_CLOSE')
   self.assertEqual(x['audit_couverture']['indisponibilite_definitive_demontree'],[])
 def test_05_no_scores_or_orders(self):
  for x in self.docs.values():
   self.assertFalse(x['arbitrage_autorise']);self.assertIsNone(x['notation']['total_mcpa']);self.assertEqual(x['notation']['statut'],'NON_VALIDEE')
 def test_06_london_pence_conversion(self):
  self.assertAlmostEqual(self.docs['AOM.L']['blocs']['valorisation']['cours']['valeur'],.89)
 def test_07_short_ipo_does_not_fabricate_history(self):
  m=self.docs['ALIEV.PA']['blocs']['momentum']
  for k in ('prix_vers_mm200','tendance_mm200','momentum_12m_pct','drawdown_12m_pct'):self.assertIsNone(m[k]['valeur'])
 def test_08_na_never_becomes_zero(self):
  self.assertIsNone(M.number('n/a'));self.assertEqual(M.number('0'),0);self.assertEqual(M.number('-1.25M'),-1250000)
 def test_09_conflicting_prices_rejected(self):
  x=json.loads(json.dumps(self.docs['IDN']));row={'Date_UTC':'2026-11-03','AdjClose':'2','Close':'2','Volume':'10','Source':'test'}
  with self.assertRaises(ValueError):M.market(x,[row,dict(row,Close='3')])
 def test_10_insider_totals_respect_incompleteness(self):
  rows=json.loads((BASE/'AUDITS/FINALISATION_FICHES_20261104/SEC/INITIES_5_US.json').read_text())
  for r in rows:
   for days,v in r['totaux'].items():
    cell=self.docs[r['ticker']]['blocs']['risque']['transactions_initiees_net_'+days+'j']
    if v['statut']=='INCOMPLET':self.assertIsNone(cell['valeur'])
    else:self.assertEqual(cell['valeur'],v['valeur'])
 def test_11_coverage_counts_are_exact(self):
  for x in self.docs.values():
   cells=[c for block in x['blocs'].values() for c in block.values()];a=x['audit_couverture']
   self.assertEqual(len(cells),108);self.assertEqual(a['champs_renseignes'],sum(c['valeur'] is not None for c in cells));self.assertEqual(a['champs_total'],108)
 def test_12_filter_connector_keeps_live_review_unchanged(self):
  p=D/'REVUE_HEBDOMADAIRE_MCPA_IPS.csv';before=p.read_bytes()
  adaptor=module('adaptor','SCRIPTS_ACTIFS/09S_ADAPTATEUR_FICHES_MCPA_40.py');self.assertEqual(adaptor.main(),0);self.assertEqual(p.read_bytes(),before)
 def test_13_research_trace_for_every_company(self):
  for x in self.docs.values():
   self.assertTrue({'fondamentaux','valorisation_revisions_inities','transactions_inities','statistiques_financieres'}<={r['famille'] for r in x['journal_recherches']})
 def test_14_no_nonfinite_numbers(self):
  def walk(v):
   if isinstance(v,float):self.assertTrue(math.isfinite(v))
   elif isinstance(v,dict):
    for x in v.values():walk(x)
   elif isinstance(v,list):
    for x in v:walk(x)
  for x in self.docs.values():walk(x)
 def test_15_idempotent_offline_enrichment(self):
  before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.paths};M.main()
  self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.paths})
if __name__=='__main__':unittest.main(verbosity=2)

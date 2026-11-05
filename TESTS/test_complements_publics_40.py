"""Consensus dates/currencies, zero denominators and verified-cell preservation."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
B=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('import_public',B/'SCRIPTS_ACTIFS/10H_IMPORTER_COMPLEMENTS_PUBLICS_40.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
class PublicEvidence(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.b=Path(self.tmp.name);self.d=self.b/'DONNEES';self.f=self.b/'DOSSIERS_MCPA_IPS_40';self.d.mkdir();self.f.mkdir();M.B=self.b;M.D=self.d;M.F=self.f
  self.paths=sorted((B/'DOSSIERS_MCPA_IPS_40').glob('*.json'));self.docs=[json.loads(p.read_text()) for p in self.paths]
  self.annual=json.loads((B/'DONNEES/IDENTITES_CROISSANCE_40_20261104.json').read_text());self.records=[dict(ticker=d['ticker'],date_collecte='2026-11-05') for d in self.docs];self.idn=next(d for d in self.docs if d['ticker']=='IDN');self.record=next(r for r in self.records if r['ticker']=='IDN')
 def tearDown(self):self.tmp.cleanup()
 def write(self):
  for p,d in zip(self.paths,self.docs):(self.f/p.name).write_text(json.dumps(d))
  (self.d/'IDENTITES_CROISSANCE_40_20261104.json').write_text(json.dumps(self.annual));(self.d/'COMPLEMENTS_PUBLICS_40_20261105.json').write_text(json.dumps(self.records))
 def idn_after(self):return next(json.loads(p.read_text()) for p in self.f.glob('*.json') if json.loads(p.read_text())['ticker']=='IDN')
 def trend(self,current=.13,old=.195):return dict(period='0y',endDate='2026-12-31',epsTrend={'current':{'raw':current},'30daysAgo':{'raw':old},'90daysAgo':{'raw':old},'epsTrendCurrency':'USD'},earningsEstimate={'numberOfAnalysts':{'raw':3}})
 def prepare(self,t=None):self.record['revisions']=dict(url='https://example.invalid/fixture',statut='FIXTURE',tendances=[t or self.trend()])
 def test_same_fiscal_year_revisions(self):
  self.prepare();self.write();M.main();c=self.idn_after()['blocs']['croissance']['revision_bpa_30j_pct'];self.assertAlmostEqual(c['valeur'],-100/3);self.assertIn('2026-12-31',c['periode']);self.assertEqual(c['date_source'],'2026-11-05')
 def test_no_current_consensus_is_not_zero_revision(self):
  self.prepare(self.trend(current=None));self.write();M.main();self.assertIsNone(self.idn_after()['blocs']['croissance']['revision_bpa_30j_pct']['valeur'])
 def test_zero_base_explicit_na(self):
  self.prepare(self.trend(old=0));self.write();M.main();c=self.idn_after()['blocs']['croissance']['revision_bpa_30j_pct'];self.assertIsNone(c['valeur']);self.assertEqual(c['statut'],'NON_APPLICABLE')
 def test_past_fiscal_year_not_substituted(self):
  t=self.trend();t['endDate']='2025-12-31';self.prepare(t);self.write();M.main();self.assertIsNone(self.idn_after()['blocs']['croissance']['revision_bpa_30j_pct']['valeur'])
 def test_existing_verified_value_never_overwritten(self):
  c=self.idn['blocs']['croissance']['revision_bpa_30j_pct'];c.update(valeur=12.34,unite='pct',periode='verified fixture',date_source='2026-11-04',source_url='https://example.invalid/verified',statut='SOURCE_PRIMAIRE');c.pop('recherche',None);before=copy.deepcopy(c);self.prepare();self.write();M.main();self.assertEqual(self.idn_after()['blocs']['croissance']['revision_bpa_30j_pct'],before)
 def test_idempotent_and_all_forty_processed(self):
  self.prepare();self.write();M.main();before={p.name:p.read_bytes() for p in self.f.glob('*.json')};M.main();self.assertEqual(before,{p.name:p.read_bytes() for p in self.f.glob('*.json')});self.assertEqual(len(before),40)
if __name__=='__main__':unittest.main()

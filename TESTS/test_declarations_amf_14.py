"""Use real public AMF forms to verify bilingual/multiline parsing and fail-closed totals."""
import copy,importlib.util,json,unittest,subprocess
from pathlib import Path
B=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('amf',B/'SCRIPTS_ACTIFS/10L_COLLECTE_DECLARATIONS_AMF_14.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
class AMF(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={r['ticker']:r for r in json.loads((B/'DONNEES/DECLARATIONS_AMF_14_20261105.json').read_text())}
 def text(self,ticker,numero):
  r=self.rows[ticker];rec=next(x for x in r['declarations'] if x['numero']==numero);pdf=B/rec['archive_pdf'];textpath=pdf.with_suffix('.txt')
  if not textpath.exists():subprocess.run(['pdftotext','-layout',str(pdf),str(textpath)],check=True,capture_output=True)
  return textpath.read_text(),r['isin']
 def test_exact_fourteen_issuers_and_all_pages(self):
  self.assertEqual(len(self.rows),14)
  for r in self.rows.values():self.assertTrue(r['pagination_complete']);self.assertEqual(len(r['declarations']),r['nombre_declarations_2026']);self.assertFalse(r['erreurs'])
 def test_bilingual_without_repeated_isin_label(self):
  text,isin=self.text('ALICA.PA','2026DD1144856');r=M.parse(text,isin);self.assertEqual(len(r['transactions']),1);self.assertEqual(r['transactions'][0]['valeur_nette'],-198000)
 def test_multiple_transaction_dates_are_separate(self):
  text,isin=self.text('ALMCE.PA','2026DD1147733');r=M.parse(text,isin);self.assertEqual(len(r['transactions']),3);self.assertEqual([x['date_transaction'] for x in r['transactions']],['2026-10-27','2026-10-28','2026-10-29'])
 def test_multiple_prices_use_elementary_cash_amounts(self):
  text,isin=self.text('ALLIX.PA','2026DD1117678');r=M.parse(text,isin);self.assertEqual(r['transactions'][0]['valeur_nette'],-482100);self.assertEqual(len(r['transactions'][0]['operations_elementaires']),2)
 def test_missing_instrument_is_never_zero_or_exclusion(self):
  text,isin=self.text('ALICA.PA','2026DD1144856');text=text.replace('DESCRIPTION DE L’INSTRUMENT FINANCIER','MISSING FIELD LABEL')
  with self.assertRaises(ValueError):M.parse(text,isin)
 def test_wrong_isin_rejected(self):
  text,_=self.text('ALICA.PA','2026DD1144856')
  with self.assertRaisesRegex(ValueError,'ISIN'):M.parse(text,'US0000000000')
 def test_no_registry_coverage_cannot_create_zero(self):
  r=copy.deepcopy(self.rows['MEMS.PA']);r['pagination_complete']=False
  with self.assertRaisesRegex(ValueError,'Couverture'):M.aggregate(r)
 def test_known_empty_registry_zero_has_exact_issuer_proof(self):
  r=self.rows['MEMS.PA'];self.assertEqual(r['totaux']['180']['valeur'],0);self.assertEqual(r['nombre_declarations_2026'],0);self.assertTrue(any('Jetons='+r['jeton'] in q['url'] for q in r['recherches']))
 def test_unparsed_document_blocks_both_windows(self):
  r=copy.deepcopy(self.rows['MEMS.PA']);r['declarations']=[{'numero':'FIXTURE','statut':'NON_PARSEE'}];M.aggregate(r);self.assertIsNone(r['totaux']['90']['valeur']);self.assertIsNone(r['totaux']['180']['valeur'])
 def test_window_dates_are_transaction_dates(self):
  r=self.rows['ALSTI.PA'];self.assertEqual(r['totaux']['90']['valeur'],0);self.assertEqual(r['totaux']['180']['valeur'],-377475)
if __name__=='__main__':unittest.main()

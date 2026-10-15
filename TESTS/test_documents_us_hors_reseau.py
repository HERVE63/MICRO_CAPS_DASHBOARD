"""Pièces SEC : refus des dates futures, traversées et redirections étrangères."""
from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('doc_us',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AF_COLLECTER_DOCUMENTS_US.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 assert m.url_document('0001328792','0001328792-26-000001','annual.htm')=='https://www.sec.gov/Archives/edgar/data/1328792/000132879226000001/annual.htm'
 for doc in ['../annual.htm','/annual.htm','https://evil.test/a','a?password=x']:
  try:m.url_document('1','0001328792-26-000001',doc)
  except ValueError:pass
  else:raise AssertionError('Chemin dangereux accepté')
 q={'filings':{'recent':{'form':['10-K','10-K','DEF 14A'],'filingDate':['2026-08-01','2026-11-01','2026-09-01'],
     'accessionNumber':['0001328792-26-000001','0001328792-26-000002','0001328792-26-000003'],'primaryDocument':['old.htm','future.htm','proxy.htm']}}}
 r=m.choisir(q,'2026-10-15');assert r['10-K']['Document_primaire']=='old.htm' and r['10-Q'] is None
 try:m.RedirectionsSEC().redirect_request(None,None,302,'',{},'https://evil.test/a')
 except ValueError:pass
 else:raise AssertionError('Redirection externe acceptée')
 print('DOCUMENTS US: dépôt connu, date limite, chemins et redirections contrôlés')
if __name__=='__main__':test()

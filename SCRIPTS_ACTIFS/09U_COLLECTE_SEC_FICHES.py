#!/usr/bin/env python3
"""Collect public SEC facts and issuer identity without credentials or orders."""
import concurrent.futures, hashlib, json, urllib.request
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'AUDITS/FINALISATION_FICHES_20261104/SEC'
CIKS={'IDN':'0001040896','INFU':'0001337013','OSS':'0001394056','CXDO':'0001075736','LWAY':'0000814586'}
def collect(item):
 ticker,cik=item; results=[]
 for kind,url in [('submissions',f'https://data.sec.gov/submissions/CIK{cik}.json'),('companyfacts',f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json')]:
  row={'ticker':ticker,'type':kind,'url':url,'date_collecte':'2026-11-04'}
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Microcaps research contact research@example.com','Accept':'application/json'})
   with urllib.request.urlopen(req,timeout=25) as response: raw=response.read();row['http']=response.status
   data=json.loads(raw)
   if kind=='submissions' and ticker not in data.get('tickers',[]):raise ValueError('Ticker mismatch')
   p=OUT/f'{ticker}_{kind}.json';p.write_bytes(raw)
   row.update(statut='COLLECTE',sha256=hashlib.sha256(raw).hexdigest(),fichier=str(p.relative_to(BASE)))
  except Exception as exc:row.update(statut='ECHEC_ACCES',erreur=type(exc).__name__,http=getattr(exc,'code',None))
  results.append(row)
 return results
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: rows=[x for batch in pool.map(collect,CIKS.items()) for x in batch]
 (OUT/'MANIFESTE.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps([{k:r.get(k) for k in ('ticker','type','statut','http')} for r in rows]))
if __name__=='__main__':main()

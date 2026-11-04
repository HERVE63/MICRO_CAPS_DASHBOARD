#!/usr/bin/env python3
"""Collect only missing annual share-count evidence; preserve prior acquisitions."""
import concurrent.futures,hashlib,html,importlib.util,json,re,urllib.request
from pathlib import Path
B=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('stats',B/'SCRIPTS_ACTIFS/09V_COLLECTE_STATISTIQUES_40.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OUT=B/'DONNEES/BILANS_ANNUELS_40_20261104.json'
cache={r['ticker']:r for r in json.loads(OUT.read_text())} if OUT.exists() else {}
def collect(d):
 t=d['ticker']
 if t in cache:return cache[t]
 url=m.url_for(t).removesuffix('statistics/')+'financials/balance-sheet/';r=dict(ticker=t,url=url,date_collecte='2026-11-04')
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as resp:raw=resp.read();r['http']=resp.status
  txt=raw.decode();title=html.unescape(re.search('<title>(.*?)</title>',txt,re.S)[1]);r['titre']=title
  if not re.search(r'\b'+re.escape(t.split('.')[0])+r'\b',title,re.I):raise ValueError('Identite incompatible')
  parser=m.Tables();parser.feed(txt);r['lignes']=[x for x in parser.rows if x[0] in ('Fiscal Year','Period Ending','Total Common Shares Outstanding','Shares Outstanding','Total Debt','Cash & Equivalents','Current Assets','Current Liabilities')]
  r['sha256_page']=hashlib.sha256(raw).hexdigest();r['statut']='SOURCE_SECONDAIRE_A_RAPPROCHER'
 except Exception as e:r.update(statut='ECHEC_ACCES_OU_IDENTITE',http=getattr(e,'code',None),erreur=type(e).__name__)
 return r
if __name__=='__main__':
 docs=[json.loads(p.read_text()) for p in (B/'DOSSIERS_MCPA_IPS_40').glob('*.json')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:rows=list(ex.map(collect,sorted(docs,key=lambda x:x['id_position'])))
 OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print({s:sum(r['statut']==s for r in rows) for s in set(r['statut'] for r in rows)})

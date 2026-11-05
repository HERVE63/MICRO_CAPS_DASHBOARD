#!/usr/bin/env python3
"""Retry only inaccessible historical-ratio pages; keep successful evidence intact."""
import concurrent.futures,datetime as dt,hashlib,html,importlib.util,json,re,urllib.request
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'DONNEES'
s=importlib.util.spec_from_file_location('collector',B/'SCRIPTS_ACTIFS/10G_COLLECTE_COMPLEMENTS_PUBLICS_40.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def repair(r):
 old=r.get('valorisation_historique',{})
 if old.get('statut')=='SOURCE_SECONDAIRE_HISTORIQUE' or not old.get('url'):return r
 v={'url':old['url'],'echecs_precedents':old.get('echecs_precedents',[])+[{k:v for k,v in old.items() if k!='echecs_precedents'}]}
 try:
  raw,status=m.raw(v['url']);txt=raw.decode();title=html.unescape(re.search('<title>(.*?)</title>',txt,re.S)[1])
  if not re.search(r'\b'+re.escape(r['ticker'].split('.')[0])+r'\b',title,re.I):raise ValueError('Identite divergente')
  p=m.Tables();p.feed(txt);seen=set();rows=[]
  for row in p.rows:
   if row[0] in ('Fiscal Year','Period Ending','PE Ratio','P/FCF Ratio','EV / EBITDA','EV / Sales','EV / Revenue') and row[0] not in seen:rows.append(row);seen.add(row[0])
  v.update(http=status,statut='SOURCE_SECONDAIRE_HISTORIQUE',sha256_reponse=hashlib.sha256(raw).hexdigest(),lignes=rows)
 except Exception as e:v.update(http=getattr(e,'code',None),statut='ECHEC',erreur=type(e).__name__)
 r['valorisation_historique']=v;return r
if __name__=='__main__':
 path=sorted(D.glob('COMPLEMENTS_PUBLICS_40_*.json'))[-1];rows=json.loads(path.read_text())
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(repair,rows))
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');tmp.replace(path);print(sum(r.get('valorisation_historique',{}).get('statut')=='SOURCE_SECONDAIRE_HISTORIQUE' for r in rows))

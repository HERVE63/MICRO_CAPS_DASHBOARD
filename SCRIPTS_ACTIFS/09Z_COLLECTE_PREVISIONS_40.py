#!/usr/bin/env python3
"""Collect explicitly labelled annual consensus forecasts and their currency."""
import concurrent.futures,csv,hashlib,html,importlib.util,json,re,urllib.request
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('statcollector',BASE/'SCRIPTS_ACTIFS/09V_COLLECTE_STATISTIQUES_40.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def collect(h):
 t=h['Ticker'];url=m.url_for(t).removesuffix('statistics/')+'forecast/';out={'ticker':t,'url':url,'date_collecte':'2026-11-04'}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=20) as response:raw=response.read();out['http']=response.status
  text=raw.decode();out['titre']=html.unescape(re.search(r'<title>(.*?)</title>',text,re.S)[1])
  if not re.search(r'\b'+re.escape(t.split('.')[0])+r'\b',out['titre'],re.I):raise ValueError('Ticker mismatch')
  parser=m.Tables();parser.feed(text);out['lignes']=[];seen=set()
  for row in parser.rows:
   if row[0] in ('Fiscal Year','Period Ending','Revenue','EPS') and row[0] not in seen:out['lignes'].append(row);seen.add(row[0])
  plain=re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',text)));currency=re.search(r'Financial currency is ([A-Z]{3})',plain)
  out['devise_previsions']=currency[1] if currency else None
  out['eps_non_gaap_ajuste']='non-GAAP adjusted' in plain
  out.update(sha256_page=hashlib.sha256(raw).hexdigest(),statut='SOURCE_SECONDAIRE_PREVISIONS' if out['lignes'] else 'PREVISIONS_NON_EXPOSEES_SUR_PAGE')
 except Exception as exc:out.update(statut='ECHEC_ACCES_OU_IDENTITE',erreur=type(exc).__name__,http=getattr(exc,'code',out.get('http')))
 return out
def main():
 with (BASE/'DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv').open() as f:holdings=list(csv.DictReader(f))
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:rows=list(ex.map(collect,holdings))
 (BASE/'DONNEES/PREVISIONS_40_20261104.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps([{'ticker':r['ticker'],'statut':r['statut'],'devise':r.get('devise_previsions')} for r in rows]))
if __name__=='__main__':main()

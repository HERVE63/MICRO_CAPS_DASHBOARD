#!/usr/bin/env python3
"""Secondary issuer profiles and annual growth series, with explicit fiscal dates."""
import concurrent.futures,csv,hashlib,html,importlib.util,json,re,urllib.request
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('statcollector',BASE/'SCRIPTS_ACTIFS/09V_COLLECTE_STATISTIQUES_40.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
PROFILE={'Country','Industry','Sector','Exchange','Reporting Currency','ISIN Number','Fiscal Year','Ticker Symbol'}
FINANCE={'Fiscal Year','Period Ending','Fiscal Quarter','Revenue','Revenue Growth (YoY)','EBITDA','EBITDA Growth','EPS (Diluted)','EPS Growth','Free Cash Flow','Net Income','Revenue Growth'}
def collect(h):
 t=h['Ticker'];base=mod.url_for(t).removesuffix('statistics/');out={'ticker':t,'date_collecte':'2026-11-04'}
 cachefile=BASE/'DONNEES/IDENTITES_CROISSANCE_40_20261104.json'
 cache={r['ticker']:r for r in json.loads(cachefile.read_text())} if cachefile.exists() else {}
 for kind,path in [('profil','company/'),('annuel','financials/')]:
  if kind=='profil' and cache.get(t,{}).get(kind,{}).get('statut')=='SOURCE_SECONDAIRE_A_RAPPROCHER':out[kind]=cache[t][kind];continue
  url=base+path;r={'url':url}
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=20) as response:raw=response.read();r['http']=response.status
   text=raw.decode();title=html.unescape(re.search(r'<title>(.*?)</title>',text,re.S)[1]);r['titre']=title
   if not re.search(r'\b'+re.escape(t.split('.')[0])+r'\b',title,re.I):raise ValueError('Ticker mismatch')
   parser=mod.Tables();parser.feed(text)
   aliases={'Revenue Revenue Growth':'Revenue','Net Income Net Income Growth':'Net Income','Earnings Per Share EPS Growth':'EPS (Diluted)','Free Cash Flow Free Cash Flow Growth':'Free Cash Flow','EBITDA EBITDA Growth':'EBITDA'}
   normalized=[[aliases.get(row[0],row[0])]+row[1:] for row in parser.rows]
   r['lignes']=[];seen=set()
   for row in normalized:
    if row[0] in (PROFILE if kind=='profil' else FINANCE) and row[0] not in seen:r['lignes'].append(row);seen.add(row[0])
   r['sha256_page']=hashlib.sha256(raw).hexdigest();r['statut']='SOURCE_SECONDAIRE_A_RAPPROCHER'
   if kind=='annuel':
    # Preserve the unit statement; annual values cannot be imported without it.
    plain=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]*>',' ',text)))
    m=re.search(r'(?:Financials in [A-Z]{3}|Numbers in (?:millions|thousands)|All numbers in|in millions|in thousands).{0,100}',plain,re.I);r['mention_unites']=m.group(0) if m else None
  except Exception as e:r.update(statut='ECHEC_ACCES_OU_IDENTITE',erreur=type(e).__name__,http=getattr(e,'code',r.get('http')))
  out[kind]=r
 return out
def main():
 with (BASE/'DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv').open() as f:holdings=list(csv.DictReader(f))
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:rows=list(ex.map(collect,holdings))
 (BASE/'DONNEES/IDENTITES_CROISSANCE_40_20261104.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps([{'ticker':r['ticker'],'profil':r['profil']['statut'],'annuel':r['annuel']['statut']} for r in rows]))
if __name__=='__main__':main()

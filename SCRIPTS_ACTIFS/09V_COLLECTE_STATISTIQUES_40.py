#!/usr/bin/env python3
"""Collect secondary financial statistics for each exact listing, never n/a=0.
Only selected facts are retained; no complete copyrighted page is republished.
"""
import csv,concurrent.futures,hashlib,html,json,re,urllib.request
from html.parser import HTMLParser
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'DONNEES/STATISTIQUES_SECONDAIRES_40_20261104.json'
LABELS=set('Market Cap|Enterprise Value|Shares Outstanding|Shares Change (YoY)|Owned by Insiders (%)|Float|PE Ratio|Forward PE|PS Ratio|PB Ratio|P/FCF Ratio|PEG Ratio|EV / Sales|EV / EBITDA|EV / EBIT|Current Ratio|Interest Coverage|Return on Equity (ROE)|Return on Invested Capital (ROIC)|Revenue|Gross Profit|Operating Income|Net Income|EBITDA|Earnings Per Share (EPS)|Cash & Cash Equivalents|Total Debt|Net Cash|Equity (Book Value)|Operating Cash Flow|Capital Expenditures|Free Cash Flow|Gross Margin|Operating Margin|Profit Margin|EBITDA Margin|FCF Yield|Revenue Growth Forecast (3Y)|EPS Growth Forecast (3Y)|Earnings Date'.split('|'))
class Tables(HTMLParser):
 def __init__(self):super().__init__();self.table=0;self.cell=False;self.text='';self.row=[];self.rows=[]
 def handle_starttag(self,tag,attrs):
  if tag=='table':self.table+=1
  if self.table and tag=='tr':self.row=[]
  if self.table and tag in ('td','th'):self.cell=True;self.text=''
 def handle_data(self,s):
  if self.cell:self.text+=s
 def handle_endtag(self,tag):
  if self.table and tag in ('td','th'):self.row.append(re.sub(r'\s+',' ',self.text).strip());self.cell=False
  if self.table and tag=='tr' and len(self.row)>=2:self.rows.append(self.row)
  if tag=='table':self.table-=1
def url_for(t):
 if '.' not in t:return f'https://stockanalysis.com/stocks/{t.lower()}/statistics/'
 code,suffix=t.rsplit('.',1);exchange={'L':'aim','PA':'epa','TO':'tsx','V':'tsxv','ST':'sto','MI':'bit'}[suffix]
 if t=='PLEJD.ST':exchange='xsat' # exact issuer on Spotlight; cohort ticker preserved
 return f'https://stockanalysis.com/quote/{exchange}/{code}/statistics/'
def collect(row):
 t=row['Ticker'];url=url_for(t);out={'ticker':t,'societe_attendue':row['Societe'],'url':url,'date_collecte':'2026-11-04'}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=25) as r:raw=r.read();out['http']=r.status;out['url_effective']=r.url
  s=raw.decode('utf-8');out['sha256_page']=hashlib.sha256(raw).hexdigest()
  title=html.unescape(re.search(r'<title>(.*?)</title>',s,re.S)[1]);out['titre']=title
  # Require the exact requested ticker in the page title, not a redirected peer.
  expected=t.split('.')[0]
  if not re.search(r'\b'+re.escape(expected)+r'\b',title,re.I):raise ValueError('Ticker absent du titre')
  parser=Tables();parser.feed(s)
  out['mesures']={r[0]:r[1] for r in parser.rows if r[0] in LABELS}
  # Site explicitly identifies these statement metrics as trailing twelve months.
  plain=re.sub('<[^>]*>',' ',s);plain=html.unescape(re.sub(r'\s+',' ',plain))
  m=re.search(r'.{0,70}last 12 months.{0,160}',plain,re.I)
  out['mention_ttm']=m.group(0) if m else None
  m=re.search(r'Last updated: ?([A-Za-z]+ \d{1,2}, \d{4})',plain)
  out['date_maj_fournisseur']=m.group(1) if m else None
  # Currency text is kept for a manual identity/currency check before importing money.
  out['devise_cotation_attendue']=row['Devise']
  m=re.search(r'last 12 months,.{0,100}?revenue of (USD|CAD|GBP|EUR|SEK|\$)',plain,re.I)
  out['devise_comptes_fournisseur']=(('USD' if m.group(1)=='$' else m.group(1).upper()) if m else None)
  out.pop('mention_devise',None)
  out['statut']='SOURCE_SECONDAIRE_A_RAPPROCHER'
 except Exception as e:out.update(statut='ECHEC_ACCES_OU_IDENTITE',erreur=type(e).__name__,http=getattr(e,'code',out.get('http')))
 return out
def main():
 with (BASE/'DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv').open() as f:holdings=list(csv.DictReader(f))
 if OUT.exists():
  previous={r['ticker']:r for r in json.loads(OUT.read_text())}
 else:previous={}
 pending=[r for r in holdings if previous.get(r['Ticker'],{}).get('statut')!='SOURCE_SECONDAIRE_A_RAPPROCHER']
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:new=list(ex.map(collect,pending))
 previous.update({r['ticker']:r for r in new})
 rows=[previous[r['Ticker']] for r in holdings]
 for r in rows:
  if 'devise_comptes_fournisseur' not in r:
   m=re.search(r'last 12 months,.{0,100}?revenue of (USD|CAD|GBP|EUR|SEK|\$)',r.get('mention_ttm') or '',re.I)
   r['devise_comptes_fournisseur']=(('USD' if m.group(1)=='$' else m.group(1).upper()) if m else None)
  r.pop('mention_devise',None)
 OUT.write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps([{'ticker':r['ticker'],'statut':r['statut'],'mesures':len(r.get('mesures',{})),'ttm':bool(r.get('mention_ttm'))} for r in rows]))
if __name__=='__main__':main()

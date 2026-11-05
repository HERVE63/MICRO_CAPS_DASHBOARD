#!/usr/bin/env python3
"""Same-currency performance comparison with a disclosed MSCI World ETF proxy."""
import concurrent.futures,csv,datetime as dt,hashlib,json,math,calendar,urllib.request,urllib.parse
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'DONNEES';F=B/'DOSSIERS_MCPA_IPS_40';DATE='2026-11-05';CUTOFF='2026-11-03';OUT=D/'REFERENCE_RELATIVE_MSCI_WORLD_20261105.json'
def collect(symbol):
 url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol,safe='')+'?range=2y&interval=1d&events=div%2Csplits';r=dict(symbol=symbol,url=url,date_collecte=DATE)
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as response:raw=response.read();r['http']=response.status
  x=json.loads(raw)['chart']['result'][0]
  if x['meta']['symbol']!=symbol or x['meta']['currency']!='USD':raise ValueError('Identite/devise divergente')
  vals=x['indicators']['adjclose'][0]['adjclose'] if symbol=='URTH' else x['indicators']['quote'][0]['close'];r['observations']={dt.datetime.fromtimestamp(ts,dt.timezone.utc).date().isoformat():v for ts,v in zip(x['timestamp'],vals) if v is not None and v>0 and dt.datetime.fromtimestamp(ts,dt.timezone.utc).date().isoformat()<=CUTOFF};r.update(sha256_reponse=hashlib.sha256(raw).hexdigest(),statut='SOURCE_MARCHE_SECONDAIRE',currency='USD')
 except Exception as e:r.update(statut='ECHEC',http=getattr(e,'code',r.get('http')),erreur=type(e).__name__)
 return r
def before(date,months):
 d=dt.date.fromisoformat(date);y,m=divmod(d.year*12+d.month-1-months,12);m+=1;return dt.date(y,m,min(d.day,calendar.monthrange(y,m)[1])).isoformat()
def main():
 if OUT.exists():ref=json.loads(OUT.read_text())
 else:
  with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:rr=list(ex.map(collect,['URTH','EURUSD=X','GBPUSD=X','CADUSD=X','SEKUSD=X']))
  ref=dict(reference_emetteur='https://www.ishares.com/us/products/239696/ishares-msci-world-etf',limite='URTH réplique MSCI World Net : frais/écart de suivi; ce ne sont pas les cours officiels de l’indice.',series=rr);OUT.write_text(json.dumps(ref,ensure_ascii=False,indent=2)+'\n')
 refs={r['symbol']:r for r in ref['series'] if r['statut']=='SOURCE_MARCHE_SECONDAIRE'};benchmark=refs.get('URTH',{}).get('observations',{});histories={}
 for r in csv.DictReader((D/'HISTORIQUES_YAHOO_40.csv').open()):
  if r['Date_UTC']<=CUTOFF:histories.setdefault(r['Ticker'],{})[r['Date_UTC']]=float(r['AdjClose'])
 filled=0
 for p in F.glob('*.json'):
  d=json.loads(p.read_text());c=d['blocs']['momentum']['force_relative_indice']
  if c['valeur'] is not None:continue
  prices=histories[d['ticker']];fx=refs.get(d['devise']+'USD=X',{}).get('observations',{}) if d['devise']!='USD' else {day:1 for day in prices};days=sorted(set(prices)&set(benchmark)&set(fx));relative={}
  if days:
   end=days[-1]
   for months in (1,3,6,12):
    earlier=[day for day in days if day<=before(end,months)]
    if not earlier:continue
    start=earlier[-1];relative[str(months)+'m']=dict(debut=start,fin=end,valeur_pct=((prices[end]*fx[end])/(prices[start]*fx[start])/(benchmark[end]/benchmark[start])-1)*100)
  if relative:
   c.clear();c.update(valeur=relative,unite='pct relatif en USD',periode='1/3/6/12 mois disponibles au '+CUTOFF,date_source=DATE,date_collecte=DATE,source_url='DONNEES/HISTORIQUES_YAHOO_40.csv | DONNEES/REFERENCE_RELATIVE_MSCI_WORLD_20261105.json | '+ref['reference_emetteur'],statut='CALCULE_FORCE_RELATIVE_PROXY_MSCI_WORLD',commentaire='Ratio (titre ajusté converti en USD / URTH ajusté) sur chaque fenêtre, moins 1. Ancrages communs titre/ETF/FX; GBp constant annulé dans le ratio. URTH est un proxy ETF avec frais/écart de suivi; horaires de clôture non synchrones. Fenêtres impossibles avant IPO omises, jamais extrapolées.')
   p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n');filled+=1
 print(json.dumps({'references':len(refs),'fiches_completees':filled,'ordres':0}))
if __name__=='__main__':main()

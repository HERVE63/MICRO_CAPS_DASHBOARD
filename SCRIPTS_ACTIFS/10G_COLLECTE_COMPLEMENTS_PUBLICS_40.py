#!/usr/bin/env python3
"""Missing-only public source collection; anonymous sessions never persisted."""
import concurrent.futures,datetime as dt,hashlib,html,http.cookiejar,json,re,urllib.request,urllib.parse
from html.parser import HTMLParser
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'DONNEES';DATE=dt.datetime.now(dt.timezone.utc).date().isoformat();OUT=D/('COMPLEMENTS_PUBLICS_40_'+DATE.replace('-','')+'.json')
CACHE={x['ticker']:x for x in json.loads(OUT.read_text())} if OUT.exists() else {}
class Tables(HTMLParser):
 def __init__(self):super().__init__();self.depth=0;self.cell=False;self.text='';self.row=[];self.rows=[]
 def handle_starttag(self,tag,attrs):
  if tag=='table':self.depth+=1
  if self.depth and tag=='tr':self.row=[]
  if self.depth and tag in ('td','th'):self.cell=True;self.text=''
 def handle_data(self,s):
  if self.cell:self.text+=s
 def handle_endtag(self,tag):
  if self.depth and tag in ('td','th'):self.row.append(re.sub(r'\s+',' ',self.text).strip());self.cell=False
  if self.depth and tag=='tr' and len(self.row)>=2:self.rows.append(self.row)
  if tag=='table':self.depth-=1
jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));opener.addheaders=[('User-Agent','Mozilla/5.0')]
def raw(url,session=False):
 request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
 with (opener.open(request,timeout=25) if session else urllib.request.urlopen(request,timeout=25)) as r:return r.read(),r.status

def collect(d,crumb):
 t=d['ticker'];r={'ticker':t,'date_collecte':DATE}
 if t in CACHE:return CACHE[t]
 targets=[tag for k,tag in [('croissance_ebitda_pct','annualEBITDA'),('croissance_bpa_pct','annualDilutedEPS'),('croissance_fcf_pct','annualFreeCashFlow')] if d['blocs']['croissance'][k]['valeur'] is None and d['blocs']['croissance'][k]['statut']!='NON_APPLICABLE']
 if targets:
  url='https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/'+urllib.parse.quote(t)+'?'+urllib.parse.urlencode({'type':','.join(targets),'period1':1640995200,'period2':int(dt.datetime.now(dt.timezone.utc).timestamp())})
  v={'url':url,'types_demandes':targets}
  try:
   b,status=raw(url);v.update(http=status,sha256_reponse=hashlib.sha256(b).hexdigest(),series=json.loads(b).get('timeseries',{}).get('result'),statut='SOURCE_SECONDAIRE_SERIES_DATEES')
   if any(s.get('meta',{}).get('symbol')!=[t] for s in v['series'] or []):raise ValueError('Identite divergente')
  except Exception as e:v.update(http=getattr(e,'code',None),statut='ECHEC',erreur=type(e).__name__);v.pop('series',None)
  r['series_annuelles']=v
 if d['blocs']['valorisation']['valorisation_historique']['valeur'] is None:
  if '.' not in t:url='https://stockanalysis.com/stocks/'+t.lower()+'/financials/ratios/'
  else:
   code,suffix=t.rsplit('.',1);exchange={'L':'aim','PA':'epa','TO':'tsx','V':'tsxv','ST':'sto','MI':'bit'}[suffix]
   if t=='PLEJD.ST':exchange='xsat'
   url='https://stockanalysis.com/quote/'+exchange+'/'+code+'/financials/ratios/'
  v={'url':url}
  try:
   b,status=raw(url);txt=b.decode();title=html.unescape(re.search('<title>(.*?)</title>',txt,re.S)[1])
   if not re.search(r'\b'+re.escape(t.split('.')[0])+r'\b',title,re.I):raise ValueError('Identite divergente')
   p=Tables();p.feed(txt);seen=set();rows=[]
   for row in p.rows:
    if row[0] in ('Fiscal Year','Period Ending','PE Ratio','P/FCF Ratio','EV / EBITDA','EV / Sales','EV / Revenue') and row[0] not in seen:rows.append(row);seen.add(row[0])
   v.update(http=status,statut='SOURCE_SECONDAIRE_HISTORIQUE',sha256_reponse=hashlib.sha256(b).hexdigest(),lignes=rows)
  except Exception as e:v.update(http=getattr(e,'code',None),statut='ECHEC',erreur=type(e).__name__)
  r['valorisation_historique']=v
 if any(d['blocs']['croissance'][k]['valeur'] is None for k in ('revision_bpa_30j_pct','revision_bpa_90j_pct')):
  endpoint='https://query1.finance.yahoo.com/v10/finance/quoteSummary/'+urllib.parse.quote(t);v={'url':endpoint+'?modules=earningsTrend'}
  try:
   if not crumb:raise RuntimeError('Session publique indisponible')
   b,status=raw(endpoint+'?'+urllib.parse.urlencode({'modules':'earningsTrend','crumb':crumb}),True);j=json.loads(b);result=j.get('quoteSummary',{}).get('result')
   if not result:raise ValueError('Aucun consensus retourne')
   v.update(http=status,statut='SOURCE_SECONDAIRE_CONSENSUS_DATE',sha256_reponse=hashlib.sha256(b).hexdigest(),tendances=result[0].get('earningsTrend',{}).get('trend',[]))
  except Exception as e:v.update(http=getattr(e,'code',None),statut='ECHEC_OU_ABSENCE_CONSENSUS',erreur=type(e).__name__)
  r['revisions']=v
 return r
if __name__=='__main__':
 docs=sorted([json.loads(p.read_text()) for p in (B/'DOSSIERS_MCPA_IPS_40').glob('*.json')],key=lambda d:d['id_position']);assert len(docs)==40
 crumb=None
 try:
  try:opener.open('https://fc.yahoo.com',timeout=15).read()
  except urllib.error.HTTPError:pass
  crumb=opener.open('https://query1.finance.yahoo.com/v1/test/getcrumb',timeout=20).read().decode()
 except Exception:pass
 rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  futures={ex.submit(collect,d,crumb):d['ticker'] for d in docs}
  for f in concurrent.futures.as_completed(futures):
   try:row=f.result()
   except Exception as e:row={'ticker':futures[f],'date_collecte':DATE,'statut':'ERREUR_COLLECTEUR','erreur':type(e).__name__}
   rows.append(row);tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(sorted(rows,key=lambda r:r['ticker']),ensure_ascii=False,indent=2)+'\n');tmp.replace(OUT)
 print(json.dumps({'fiches_traitees':len(rows),'revisions_avec_tendances':sum(bool(r.get('revisions',{}).get('tendances')) for r in rows),'ordres':0}))

#!/usr/bin/env python3
"""Public professional governance/holdings evidence. No completeness claim for insiders."""
import concurrent.futures,datetime as dt,hashlib,http.cookiejar,json,urllib.request,urllib.parse
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'DONNEES';DATE=dt.datetime.now(dt.timezone.utc).date().isoformat();OUT=D/('GOUVERNANCE_PUBLIQUE_40_'+DATE.replace('-','')+'.json');CACHE={r['ticker']:r for r in json.loads(OUT.read_text())} if OUT.exists() else {}
jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));opener.addheaders=[('User-Agent','Mozilla/5.0')]
def collect(pair):
 d,crumb=pair;t=d['ticker']
 if t in CACHE:return CACHE[t]
 endpoint='https://query1.finance.yahoo.com/v10/finance/quoteSummary/'+urllib.parse.quote(t);modules='assetProfile,majorHoldersBreakdown,insiderHolders,insiderTransactions';r=dict(ticker=t,date_collecte=DATE,url=endpoint+'?modules='+modules)
 try:
  with opener.open(endpoint+'?'+urllib.parse.urlencode({'modules':modules,'crumb':crumb}),timeout=25) as response:raw=response.read();r['http']=response.status
  j=json.loads(raw);v=j.get('quoteSummary',{}).get('result')
  if not v:raise ValueError('Aucun profil retourne')
  v=v[0];profile=v.get('assetProfile',{});r['profil']={k:profile[k] for k in ('country','city','industry','sector','website','fullTimeEmployees') if k in profile};r['dirigeants']=[{k:p[k] for k in ('name','title','yearBorn','fiscalYear','totalPay','exercisedValue','unexercisedValue') if k in p} for p in profile.get('companyOfficers',[])]
  if profile.get('longBusinessSummary'):r['sha256_description_activite']=hashlib.sha256(profile['longBusinessSummary'].encode()).hexdigest()
  r['actionnariat']=v.get('majorHoldersBreakdown',{});r['detentions_initiees']=v.get('insiderHolders',{}).get('holders',[]);r['transactions_initiees']=v.get('insiderTransactions',{}).get('transactions',[]);r['sha256_reponse']=hashlib.sha256(raw).hexdigest();r['statut']='SOURCE_SECONDAIRE_GOUVERNANCE_NON_RAPPROCHEE';r['limite']='Initiés fournisseur ≠ dirigeants stricts; transactions potentiellement partielles, jamais total net exhaustif par défaut. Options et attributions distinctes des achats au comptant.'
 except Exception as e:r.update(statut='ECHEC_ACCES_OU_ABSENCE',http=getattr(e,'code',r.get('http')),erreur=type(e).__name__)
 return r
if __name__=='__main__':
 docs=sorted([json.loads(p.read_text()) for p in (B/'DOSSIERS_MCPA_IPS_40').glob('*.json')],key=lambda d:d['id_position']);assert len(docs)==40
 try:
  try:opener.open('https://fc.yahoo.com',timeout=15).read()
  except urllib.error.HTTPError:pass
  crumb=opener.open('https://query1.finance.yahoo.com/v1/test/getcrumb',timeout=20).read().decode()
  rows=[]
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
   for r in ex.map(collect,[(d,crumb) for d in docs]):
    rows.append(r);tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');tmp.replace(OUT)
 except Exception as e:raise RuntimeError('Session publique indisponible: '+type(e).__name__) from None
 print(json.dumps({'fiches':len(rows),'profils':sum(bool(r.get('profil')) for r in rows),'detentions':sum(bool(r.get('detentions_initiees')) for r in rows),'ordres':0}))

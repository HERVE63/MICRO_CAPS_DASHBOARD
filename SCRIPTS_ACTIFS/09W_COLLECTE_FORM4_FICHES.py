#!/usr/bin/env python3
"""Aggregate SEC Form 4 P/S trades; amendments/incomplete windows block totals."""
import concurrent.futures,datetime as dt,hashlib,json,sys,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];D=BASE/'AUDITS/FINALISATION_FICHES_20261104/SEC'
ASOF=dt.date(2026,11,4);START=(ASOF-dt.timedelta(days=180)).isoformat()
def issuer(p):
 s=json.loads(p.read_text());t=p.name.split('_')[0];cik=int(s['cik']);recent=s['filings']['recent'];forms=[];errors=[]
 dates=recent.get('filingDate',[]);covers=bool(dates) and min(dates)<=START
 for i,f in enumerate(recent.get('form',[])):
  if f not in ('4','4/A') or not START<=dates[i]<=ASOF.isoformat():continue
  accession=recent['accessionNumber'][i];doc=recent['primaryDocument'][i].split('/')[-1]
  url=f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace("-","")}/{doc}'
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Microcaps public research research@example.com'})
   with urllib.request.urlopen(req,timeout=15) as r:raw=r.read()
   root=ET.fromstring(raw);trades=[]
   # Issuer CIK must agree with the submissions identity already checked.
   if int(root.findtext('issuer/issuerCik') or 0)!=cik:raise ValueError('CIK XML divergent')
   for tr in root.findall('.//nonDerivativeTransaction'):
    code=tr.findtext('transactionCoding/transactionCode');date=(tr.findtext('transactionDate/value') or '')[:10]
    if code not in ('P','S') or not date or not START<=date<=ASOF.isoformat():continue
    n=tr.findtext('transactionAmounts/transactionShares/value');price=tr.findtext('transactionAmounts/transactionPricePerShare/value')
    trades.append({'date':date,'code':code,'titres':float(n) if n else None,'prix_USD':float(price) if price else None})
   forms.append({'form':f,'date_depot':dates[i],'accession':accession,'url':url,'sha256_xml':hashlib.sha256(raw).hexdigest(),'transactions_PS':trades})
  except Exception as e:errors.append({'url':url,'date_depot':dates[i],'erreur':type(e).__name__,'http':getattr(e,'code',None)})
 out={'ticker':t,'date_collecte':ASOF.isoformat(),'debut_fenetre_180j':START,'couverture_depots_180j':covers,'formulaires':forms,'erreurs':errors,'totaux':{}}
 return aggregate(out)
def aggregate(out):
 forms=out['formulaires'];errors=out['erreurs'];covers=out['couverture_depots_180j']
 for days in (90,180):
  start=(ASOF-dt.timedelta(days=days)).isoformat()
  transactions=[dict(tr,date=tr['date'][:10]) for f in forms for tr in f['transactions_PS'] if start<=tr['date'][:10]<=ASOF.isoformat()]
  # A filing already submitted before the window cannot report a later trade.
  # Thus unresolved June amendments block 180d, but not the August-November window.
  blocked=not covers or any(e.get('date_depot','9999')>=start for e in errors) or any(f['form']=='4/A' and f['date_depot']>=start for f in forms)
  incomplete=any(tr['titres'] is None or tr['prix_USD'] is None for tr in transactions)
  out['totaux'][str(days)]={'valeur':None if blocked or incomplete else sum((1 if tr['code']=='P' else -1)*tr['titres']*tr['prix_USD'] for tr in transactions),'unite':'USD','nombre_transactions':len(transactions),'statut':'INCOMPLET' if blocked or incomplete else 'DEPOTS_SEC_FENETRE_CONTROLEE'}
 return out
def main():
 if '--reaggregate' in sys.argv:
  rows=json.loads((D/'INITIES_5_US.json').read_text())
  for row in rows:
   s=json.loads((D/(row['ticker']+'_submissions.json')).read_text())['filings']['recent']
   for error in row['erreurs']:
    for i,accession in enumerate(s['accessionNumber']):
     if '/'+accession.replace('-','')+'/' in error['url']:error['date_depot']=s['filingDate'][i]
   aggregate(row)
  (D/'INITIES_5_US.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n');print('Reaggregated existing filings by exact window');return
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:rows=list(ex.map(issuer,sorted(D.glob('*_submissions.json'))))
 (D/'INITIES_5_US.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps([{'ticker':r['ticker'],'formulaires':len(r['formulaires']),'erreurs':len(r['erreurs']),'totaux':r['totaux']} for r in rows]))
if __name__=='__main__':main()

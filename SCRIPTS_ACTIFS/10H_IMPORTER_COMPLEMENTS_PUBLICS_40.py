#!/usr/bin/env python3
"""Import dated evidence into empty fields only. Never assigns financial scores."""
import csv,datetime as dt,json,math,re
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'DONNEES';F=B/'DOSSIERS_MCPA_IPS_40'
def load(p):return json.loads(p.read_text())
def num(v):
 if isinstance(v,dict):v=v.get('raw')
 if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v):return v
 if isinstance(v,str):
  try:return float(v.replace(',','').replace('%',''))
  except ValueError:pass
 return None
def cell(value,unit,period,date,url,status,comment):return dict(valeur=value,unite=unit,periode=period,date_source=date,source_url=url,statut=status,commentaire=comment,date_collecte=date)
def put(d,b,k,v,u,p,r,comment,status='SOURCE_SECONDAIRE_DATEE_A_RAPPROCHER'):
 c=d['blocs'][b][k]
 if c['valeur'] is not None:return
 c.clear();c.update(cell(v,u,p,r['date_collecte'],r['url'],status,comment))
 if v is None:c['recherche']={'date':r['date_collecte'],'statut':status,'motif':comment,'journal':'journal_recherches'}
def main():
 files=sorted(D.glob('COMPLEMENTS_PUBLICS_40_*.json'))
 if not files:return
 observations={}
 for file in files:
  for r in load(file):observations[r['ticker']]=r
 annual={r['ticker']:r for r in load(D/'IDENTITES_CROISSANCE_40_20261104.json')}
 report=[];matrix=[]
 for path in sorted(F.glob('*.json')):
  d=load(path);r=observations.get(d['ticker'])
  if not r:continue
  date=r['date_collecte'];ar=annual[d['ticker']].get('annuel',{});rows={r[0]:r[1:] for r in ar.get('lignes',[])};hh=rows.get('Fiscal Year',[]);ee=rows.get('Period Ending',[]);expected=None
  for i,h in enumerate(hh):
   if re.fullmatch('FY ?20[0-9][0-9]',h) and i<len(ee):
    m=re.search(r'([A-Za-z]{3} \d{1,2}, 20\d{2})',ee[i])
    if m:expected=dt.datetime.strptime(m[1],'%b %d, %Y').date().isoformat()
    break
  sr=r.get('series_annuelles',{})
  for s in sr.get('series') or []:
   tag=next(iter(s.get('meta',{}).get('type',[])),None);key={'annualEBITDA':'croissance_ebitda_pct','annualDilutedEPS':'croissance_bpa_pct','annualFreeCashFlow':'croissance_fcf_pct'}.get(tag)
   if not key or not expected:continue
   points=sorted([v for v in s.get(tag,[]) if v.get('asOfDate','')<=expected and v.get('periodType')=='12M'],key=lambda v:v['asOfDate'],reverse=True)
   if len(points)<2 or points[0]['asOfDate']!=expected:continue
   a,b=points[:2]
   if int(a['asOfDate'][:4])-int(b['asOfDate'][:4])!=1 or a.get('currencyCode')!=b.get('currencyCode'):continue
   av,bv=num(a.get('reportedValue')),num(b.get('reportedValue'))
   if av is None or bv is None:continue
   pr=dict(sr,date_collecte=date);period=b['asOfDate']+' / '+a['asOfDate']
   if bv>0:put(d,'croissance',key,(av/bv-1)*100,'pct',period,pr,'Yahoo '+tag+'; devise commune '+str(a.get('currencyCode'))+'. Arrêté aligné sur dernier exercice connu; source secondaire non rapprochée.')
   else:put(d,'croissance',key,None,'sans objet',period,pr,'Base annuelle '+tag+' non positive; pas de pourcentage interprétable selon cette convention. Comparer montants et signes.','NON_APPLICABLE')
  vr=r.get('valorisation_historique',{});vv={v[0]:v[1:] for v in vr.get('lignes',[])};hh=vv.get('Fiscal Year',[]);ee=vv.get('Period Ending',[]);history=[]
  for i,h in enumerate(hh):
   if not re.fullmatch('FY ?20[0-9][0-9]',h):continue
   # IEVA IPO in 2026: annual pre-IPO multiples are not market observations.
   if d['ticker']=='ALIEV.PA' and int(h[-4:])<2026:continue
   row={'exercice':h,'arrete':ee[i] if i<len(ee) else h,'ratios':{}}
   for label in ('PE Ratio','P/FCF Ratio','EV / EBITDA','EV / Sales','EV / Revenue'):
    vals=vv.get(label,[]);v=num(vals[i]) if i<len(vals) else None
    if v is not None:row['ratios'][label]=v
   if row['ratios']:history.append(row)
  if history:put(d,'valorisation','valorisation_historique',history,'multiples historiques','clôtures annuelles, hors Current',dict(vr,date_collecte=date),'Multiples de clôtures annuelles fournisseur, pas juste valeur ni moyenne sectorielle. n/a omis sans conversion en zéro; retraitements à rapprocher.')
  rr=r.get('revisions',{});trends=sorted([x for x in rr.get('tendances',[]) if x.get('period') in ('0y','+1y') and isinstance(x.get('endDate'),str) and x['endDate']>=date],key=lambda x:x['endDate'])
  if trends:
   t=trends[0];eps=t.get('epsTrend',{});current=num(eps.get('current'));period='consensus annuel clos au '+t['endDate'];pr=dict(rr,date_collecte=date);count=num(t.get('earningsEstimate',{}).get('numberOfAnalysts'));currency=eps.get('epsTrendCurrency') or t.get('earningsEstimate',{}).get('earningsCurrency')
   for days in (30,90):
    old=num(eps.get(str(days)+'daysAgo'));key='revision_bpa_'+str(days)+'j_pct'
    if current is None or old is None or count==0:continue
    comment='Consensus Yahoo pour un même exercice : BPA actuel '+str(current)+', BPA à J-'+str(days)+' '+str(old)+', devise '+str(currency)+'. Variation (actuel/antérieur -1). Pas une révision d’objectif de cours; instantanés de consensus secondaires à rapprocher.'
    if old>0:put(d,'croissance',key,(current/old-1)*100,'pct',period,pr,comment)
    else:put(d,'croissance',key,None,'sans objet',period,pr,comment+' Base antérieure non positive : pourcentage non interprétable selon cette convention.','NON_APPLICABLE')
   obs=dict(bloc='croissance',champ='instantanes_consensus_bpa',**cell({'exercice':t['endDate'],'courant':current,'J_30':num(eps.get('30daysAgo')),'J_90':num(eps.get('90daysAgo')),'nombre_analystes':count},str(currency)+'/action',period,date,rr.get('url'),'SOURCE_SECONDAIRE_CONSENSUS_DATE','BPA généralement ajusté; identité demandée par ticker dans URL API, pas validation primaire.'))
   if obs not in d['observations_complementaires']:d['observations_complementaires'].append(obs)
  for family,v in r.items():
   if not isinstance(v,dict):continue
   log={'famille':'complement_public_'+family,'date':date,'url':v.get('url'),'http':v.get('http'),'statut':v.get('statut'),'limite':'Échec ou champ absent ne prouve pas une indisponibilité définitive.'}
   if log not in d['journal_recherches']:d['journal_recherches'].append(log)
  counts={'RENSEIGNE':0,'NON_APPLICABLE':0,'INDISPONIBLE_A_DATE':0,'RECHERCHE_A_POURSUIVRE':0};missing=[]
  for b,bl in d['blocs'].items():
   for k,c in bl.items():
    if c['valeur'] is not None:status='RENSEIGNE';c.pop('recherche',None)
    elif c['statut']=='NON_APPLICABLE':status='NON_APPLICABLE';c['recherche']={'date':c['date_collecte'],'statut':'NON_APPLICABLE','motif':c['commentaire'],'journal':'journal_recherches'}
    elif c['statut'].startswith('INDISPONIBLE_A_DATE'):status='INDISPONIBLE_A_DATE'
    else:status='RECHERCHE_A_POURSUIVRE';missing.append(b+'.'+k)
    counts[status]+=1;matrix.append(dict(ticker=d['ticker'],bloc=b,champ=k,statut=status,motif=c.get('commentaire') or c.get('recherche',{}).get('motif'),source=c.get('source_url')))
  d['audit_poursuite'].update(date=date,comptage=counts,couverture_valeurs_pct=round(counts['RENSEIGNE']/108*100,2),couverture_applicable_pct=round(counts['RENSEIGNE']/(108-counts['NON_APPLICABLE'])*100,2),recherches_non_closes=missing)
  d['audit_couverture'].update(date=date,champs_renseignes=counts['RENSEIGNE'],couverture_pct=round(counts['RENSEIGNE']/108*100,2),champs_manquants=[b+'.'+k for b,bl in d['blocs'].items() for k,c in bl.items() if c['valeur'] is None])
  path.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n');report.append(dict(Ticker=d['ticker'],Societe=d['societe'],**counts,Couverture_valeurs_pct=d['audit_poursuite']['couverture_valeurs_pct'],Validation=d['audit_poursuite']['validation_individuelle']))
 if len(report)!=40:raise RuntimeError('Couverture source incomplète : '+str(len(report)))
 with (D/'COUVERTURE_POURSUITE_40_20261105.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=report[0].keys());w.writeheader();w.writerows(report)
 (D/'MATRICE_CHAMPS_POURSUITE_40_20261105.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:sum(r[k] for r in report) for k in counts}))
if __name__=='__main__':main()

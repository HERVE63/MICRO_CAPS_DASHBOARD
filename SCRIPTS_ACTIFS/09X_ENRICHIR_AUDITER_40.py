#!/usr/bin/env python3
"""Evidence-only enrichment of all forty dossiers. Original populated cells immutable.
Secondary observations are labelled unreconciled and never authorize arbitration.
"""
import calendar,csv,datetime as dt,hashlib,json,math,re,statistics,subprocess,unicodedata
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];D=BASE/'DONNEES';F=BASE/'DOSSIERS_MCPA_IPS_40'
DATE='2026-11-04';PRICE_CUTOFF='2026-11-03'
BASELINE_COMMIT='076ba2accecd4bc0b161ecb9d5c020e0a08f7533'
PROTECTED={}
for _path in sorted(F.glob('*.json')):
 _original=json.loads(subprocess.check_output(['git','show',BASELINE_COMMIT+':'+str(_path.relative_to(BASE))],cwd=BASE,text=True))
 PROTECTED[_original['ticker']]={(b,k) for b,block in _original['blocs'].items() for k,c in block.items() if c['valeur'] is not None}
def load(p):return json.loads(p.read_text())
def cell(value,unit,period,date,url,status,comment=None):
 return dict(valeur=value,unite=unit,periode=period,date_source=date,source_url=url,statut=status,commentaire=comment,date_collecte=DATE)
def put(doc,block,key,c):
 if key not in doc['blocs'][block]:
  obs=dict(bloc=block,champ=key,**c)
  if obs not in doc['observations_complementaires']:doc['observations_complementaires'].append(obs)
  return False
 target=doc['blocs'][block][key]
 if target['valeur'] is None:
  target.update(c);target.pop('recherche',None);return True
 if (block,key) not in PROTECTED.get(doc['ticker'],set()) and target.get('statut')==c.get('statut') and (target.get('valeur')!=c.get('valeur') or target.get('periode')!=c.get('periode')):
  old=dict(bloc=block,champ=key,**target)
  if old not in doc['observations_complementaires']:doc['observations_complementaires'].append(old)
  target.clear();target.update(c);return True
 if target.get('statut','').startswith('SOURCE_SECONDAIRE') and c.get('statut','').startswith('SOURCE_PRIMAIRE'):
  old=dict(bloc=block,champ=key,**target)
  if old not in doc['observations_complementaires']:doc['observations_complementaires'].append(old)
  target.clear();target.update(c);return True
 if target['valeur']!=c['valeur'] or target.get('periode')!=c.get('periode'):
  obs=dict(bloc=block,champ=key,**c)
  if obs not in doc['observations_complementaires']:doc['observations_complementaires'].append(obs)
 return False
def number(s):
 if not s or s.lower() in ('n/a','-','upgrade'):return None
 s=s.replace(',','').replace('$','').replace('%','').replace('+','').strip()
 m=re.fullmatch(r'(-?\d+(?:\.\d+)?)([KMBT]?)',s)
 return float(m[1])*{'':1,'K':1e3,'M':1e6,'B':1e9,'T':1e12}[m[2]] if m else None
def norm(s):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def month_before(date,months):
 d=dt.date.fromisoformat(date);m=d.year*12+d.month-1-months;y,m=divmod(m,12);m+=1
 return dt.date(y,m,min(d.day,calendar.monthrange(y,m)[1])).isoformat()
def market(doc,rows):
 rows=sorted([r for r in rows if r['Date_UTC']<=PRICE_CUTOFF],key=lambda r:r['Date_UTC'])
 # Repeated conflicting prices are quarantined, not chosen by max/min price.
 unique={}
 for r in rows:
  date=r['Date_UTC']
  if date in unique and any(unique[date][k]!=r[k] for k in ('Close','AdjClose','Volume')):raise ValueError('Conflicting prices '+doc['ticker'])
  unique[date]=r
 rows=list(unique.values());prices=[float(r['AdjClose']) for r in rows];last=rows[-1];date=last['Date_UTC'];url=last['Source']
 # London raw Yahoo prices are GBp; only raw quote is converted to GBP.
 scale=.01 if doc['ticker'].endswith('.L') else 1
 def putm(k,v,unit,period,comment):put(doc,'momentum',k,cell(v,unit,period,date,url,'CALCULE_HISTORIQUE_SECONDAIRE',comment))
 put(doc,'valorisation','cours',cell(float(last['Close'])*scale,doc['devise'],'cloture '+date,date,url,'SOURCE_MARCHE','Cours non ajuste; GBp/100 pour Londres.'))
 put(doc,'valorisation','date_cours',cell(date,'date','cloture',date,url,'SOURCE_MARCHE'))
 for months in (1,3,6,12):
  target=month_before(date,months);old=[r for r in rows if r['Date_UTC']<=target]
  if old:putm(f'momentum_{months}m_pct',(prices[-1]/float(old[-1]['AdjClose'])-1)*100,'pct',old[-1]['Date_UTC']+' / '+date,'Cours ajustés, ancrage calendaire; dernière séance <= date cible.')
 a=[r for r in rows if r['Date_UTC']<=month_before(date,1)];b=[r for r in rows if r['Date_UTC']<=month_before(date,6)]
 if a and b:putm('momentum_6_1_pct',(float(a[-1]['AdjClose'])/float(b[-1]['AdjClose'])-1)*100,'pct',b[-1]['Date_UTC']+' / '+a[-1]['Date_UTC'],'Momentum 6–1 : prix à -1 mois / prix à -6 mois - 1; aucune modification de la règle de sélection.')
 if len(prices)>=200:
  ma=statistics.mean(prices[-200:]);putm('prix_vers_mm200',prices[-1]/ma,'ratio','200 dernières séances','Cours ajusté / moyenne mobile 200 séances.')
  if len(prices)>=220:
   prev=statistics.mean(prices[-220:-20]);putm('tendance_mm200',(ma/prev-1)*100,'pct','variation MM200 sur 20 séances','Pente approchée par variation MM200(t)/MM200(t-20)-1; niveau MM200 non confondu avec pente.')
 vols=[float(r['Volume']) for r in rows[-20:]]
 if len(vols)==20:
  av=statistics.mean(vols);putm('volume_moyen_20j',av,'titres','20 dernières séances','Moyenne arithmétique des volumes Yahoo non ajustés.')
  if av>0:putm('ratio_volume',vols[-1]/av,'ratio','dernière séance / moyenne 20 séances','Ratio de volume de la dernière séance.')
 if len(prices)>=91:
  ret=[math.log(prices[i]/prices[i-1]) for i in range(len(prices)-90,len(prices))];putm('volatilite_90j_pct',statistics.stdev(ret)*math.sqrt(252)*100,'pct','90 rendements quotidiens','Écart-type échantillon des log-rendements ajustés annualisé sqrt(252).')
 start=month_before(date,12);window=[r for r in rows if r['Date_UTC']>=start]
 if rows[0]['Date_UTC']<=start:
  peak=0;dd=0
  for r in window:price=float(r['AdjClose']);peak=max(peak,price);dd=min(dd,price/peak-1)
  putm('drawdown_12m_pct',dd*100,'pct',start+' / '+date,'Maximum drawdown du prix ajusté sur la fenêtre, valeur négative.')
 if doc['ticker']=='ALIEV.PA':
  doc['anomalies'].append('HISTORIQUE_COURT_IPO: MM200 et momentum12m non calculables avec les données archivées.') if 'HISTORIQUE_COURT_IPO: MM200 et momentum12m non calculables avec les données archivées.' not in doc['anomalies'] else None
def secondary(doc,r):
 if r.get('statut')!='SOURCE_SECONDAIRE_A_RAPPROCHER':return
 url=r['url'];currency=r.get('devise_comptes_fournisseur');m=r['mesures']
 status='SOURCE_SECONDAIRE_NON_RAPPROCHEE'
 period='TTM affiché au '+DATE+'; date exacte de fin non fournie sur la page statistiques'
 balance='Dernier bilan affiché au '+DATE+'; date comptable exacte à rapprocher'
 mapping={
 'Market Cap':('valorisation','capitalisation',doc['devise'],'cotation au '+DATE),
 'Enterprise Value':('valorisation','valeur_entreprise',doc['devise'],'valorisation affichée au '+DATE),
 'PE Ratio':('valorisation','pe','ratio',period),'PB Ratio':('valorisation','p_b','ratio',balance),
 'P/FCF Ratio':('valorisation','p_fcf','ratio',period),'PEG Ratio':('croissance','peg','ratio','prévision fournisseur, horizon non explicité'),
 'EV / Sales':('valorisation','ev_ca','ratio',period),'EV / EBITDA':('valorisation','ev_ebitda','ratio',period),'EV / EBIT':('valorisation','ev_ebit','ratio',period),
 'Current Ratio':('risque','liquidite_courante','ratio',balance),'Interest Coverage':('risque','couverture_interets','ratio',period),
 'Return on Equity (ROE)':('qualite','roe_pct','pct',period),'Return on Invested Capital (ROIC)':('qualite','roic_pct','pct',period),
 'Revenue':('qualite','ca_ttm',currency,period),'Free Cash Flow':('qualite','fcf_ttm',currency,period),
 'Cash & Cash Equivalents':('risque','cash',currency,balance),'Total Debt':('risque','dette_brute',currency,balance),
 'Gross Margin':('qualite','marge_brute_pct','pct',period),'Operating Margin':('qualite','marge_ebit_pct','pct',period),'Profit Margin':('qualite','marge_nette_pct','pct',period),'EBITDA Margin':('qualite','marge_ebitda_pct','pct',period),
 'FCF Yield':('valorisation','rendement_fcf_pct','pct',period),'Owned by Insiders (%)':('identite','actionnariat_dirigeants_pct','pct','détentions déclarées, dates hétérogènes du fournisseur')}
 for label,(block,key,unit,p) in mapping.items():
  value=number(m.get(label))
  if value is None or unit is None:continue
  # Suspicious provider classifications are retained separately, never silently imported.
  if label=='Gross Margin' and doc['ticker'] in ('AL2SI.PA','ALBFR.PA','GENI.ST'):
   doc['observations_complementaires'].append(dict(bloc=block,champ=key,**cell(value,unit,p,DATE,url,'ANOMALIE_CLASSIFICATION_FOURNISSEUR','Marge brute fournisseur incompatible ou non comparable avec présentation primaire; pas d’import dans le champ.')));continue
  put(doc,block,key,cell(value,unit,p,DATE,url,status,'Donnée de fournisseur secondaire; ni certification des comptes ni validation MCPA. Arrêté précis à rapprocher.'))
 shares=number(m.get('Shares Outstanding'));free=number(m.get('Float'))
 if shares and free is not None and 0<=free<=shares:put(doc,'identite','flottant_pct',cell(free/shares*100,'pct','flottant/actions fournisseur au '+DATE,DATE,url,status,'Calcul sur nombres arrondis; détenu par initiés ≠ total dirigeants strict.'))
 cash=number(m.get('Net Cash'))
 if cash is not None and currency:put(doc,'risque','dette_nette',cell(-cash,currency,balance,DATE,url,status,'Dette nette = - Net Cash du fournisseur; périmètre dette/locations à rapprocher.'))
 debt=number(m.get('Total Debt'));cash2=number(m.get('Cash & Cash Equivalents'));ebitda=number(m.get('EBITDA'));fcf=number(m.get('Free Cash Flow'));net=number(m.get('Net Income'))
 if debt is not None and cash2 is not None and ebitda and ebitda>0:put(doc,'risque','dette_nette_ebitda',cell((debt-cash2)/ebitda,'ratio',period,DATE,url,status,'(Total Debt - Cash)/EBITDA, tous issus du même fournisseur; dates exactes à rapprocher.'))
 if net and net>0 and fcf is not None:put(doc,'qualite','conversion_fcf_pct',cell(fcf/net*100,'pct',period,DATE,url,status,'Convention explicitée : FCF/résultat net; pas de calcul si résultat net <=0.'))
 # Earnings dates marked by a secondary provider are estimates until issuer confirmation.
 if m.get('Earnings Date') not in (None,'n/a'):doc['observations_complementaires'].append(dict(bloc='croissance',champ='catalyseurs_dates',**cell(m['Earnings Date'],'date fournisseur','publication mentionnée par le fournisseur; vérifier si passée ou future',DATE,url,'CALENDRIER_SECONDAIRE_A_CONFIRMER','Ne remplace pas un calendrier officiel.')))
 change=number(m.get('Shares Change (YoY)'))
 if change is not None:put(doc,'risque','risque_dilution',cell('Variation annuelle des actions en circulation fournisseur : '+str(change)+' %. Ne mesure pas les instruments potentiellement dilutifs.','texte','YoY fournisseur au '+DATE,DATE,url,status,'Indicateur réalisé, non prévision de dilution.'))
 if doc['devise']!='EUR':put(doc,'risque','risque_change',cell('Conversion de la cotation '+doc['devise']+' vers EUR pour le portefeuille virtuel; exposition opérationnelle et couverture de change non documentées.','texte','cotation au '+DATE,DATE,url,'ANALYSE_DEVISE_COTATION','Risque de conversion identifié; aucune hypothèse de couverture opérationnelle.'))
 if fcf is not None and fcf<0 and cash2 is not None and cash2>=0 and currency:put(doc,'risque','cash_runway_mois',cell(cash2/(-fcf/12),'mois','cash dernier bilan / consommation FCF TTM',DATE,url,status,'Extrapolation mécanique : cash/(-FCF_TTM/12), sans financement futur; pas une prévision de liquidité ni un avis sur continuité.'))
def profile_growth(doc,r):
 profile=r.get('profil',{});url=profile.get('url');p=dict((a[0],a[1]) for a in profile.get('lignes',[]) if len(a)>1)
 if profile.get('statut')=='SOURCE_SECONDAIRE_A_RAPPROCHER':
  for label,key in [('Country','pays'),('Industry','industrie'),('Sector','secteur'),('Exchange','place_cotation'),('ISIN Number','isin')]:
   val=p.get(label)
   if val and val!='n/a':put(doc,'identite',key,cell(val,'identifiant' if key=='isin' else 'texte','profil émetteur au '+DATE,DATE,url,'SOURCE_SECONDAIRE_NON_RAPPROCHEE','Profil de la cotation exacte; identité à corroborer avec une source réglementaire.'))
  if p.get('Sector'):put(doc,'diversification','exposition_sectorielle',cell(p['Sector'],'classification fournisseur','profil au '+DATE,DATE,url,'SOURCE_SECONDAIRE_NON_RAPPROCHEE','Secteur de l’émetteur; ne représente pas la répartition de son CA par secteur.'))
 # Annual tables may contain a leading TTM column: identify FY columns by header.
 annual=r.get('annuel',{});rows=annual.get('lignes',[]);a={row[0]:row[1:] for row in rows}
 endings0=next((row[1:] for row in rows if row[0]=='Period Ending'),[])
 if endings0:
  # Explicitly record the same provider's statement period; do not claim primary reconciliation.
  for block in doc['blocs'].values():
   for c in block.values():
    if c.get('statut')=='SOURCE_SECONDAIRE_NON_RAPPROCHEE' and 'date exacte de fin non fournie' in str(c.get('periode')):
     c['periode']='TTM fournisseur; arrêté indiqué dans son tableau financier : '+endings0[0]
     c['commentaire']=(c.get('commentaire') or '')+' Date rapprochée au tableau financier du même fournisseur, sans certification primaire.'
 headers=next((row[1:] for row in rows if 'Fiscal Year' in row[0]),[])
 indices=[i for i,h in enumerate(headers) if re.fullmatch(r'FY ?20\d\d',h)]
 if not indices:return
 i=indices[0];fy=headers[i];endings=next((row[1:] for row in rows if 'Period Ending' in row[0]),[]);period=(endings[i] if i<len(endings) else fy)
 rev=a.get('Revenue',[]);eps=a.get('EPS (Diluted)',[]);ebitda=a.get('EBITDA',[])
 def val(series,j):return number(series[j]) if j<len(series) else None
 for key,series in [('croissance_ca_1a_pct',rev),('croissance_bpa_pct',eps),('croissance_ebitda_pct',ebitda)]:
  if len(indices)<2:continue
  j=indices[1];cur=val(series,i);old=val(series,j)
  direct=val(a.get('EPS Growth' if key=='croissance_bpa_pct' else 'Revenue Growth',[]),i) if key!='croissance_ebitda_pct' else None
  if cur is not None and old is not None and old>0 and (key!='croissance_bpa_pct' or cur>=0):put(doc,'croissance',key,cell(direct if direct is not None else (cur/old-1)*100,'pct',fy+' / '+headers[j]+'; clôture '+period,DATE,annual['url'],'SOURCE_SECONDAIRE_NON_RAPPROCHEE','Croissance publiée par le fournisseur si disponible; sinon calcul sur montants annuels arrondis, dénominateur positif.'))
 fcf=a.get('Free Cash Flow',[])
 if len(indices)>=2:
  j=indices[1];cur=val(fcf,i);old=val(fcf,j)
  if cur is not None and old is not None and old>0:put(doc,'croissance','croissance_fcf_pct',cell((cur/old-1)*100,'pct',fy+' / '+headers[j],DATE,annual['url'],'SOURCE_SECONDAIRE_NON_RAPPROCHEE','FCF annuel fournisseur, montants arrondis; pas de pourcentage si base <=0.'))
 if len(indices)>=4:
  j=indices[3];cur=val(rev,i);old=val(rev,j)
  years=int(headers[i][-4:])-int(headers[j][-4:])
  if cur and cur>0 and old and old>0 and years==3:put(doc,'croissance','croissance_ca_3a_cagr_pct',cell(((cur/old)**(1/3)-1)*100,'pct',headers[j]+' / '+fy,DATE,annual['url'],'SOURCE_SECONDAIRE_NON_RAPPROCHEE','CAGR annuel sur trois ans; pas de confusion avec prévision de croissance.'))
def euro_metrics(doc,stats,history,fx):
 rate=fx['taux'][doc['devise']];cap=number(stats.get('mesures',{}).get('Market Cap'))
 if cap is not None:put(doc,'identite','capitalisation_eur',cell(cap/rate,'EUR','capitalisation fournisseur et référence BCE du '+DATE,DATE,stats['url']+' | '+fx['source_url'],'SOURCE_SECONDAIRE_NON_RAPPROCHEE','Capitalisation en devise de cotation / unités de cette devise pour 1 EUR; montant fournisseur arrondi.'))
 rows=sorted([r for r in history if r['Date_UTC']<=PRICE_CUTOFF],key=lambda r:r['Date_UTC'])[-20:]
 if len(rows)==20:
  scale=.01 if doc['ticker'].endswith('.L') else 1
  liquidity=statistics.mean(float(r['Close'])*scale*float(r['Volume']) for r in rows)/rate
  put(doc,'identite','liquidite_moyenne_eur_20j',cell(liquidity,'EUR/jour',rows[0]['Date_UTC']+' / '+rows[-1]['Date_UTC'],DATE,rows[-1]['Source']+' | '+fx['source_url'],'ESTIMATION_PROXY_LIQUIDITE','Moyenne(clôture non ajustée × volume) sur 20 séances, convertie au seul FX BCE du 04/11/2026; proxy de liquidité, pas volumes réellement négociés en EUR à chaque date. GBp/100 à Londres.'))
def forecasts(doc,r):
 if r.get('statut')!='SOURCE_SECONDAIRE_PREVISIONS':return
 rows={a[0]:a[1:] for a in r.get('lignes',[])};ends=rows.get('Period Ending',[])
 currency=r.get('devise_previsions')
 if currency is None and doc['ticker'] in ('IDN','INFU','OSS','CXDO','LWAY'):currency='USD'
 for i,end in enumerate(ends):
  try:date=dt.datetime.strptime(end,'%b %d, %Y').date().isoformat()
  except ValueError:continue
  if date<DATE:continue
  for label,key in [('Revenue','previsions_ca_1a'),('EPS','previsions_bpa_1a')]:
   series=rows.get(label,[]);v=number(series[i]) if i<len(series) else None
   if v is not None and currency:put(doc,'croissance',key,cell(v,currency+('/action' if label=='EPS' else ''),'exercice annuel prévisionnel clos au '+date,DATE,r['url'],'SOURCE_SECONDAIRE_PREVISION_NON_RAPPROCHEE','Premier exercice futur affiché; consensus et non engagement de direction. BPA non-GAAP ajusté selon le fournisseur; ne pas comparer directement au BPA comptable. Devise USD pour les cinq émetteurs domestiques US, devise financière explicitée pour les autres.'))
  # Only the nearest future fiscal year matches this annual forecast field.
  break
def sec(doc):
 p=BASE/f"AUDITS/FINALISATION_FICHES_20261104/SEC/{doc['ticker']}_companyfacts.json"
 extracted=p.with_name(doc['ticker']+'_companyfacts_extrait.json')
 if extracted.exists():p=extracted
 sub=p.with_name(doc['ticker']+'_submissions.json')
 if not p.exists() or not sub.exists():return
 data=load(p);identity=load(sub)
 if doc['ticker'] not in identity.get('tickers',[]) or int(data['cik'])!=int(identity['cik']):raise ValueError('SEC identity mismatch')
 cik=str(identity['cik']).zfill(10);url=f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json';status='CALCULE_SOURCE_SEC'
 put(doc,'identite','pays',cell('États-Unis','texte','identité SEC au '+DATE,DATE,'https://data.sec.gov/submissions/CIK'+cik+'.json','SOURCE_SEC_IDENTITE','Émetteur domestique SEC; siège à contrôler dans adresses.'))
 if identity.get('sicDescription'):put(doc,'identite','industrie',cell(identity['sicDescription'],'classification SIC','identité SEC au '+DATE,DATE,'https://data.sec.gov/submissions/CIK'+cik+'.json','SOURCE_SEC_IDENTITE'))
 if identity.get('exchanges'):put(doc,'identite','place_cotation',cell(identity['exchanges'][0],'texte','identité SEC au '+DATE,DATE,'https://data.sec.gov/submissions/CIK'+cik+'.json','SOURCE_SEC_IDENTITE'))
 facts=data['facts']['us-gaap']
 def exact(tags,start,end,unit='USD'):
  for tag in tags:
   items=[x for x in facts.get(tag,{}).get('units',{}).get(unit,[]) if x.get('start')==start and x.get('end')==end and x.get('filed','9999')<=DATE and x.get('form') in ('10-Q','10-K','10-Q/A','10-K/A')]
   if items:
    date=max(x['filed'] for x in items);vals={x['val'] for x in items if x['filed']==date}
    if len(vals)==1:return next(iter(vals))
  return None
 tags={
 'revenue':['RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet'],
 'net':['NetIncomeLoss'],'ebit':['OperatingIncomeLoss'],'gross':['GrossProfit'],
 'cfo':['NetCashProvidedByUsedInOperatingActivities'],'capex':['PaymentsToAcquirePropertyPlantAndEquipment']}
 ends=sorted({x['end'] for tag in tags['revenue'] for x in facts.get(tag,{}).get('units',{}).get('USD',[]) if x.get('filed','9999')<=DATE and x.get('start')=='2026-01-01' and x.get('end','')<=DATE})
 if not ends:return
 end=ends[-1];prior='2025'+end[4:];start='2025'+end[4:]
 ttm={}
 for key,tt in tags.items():
  fy=exact(tt,'2025-01-01','2025-12-31');cur=exact(tt,'2026-01-01',end);old=exact(tt,'2025-01-01',prior)
  if None not in (fy,cur,old):ttm[key]=fy+cur-old
 period='12 mois clos au '+end+'; FY2025 + YTD2026 - YTD2025'
 def puts(b,k,v,u,comment):put(doc,b,k,cell(v,u,period,DATE,url,status,comment))
 if 'revenue'in ttm:puts('qualite','ca_ttm',ttm['revenue'],'USD','Somme de périodes SEC alignées; versions déposées au plus tard le 04/11/2026.')
 if ttm.get('revenue',0)>0:
  for metric,key in [('gross','marge_brute_pct'),('ebit','marge_ebit_pct'),('net','marge_nette_pct')]:
   if metric in ttm:puts('qualite',key,ttm[metric]/ttm['revenue']*100,'pct',metric+'/CA TTM, mêmes périodes SEC.')
 if 'cfo'in ttm and 'capex'in ttm:
  fcf=ttm['cfo']-ttm['capex'];puts('qualite','fcf_ttm',fcf,'USD','FCF = CFO - achats immobilisations corporelles; acquisitions et logiciels exclus de cette convention.')
  if ttm.get('net',0)>0:puts('qualite','conversion_fcf_pct',fcf/ttm['net']*100,'pct','FCF/résultat net TTM; convention explicitée.')
 # Annual growth uses complete fiscal years, never YTD presented as annual.
 rev25=exact(tags['revenue'],'2025-01-01','2025-12-31');rev24=exact(tags['revenue'],'2024-01-01','2024-12-31');rev22=exact(tags['revenue'],'2022-01-01','2022-12-31')
 for key,val,pd in [('croissance_ca_1a_pct',(rev25/rev24-1)*100 if rev25 is not None and rev24 and rev24>0 else None,'FY2025 / FY2024'),('croissance_ca_3a_cagr_pct',((rev25/rev22)**(1/3)-1)*100 if rev25 and rev25>0 and rev22 and rev22>0 else None,'FY2022 / FY2025')]:
  if val is not None:put(doc,'croissance',key,cell(val,'pct',pd,DATE,url,status,'Calcul sur exercices calendaires complets SEC, non sur un semestre.'))
def main():
 paths=sorted(F.glob('*.json'));assert len(paths)==40
 histories={}
 with (D/'HISTORIQUES_YAHOO_40.csv').open() as f:
  for r in csv.DictReader(f):histories.setdefault(r['Ticker'],[]).append(r)
 stats={r['ticker']:r for r in load(D/'STATISTIQUES_SECONDAIRES_40_20261104.json')}
 research=load(D/'RECHERCHES_40_20261104.json')+load(D/'RECHERCHES_INITIES_40_20261104.json')
 insider_path=BASE/'AUDITS/FINALISATION_FICHES_20261104/SEC/INITIES_5_US.json'
 insiders={r['ticker']:r for r in load(insider_path)} if insider_path.exists() else {}
 profiles_path=D/'IDENTITES_CROISSANCE_40_20261104.json';profiles={r['ticker']:r for r in load(profiles_path)} if profiles_path.exists() else {}
 primary_path=D/'PREUVES_PRIMAIRES_FICHES_20261104.json';primaries=load(primary_path) if primary_path.exists() else []
 fx=load(D/'FX_REFERENCE_BCE_20261104.json')
 forecastpath=D/'PREVISIONS_40_20261104.json';fc={r['ticker']:r for r in load(forecastpath)} if forecastpath.exists() else {}
 report=[]
 for path in paths:
  x=load(path);t=x['ticker'];x.setdefault('observations_complementaires',[])
  market(x,histories.get(t,[]));sec(x);secondary(x,stats[t])
  if t in profiles:profile_growth(x,profiles[t])
  euro_metrics(x,stats[t],histories[t],fx)
  if t in fc:forecasts(x,fc[t])
  for evidence in primaries:
   if evidence['ticker']!=t:continue
   for v in evidence['champs']:
    if v['bloc'] and v['champ'] in x['blocs'][v['bloc']]:put(x,v['bloc'],v['champ'],cell(v['valeur'],v['unite'],v.get('periode',evidence['periode']),evidence['date_source'],evidence['url'],v.get('statut','SOURCE_PRIMAIRE'),v.get('commentaire')))
    else:x['observations_complementaires'].append(dict(bloc=v.get('bloc'),champ=v['champ'],**cell(v['valeur'],v['unite'],v.get('periode',evidence['periode']),evidence['date_source'],evidence['url'],v.get('statut','SOURCE_PRIMAIRE'),v.get('commentaire'))))
  if t in insiders:
   for days,v in insiders[t]['totaux'].items():
    if v['valeur'] is not None:put(x,'risque',f'transactions_initiees_net_{days}j',cell(v['valeur'],'USD',f'{days} jours calendaires clos au '+DATE,DATE,'https://data.sec.gov/submissions/CIK'+str(load(BASE/f'AUDITS/FINALISATION_FICHES_20261104/SEC/{t}_submissions.json')['cik']).zfill(10)+'.json','DEPOTS_SEC_FENETRE_CONTROLEE','Achats P moins ventes S, hors dons, attributions, exercices et dérivés; détails et erreurs dans INITIES_5_US.json.'))
  x['journal_recherches']=[]
  token=norm(x['societe'].split()[0]);aliases={'ALDMS.PA':['diagnosticmedical','dmsgroup'],'AL2SI.PA':['2crsi'],'ALIEV.PA':['ieva'],'GENI.ST':['generic'],'FTG.TO':['firan'],'ALMCE.PA':['moncourtier']}.get(t,[token])
  for batch in research:
   if (x['id_position']-1)//4!=batch['start']//4:continue
   urls=[r for r in batch['results'] if any(a in norm(r['title']+' '+r['url']) for a in aliases)]
   x['journal_recherches'].append({'famille':batch['family'],'requete':batch['queries'][(x['id_position']-1)%4],'date':DATE,'resultats_identifies':urls,'statut':'RECHERCHE_EFFECTUEE_RESULTATS_NON_EXHAUSTIFS'})
  x['journal_recherches'].append({'famille':'statistiques_financieres','url':stats[t]['url'],'date':DATE,'statut':stats[t]['statut'],'http':stats[t].get('http')})
  if t in fc:x['journal_recherches'].append({'famille':'previsions_annuelles','url':fc[t]['url'],'date':DATE,'statut':fc[t]['statut'],'http':fc[t].get('http'),'limite':'Les cellules Upgrade ne sont jamais converties en chiffres.'})
  cells=[(b,k,c) for b,block in x['blocs'].items() for k,c in block.items()]
  missing=[]
  for b,k,c in cells:
   if c['valeur'] is not None:c.pop('recherche',None)
   if c['valeur'] is None:
    reason='Aucune valeur vérifiée importée à cette étape; les recherches tracées ne démontrent pas une indisponibilité définitive.'
    if b=='complements' or k in ('marge_securite_pct','comparables_sectoriels','valorisation_historique','avantage_concurrentiel','qualite_management','interet_strategique','complementarite_portefeuille'):
     reason='Analyse MCPA/IPS argumentée encore nécessaire; ce champ ne doit pas être rempli par une statistique de fournisseur.'
    if k in ('revision_bpa_30j_pct','revision_bpa_90j_pct'):reason='Pas de série datée de consensus BPA à J, J-30/J-90 validée; évolution objectif de cours ou guidance non substituable.'
    if 'transactions_initiees_net' in k:reason='Registre complet des transactions, codes et prix non validé sur toute la fenêtre; transaction isolée ≠ net exhaustif.'
    if t=='ALIEV.PA' and k in ('prix_vers_mm200','tendance_mm200','momentum_12m_pct','drawdown_12m_pct'):reason='Historique IPO archivé insuffisant pour cette durée; impossible de calculer fidèlement à cette date.'
    c['recherche']={'date':DATE,'statut':'MANQUANT_RECHERCHE_NON_CLOSE','motif':reason,'journal':'journal_recherches'}
    missing.append(b+'.'+k)
  filled=sum(c['valeur'] is not None for _,_,c in cells);secondary_n=sum(c['valeur'] is not None and c['statut'].startswith('SOURCE_SECONDAIRE') for _,_,c in cells)
  x['audit_couverture']={'date':DATE,'champs_total':len(cells),'champs_renseignes':filled,'couverture_pct':round(filled/len(cells)*100,2),'champs_secondaires_non_rapproches':secondary_n,'champs_manquants':missing,'indisponibilite_definitive_demontree':[],'statut':'TRAITE_MAIS_INCOMPLET','cours_date_limite':PRICE_CUTOFF}
  x['statut_fiche']='ENRICHIE_NON_VALIDEE';x['arbitrage_autorise']=False
  # Re-running the import must not multiply evidence or calendars.
  x['observations_complementaires']=list({json.dumps(v,sort_keys=True,ensure_ascii=False):v for v in x['observations_complementaires']}.values())
  path.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
  report.append({'ID_position':x['id_position'],'Societe':x['societe'],'Ticker':t,'Champs_total':len(cells),'Renseignes':filled,'Couverture_pct':x['audit_couverture']['couverture_pct'],'Secondaires_non_rapproches':secondary_n,'Manquants':len(missing),'Statut':'ENRICHIE_NON_VALIDEE'})
 with (D/'COUVERTURE_FICHES_40_20261104.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(report[0]));w.writeheader();w.writerows(report)
 print(json.dumps({'fiches_traitees':len(report),'champs_renseignes':sum(r['Renseignes'] for r in report),'total':sum(r['Champs_total'] for r in report),'notes_attribuees':0}))
 if (D/'BILANS_ANNUELS_40_20261104.json').exists():
  subprocess.check_call([__import__('sys').executable,str(BASE/'SCRIPTS_ACTIFS/10B_COMPLETER_CALCULS_ET_STATUTS_40.py')],cwd=BASE)
if __name__=='__main__':main()

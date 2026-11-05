#!/usr/bin/env python3
"""Official AMF declared trades only. Exact issuer token and ISIN; never assume missing=0."""
import concurrent.futures,datetime as dt,hashlib,json,re,subprocess,unicodedata,urllib.request,urllib.parse
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'DONNEES';DATE='2026-11-05';OUT=D/'DECLARATIONS_AMF_14_20261105.json';ARCH=B/'AUDITS/POURSUITE_FICHES_40_20261105/AMF';ARCH.mkdir(parents=True,exist_ok=True)
CACHE={r['ticker']:r for r in json.loads(OUT.read_text())} if OUT.exists() else {}
NAMES={'ALSTI.PA':['STIF'],'MEMS.PA':['MEMSCAP'],'ALICA.PA':['ICAPE HOLDING','ICAPE'],'ALBFR.PA':['SIDETRADE'],'ALBPK.PA':['BROADPEAK'],'ALESE.PA':['ENTECH'],'ALDMS.PA':['DIAGNOSTIC MEDICAL SYSTEMS','DMS'],'ALSTW.PA':['STREAMWIDE','STREAM WIDE'],'ALSOG.PA':['SOGECLAIR'],'ALMCE.PA':['MON COURTIER ENERGIE GROUPE','MON COURTIER ENERGIE'],'AL2SI.PA':['2CRSI'],'ALLIX.PA':['WALLIX GROUP','WALLIX'],'ALCUR.PA':['ARCURE'],'ALIEV.PA':['IEVA GROUP','IEVA']}
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower())
def request(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json','Accept-Language':'fr'}),timeout=25) as r:return r.read(),r.status
def search(params):
 url='https://bdif.amf-france.org/back/api/v1/informations?'+urllib.parse.urlencode(params,doseq=True);raw,http=request(url);return json.loads(raw),dict(url=url,http=http,sha256_reponse=hashlib.sha256(raw).hexdigest())
def money(s):
 s=s.replace('\u202f','').replace('\xa0','').replace(' ','').replace(',','.');return float(s)
def date_fr(s):
 months={'janvier':1,'fevrier':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'aout':8,'septembre':9,'octobre':10,'novembre':11,'decembre':12}
 s=norm(s) if False else unicodedata.normalize('NFKD',s.strip()).encode('ascii','ignore').decode().lower()
 m=re.match(r'(\d{1,2})\s+([a-z]+)\s+(20\d{2})',s)
 if m:return dt.date(int(m[3]),months[m[2]],int(m[1])).isoformat()
 m=re.match(r'(\d{1,2})/(\d{1,2})/(20\d{2})',s)
 if m:return dt.date(int(m[3]),int(m[2]),int(m[1])).isoformat()
 raise ValueError('Date transaction non decodee')
def parse(text,isin):
 if isin not in text:raise ValueError('ISIN absent ou divergent')
 flat=' '.join(text.split());result={};m=re.search(r'LEI\s*:\s*([A-Za-z0-9]{20})',flat)
 if m:
  lei=m[1].upper();expanded=''.join(str(ord(c)-55) if c.isalpha() else c for c in lei)
  if int(expanded)%97==1:result['lei']=lei
 modification=bool(re.search(r'NOTIFICATION INITIALE / MODIFICATION\s*:\s*Modification',flat,re.I))
 parts=re.split(r'DETAIL DE LA TRANSACTION(?:\s+\d+)?',flat)[1:]
 if not parts:raise ValueError('Detail de transaction absent')
 trades=[]
 for index,part in enumerate(parts):
  x={'index_operation':index+1,'modification':modification}
  m=re.search(r'DATE DE LA TRANSACTION\s*:\s*(.*?)\s+LIEU DE LA TRANSACTION',part)
  if not m:raise ValueError('Date transaction absente')
  x['date_transaction']=date_fr(m[1])
  m=re.search(r'NATURE DE LA TRANSACTION\s*:\s*(.*?)\s+DESCRIPTION DE L.INSTRUMENT FINANCIER',part)
  if not m:raise ValueError('Nature transaction absente')
  x['nature']=m[1].strip();m=re.search(r'DESCRIPTION DE L.INSTRUMENT FINANCIER\s*:\s*(.*?)\s+(?:CODE D.IDENTIFICATION|INFORMATION DETAILLEE)',part)
  if not m:raise ValueError('Instrument non decode; pas une exclusion')
  x['instrument']=m[1].strip();option=re.search(r"TRANSACTION LIEE A L.EXERCICE.*?PERFORMANCES\s*:\s*(OUI|NON)",part,re.I);x['liee_options_attributions']=option[1].upper() if option else None
  if norm(x['nature']) not in ('acquisition','cession') or not norm(x['instrument']).startswith('action'):
   x['statut']='EXCLUE_NON_ACHAT_VENTE_COMPTANT';trades.append(x);continue
  if modification:x['statut']='AMENDEMENT_A_RAPPROCHER';trades.append(x);continue
  m=re.search(r'INFORMATIONS AGREGEES\s+PRIX\s*:\s*([0-9\s.,]+)\s+(Euro|EUR|USD|GBP|SEK|CAD)\s+VOLUME\s*:\s*([0-9\s.,]+)',part,re.I)
  if not m:m=re.search(r'PRIX UNITAIRE\s*:\s*([0-9\s.,]+)\s+(Euro|EUR|USD|GBP|SEK|CAD)\s+VOLUME\s*:\s*([0-9\s.,]+)',part,re.I)
  if not m:raise ValueError('Prix/volume/devise non decodes')
  pairs=re.findall(r'PRIX UNITAIRE\s*:\s*([0-9\s.,]+)\s+(Euro|EUR|USD|GBP|SEK|CAD)\s+VOLUME\s*:\s*([0-9\s.,]+)',part,re.I)
  if len(pairs)!=len(re.findall(r'PRIX UNITAIRE\s*:',part)):raise ValueError('Prix/volume elementaire manquant')
  currencies={'EUR' if z[1].lower() in ('euro','eur') else z[1].upper() for z in pairs}
  if len(currencies)!=1:raise ValueError('Devises multiples a rapprocher')
  volumes=[money(z[2]) for z in pairs];amount=sum(money(z[0])*money(z[2]) for z in pairs);volume=sum(volumes)
  if abs(volume-money(m[3]))>0.0001:raise ValueError('Volume agrege incoherent')
  x.update(prix=money(m[1]),devise=next(iter(currencies)),volume=volume,operations_elementaires=[{'prix':money(z[0]),'volume':money(z[2])} for z in pairs])
  x['valeur_nette']=round(amount*(1 if norm(x['nature'])=='acquisition' else -1),8);x['statut']='OPERATION_DECLAREE_PARSEE'
  if x['prix']==0:x['statut']='EXCLUE_NON_ACHAT_VENTE_COMPTANT'
  elif x['liee_options_attributions'] is None or (x['liee_options_attributions']=='OUI' and norm(x['nature'])=='acquisition'):x['statut']='QUALIFICATION_COMPTANT_A_VERIFIER'
  trades.append(x)
 result['transactions']=trades;result['statut']='DECLARATION_PARSEE' if all(x['statut'] in ('OPERATION_DECLAREE_PARSEE','EXCLUE_NON_ACHAT_VENTE_COMPTANT') for x in trades) else 'DECLARATION_PARTIELLE'
 return result

def aggregate(r):
 if r.get('pagination_complete') is not True:raise ValueError('Couverture de registre non prouvee')
 transactions=[dict(x,numero=rec['numero']) for rec in r['declarations'] for x in rec.get('transactions',[])]
 for days in (90,180):
  start=(dt.date.fromisoformat(DATE)-dt.timedelta(days=days)).isoformat();covered=[x for x in transactions if start<=x.get('date_transaction','')<=DATE]
  unresolved=[rec for rec in r['declarations'] if rec.get('statut') not in ('DECLARATION_PARSEE','DECLARATION_PARTIELLE')]
  errors=r['erreurs'] or unresolved or [x for x in covered if x['statut'] not in ('OPERATION_DECLAREE_PARSEE','EXCLUE_NON_ACHAT_VENTE_COMPTANT') or x.get('devise','EUR')!='EUR'];trades=[x for x in covered if x['statut']=='OPERATION_DECLAREE_PARSEE']
  r['totaux'][str(days)]={'debut':start,'fin':DATE,'valeur':None if errors else round(sum(x['valeur_nette'] for x in trades),8),'unite':'EUR','nombre_transactions':len(trades),'statut':'INCOMPLET' if errors else 'DEPOTS_AMF_FENETRE_CONTROLEE','limite':'Achats moins ventes d’actions au comptant déclarés et publiés à la date de collecte; exercices/attributions/dons distingués. Cessions liées à des programmes signalées. Hors frais, produits des prix/volumes déclarés. Pas preuve d’absence de transactions non publiées.'}
 return r

def collect(d):
 t=d['ticker']
 if t in CACHE:return CACHE[t]
 r=dict(ticker=t,societe=d['societe'],isin=d['blocs']['identite']['isin']['valeur'],date_collecte=DATE,recherches=[],declarations=[],erreurs=[],totaux={})
 try:
  aliases=NAMES[t];discovery,proof=search({'RechercheTexte':aliases[0],'From':0,'Size':50});r['recherches'].append(dict(famille='identite_AMF',**proof,total=discovery['total']))
  valid={norm(a) for a in aliases};issuers={s['jeton']:s['raisonSociale'] for info in discovery.get('result',[]) for s in info.get('societes',[]) if norm(s.get('raisonSociale')) in valid}
  if len(issuers)!=1:raise ValueError('Identite AMF non univoque')
  token,name=next(iter(issuers.items()));r.update(jeton=token,nom_AMF=name)
  offset=0;all_infos=[];total=None
  while total is None or offset<total:
   response,proof=search({'Jetons':token,'TypesInformation':'DD','DateDebut':'2026-01-01T00:00:00.000Z','DateFin':'2026-11-05T23:59:59.000Z','From':offset,'Size':100});r['recherches'].append(dict(famille='declarations_2026',**proof,total=response['total'],from_index=offset));total=response['total'];page=response.get('result',[])
   if not page and offset<total:raise ValueError('Pagination incomplete')
   all_infos.extend(page);offset+=len(page)
   if total>1000:raise ValueError('Volume anormal pour un seul emetteur')
   if not total:break
  if len(all_infos)!=total or len({i['numero'] for i in all_infos})!=total:raise ValueError('Couverture/duplications declarations')
  r['nombre_declarations_2026']=total;r['pagination_complete']=True
  for info in all_infos:
   if not any(s['jeton']==token for s in info.get('societes',[])):raise ValueError('Emetteur divergent dans recherche exacte')
   if info.get('langue') not in (None,'FR'):r['erreurs'].append(dict(numero=info['numero'],motif='Langue non FR a rapprocher'));continue
   pub=info.get('datePublication') or info.get('dateInformation');docs=[x for x in info.get('documents',[]) if x.get('accessible') and x.get('path','').endswith('.pdf')]
   if len(docs)!=1:r['erreurs'].append(dict(numero=info['numero'],motif='Nombre de PDF ambigu'));continue
   url='https://bdif.amf-france.org/back/api/v1/documents/'+docs[0]['path'];rec=dict(numero=info['numero'],date_publication=pub,url=url)
   try:
    raw,http=request(url)
    if not raw.startswith(b'%PDF'):raise ValueError('Reponse non PDF')
    pdf=ARCH/(info['numero']+'.pdf');txt=pdf.with_suffix('.txt');pdf.write_bytes(raw);subprocess.run(['pdftotext','-layout',str(pdf),str(txt)],check=True,capture_output=True);text=txt.read_text();rec.update(http=http,sha256_pdf=hashlib.sha256(raw).hexdigest(),archive_pdf=str(pdf.relative_to(B)),**parse(text,r['isin']))
   except Exception as e:rec.update(statut='NON_PARSEE',erreur=type(e).__name__,http=getattr(e,'code',rec.get('http')));r['erreurs'].append(dict(numero=info['numero'],motif=type(e).__name__))
   r['declarations'].append(rec)
  aggregate(r)
  r['statut']='RECHERCHE_REGISTRE_PRIMAIRE_EFFECTUEE'
 except Exception as e:r.update(statut='BLOQUE_ACCES_IDENTITE_OU_STRUCTURE',erreur=type(e).__name__,http=getattr(e,'code',None))
 return r
def reaggregate():
 rows=json.loads(OUT.read_text())
 for r in rows:
  if not r.get('pagination_complete'):continue
  for rec in r['declarations']:
   pdf=ARCH/(rec['numero']+'.pdf')
   if pdf.exists() and pdf.read_bytes().startswith(b'%PDF'):
    rec['archive_pdf']=str(pdf.relative_to(B));rec['sha256_pdf']=hashlib.sha256(pdf.read_bytes()).hexdigest()
  errors=[x for x in r['erreurs'] if not any(z['numero']==x.get('numero') and z.get('archive_pdf') for z in r['declarations'])]
  for i,rec in enumerate(r['declarations']):
   if not rec.get('archive_pdf'):continue
   base={k:v for k,v in rec.items() if k in ('numero','date_publication','url','http','sha256_pdf','archive_pdf')}
   try:
    pdf=B/rec['archive_pdf'];textpath=pdf.with_suffix('.txt')
    if not textpath.exists():subprocess.run(['pdftotext','-layout',str(pdf),str(textpath)],check=True,capture_output=True)
    base.update(parse(textpath.read_text(),r['isin']))
   except Exception as e:base.update(statut='NON_PARSEE',erreur=type(e).__name__);errors.append(dict(numero=rec['numero'],motif=str(e)))
   r['declarations'][i]=base
  r['erreurs']=errors;aggregate(r)
 OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');return rows

if __name__=='__main__':
 if '--reaggregate' in __import__('sys').argv:
  rows=reaggregate();print(json.dumps([{'ticker':r['ticker'],'erreurs':len(r['erreurs']),'nets':{k:v['valeur'] for k,v in r['totaux'].items()}} for r in rows]));raise SystemExit(0)
 docs=sorted([json.loads(p.read_text()) for p in (B/'DOSSIERS_MCPA_IPS_40').glob('*.json') if json.loads(p.read_text())['ticker'].endswith('.PA')],key=lambda d:d['id_position']);assert len(docs)==14
 rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
  for r in ex.map(collect,docs):
   rows.append(r);tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');tmp.replace(OUT)
 print(json.dumps([{'ticker':r['ticker'],'statut':r['statut'],'declarations':r.get('nombre_declarations_2026'),'nets':{k:v['valeur'] for k,v in r['totaux'].items()}} for r in rows]))

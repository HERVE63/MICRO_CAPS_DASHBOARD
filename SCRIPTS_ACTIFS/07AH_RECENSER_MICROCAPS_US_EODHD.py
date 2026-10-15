"""Recense les cotations US 50–300 M€ depuis EODHD, indépendamment des 172 pistes.
Archives fournisseur chiffrées ; seules les métriques de couverture sont publiques.
EODHD reste une source secondaire, pas une preuve SSI automatiquement vérifiée.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from decimal import Decimal,ROUND_FLOOR,ROUND_CEILING
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import urlencode
from urllib.error import HTTPError
import base64,hashlib,importlib.util,json,math,os,time,sys
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
MIN_EUR=Decimal('50000000');MAX_EUR=Decimal('300000000')
def paquet_chiffre(data,key):
 from cryptography.hazmat.primitives.ciphers.aead import AESGCM
 nonce=os.urandom(12);cle=hashlib.sha256(b'MICRO_CAPS_EODHD_V1\0'+key.encode()).digest()
 cipher=AESGCM(cle).encrypt(nonce,data,b'MICRO_CAPS_EODHD_V1')
 return {'version':1,'algorithme':'AES-256-GCM','nonce':base64.b64encode(nonce).decode(),
         'ciphertext':base64.b64encode(cipher).decode(),'SHA256_brut':hashlib.sha256(data).hexdigest()}
def dechiffrer(obj,key):
 from cryptography.hazmat.primitives.ciphers.aead import AESGCM
 cle=hashlib.sha256(b'MICRO_CAPS_EODHD_V1\0'+key.encode()).digest()
 data=AESGCM(cle).decrypt(base64.b64decode(obj['nonce']),base64.b64decode(obj['ciphertext']),b'MICRO_CAPS_EODHD_V1')
 if hashlib.sha256(data).hexdigest()!=obj['SHA256_brut']:raise ValueError('ARCHIVE_EODHD_CORROMPUE')
 return data
class AucuneRedirection(HTTPRedirectHandler):
 def redirect_request(self,*a,**k):raise RuntimeError('REDIRECTION_EODHD_REFUSEE')
class Client:
 def __init__(self,key,out):
  self.key=key;self.out=out;self.index=[];self.cout=0;self.budget=5;self.dernier=0;self.cache={}
  today=datetime.now(timezone.utc).date().isoformat()
  for p in sorted(out.parent.glob('*/INDEX_REQUETES.json')):
   if p.parent==out:continue
   for r in json.loads(p.read_text()):
    if r.get('archive_chiffree') and r.get('date_collecte_utc','')[:10]==today:
     self.cache[(r['route'],json.dumps(r['parametres'],sort_keys=True))]=(p.parent,r)
 def archiver(self,nom,data):
  raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()
  p=self.out/(nom+'.enc.json');p.write_text(json.dumps(paquet_chiffre(raw,self.key)))
  return p.name
 def get(self,path,params=None,cout=1,archive=True):
  ident=(path,json.dumps(params or {},sort_keys=True))
  if archive and ident in self.cache:
   parent,r=self.cache[ident];p=parent/r['archive_chiffree'];manifest=json.loads((parent/'MANIFESTE.json').read_text())
   if manifest['fichiers'].get(p.name)!=hashlib.sha256(p.read_bytes()).hexdigest():raise RuntimeError('CACHE_EODHD_CORROMPU')
   data=json.loads(dechiffrer(json.loads(p.read_text()),self.key))
   nom=self.archiver('REPONSE_'+str(len(self.index)).zfill(5),data)
   self.index.append(dict(r,archive_chiffree=nom,archive_source=str(p.relative_to(BASE)),date_relecture_utc=datetime.now(timezone.utc).isoformat(),cout_estime=0))
   return data
  if self.cout+cout>self.budget:raise RuntimeError('QUOTA_RESERVE_CPI_ATTEINT_REPRISE_NECESSAIRE')
  self.cout+=cout;time.sleep(max(0,.3-(time.monotonic()-self.dernier)));self.dernier=time.monotonic()
  query=dict(params or {},api_token=self.key,fmt='json')
  # La clé est uniquement transmise à EODHD et n'entre jamais dans l'audit.
  req=Request('https://eodhd.com/api/'+path+'?'+urlencode(query),headers={'Accept':'application/json','User-Agent':'MICRO_CAPS scientific research'})
  try:
   with build_opener(AucuneRedirection()).open(req,timeout=45) as response:raw=response.read(40_000_001)
  except HTTPError as exc:raise RuntimeError('EODHD_HTTP_'+str(exc.code)) from None
  except Exception as exc:raise RuntimeError('EODHD_RESEAU_'+type(exc).__name__) from None
  if len(raw)>40_000_000:raise RuntimeError('REPONSE_EODHD_TROP_VOLUMINEUSE')
  try:data=json.loads(raw)
  except (ValueError,UnicodeError):raise RuntimeError('EODHD_REPONSE_NON_JSON') from None
  if isinstance(data,dict) and any(k in data for k in ['error','errors']):raise RuntimeError('ERREUR_API_EODHD')
  item={'route':path,'parametres':params or {},'date_collecte_utc':datetime.now(timezone.utc).isoformat(),'cout_estime':cout}
  if archive:item['archive_chiffree']=self.archiver('REPONSE_'+str(len(self.index)).zfill(5),data)
  self.index.append(item)
  (self.out/'INDEX_REQUETES.json').write_text(json.dumps(self.index,ensure_ascii=False,indent=2))
  return data
def recenser_bande(fetch,lo,hi,journal):
 """Partitions disjointes : aucune troncature silencieuse au plafond 1 000."""
 rows=[]
 for offset in range(0,1000,100):
  page=fetch(lo,hi,offset)
  if not isinstance(page,list):raise RuntimeError('SCHEMA_SCREEENER_EODHD_INVALIDE')
  rows.extend(page)
  if len(page)<100:
   journal.append({'borne_USD_min':lo,'borne_USD_max':hi,'resultats':len(rows),'pagination_complete':True});return rows
 if lo>=hi:raise RuntimeError('SATURATION_SCREEENER_VALEUR_UNIQUE')
 mid=(lo+hi)//2
 journal.append({'borne_USD_min':lo,'borne_USD_max':hi,'resultats':len(rows),'subdivisee':True})
 return recenser_bande(fetch,lo,mid,journal)+recenser_bande(fetch,mid+1,hi,journal)
def normaliser(rows,catalogue,fx,date_fx,asof):
 table={r['Code']:r for r in catalogue if r.get('Code')};valid=[];attente=[]
 for r in rows:
  code=r.get('code');cat=table.get(code);motif=''
  if cat is None:motif='ABSENT_CATALOGUE_US'
  elif cat.get('Type')!='Common Stock':motif='TYPE_NON_ACTION_ORDINAIRE_OU_A_VERIFIER'
  elif cat.get('Currency')!='USD':motif='DEVISE_A_VERIFIER'
  try:
   cap=Decimal(str(r['market_capitalization']));eur=cap/fx
   if not cap.is_finite() or cap<=0:raise ValueError()
  except (KeyError,ValueError,ArithmeticError):motif=motif or 'CAPITALISATION_NON_EXPLOITABLE';eur=None
  date=r.get('last_day_data_date','')
  try:datetime.strptime(date,'%Y-%m-%d')
  except (ValueError,TypeError):motif=motif or 'DATE_MARCHE_INVALIDE'
  if date and date>asof:motif=motif or 'DATE_MARCHE_FUTURE'
  if eur is not None and not MIN_EUR<=eur<=MAX_EUR:motif=motif or 'HORS_BANDE_50_300_MEUR'
  row={'Ticker_US':str(code)+'.US','Societe':r.get('name',''),'ISIN_catalogue':(cat or {}).get('Isin',''),
   'Pays_catalogue_non_verifie':(cat or {}).get('Country',''),'Capitalisation_EUR':str(eur) if eur is not None else '',
   'Date_marche':date,'FX_EURUSD':str(fx),'Date_FX':date_fx,'Secteur':r.get('sector',''),
   'Statut_identite':'A_VERIFIER_EMETTEUR_US','SSI':'MANQUANTE',
   'Statut_fraicheur':'DATE_MARCHE_CONCORDE_FX' if date==date_fx else 'DATES_A_RAPPROCHER'}
  if motif:attente.append(dict(row,Motif=motif))
  else:valid.append(row)
 return valid,attente
def profil_sec(cik,agent,client,cache):
 cik=str(cik or '').zfill(10)
 if not cik.isdigit() or int(cik)==0:return {'Statut_origine':'CIK_EODHD_A_COMPLETER'}
 if not agent or '@' not in agent:return {'Statut_origine':'CONTACT_SEC_ABSENT_ORIGINE_A_VERIFIER'}
 if cik in cache:return cache[cik]
 url='https://data.sec.gov/submissions/CIK'+cik+'.json'
 try:
  time.sleep(.3)
  with build_opener(AucuneRedirection()).open(Request(url,headers={'User-Agent':agent,'Accept-Encoding':'identity'}),timeout=35) as response:data=response.read(5_000_001)
  if len(data)>5_000_000:raise RuntimeError('PROFIL_SEC_TROP_VOLUMINEUX')
  obj=json.loads(data)
  spec=importlib.util.spec_from_file_location('origine_us_sec',BASE/'SCRIPTS_ACTIFS/07AE_CADRER_UNIVERS_US.py')
  mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  statut=mod.classer(obj,cik)
  result={'Statut_origine':statut,'Source_origine_URL':url,'Date_profil_SEC_UTC':datetime.now(timezone.utc).isoformat(),
    'Archive_profil_SEC':client.archiver('PROFIL_SEC_'+cik,obj),'Nom_SEC':obj.get('name','')}
 except Exception as exc:result={'Statut_origine':'SOURCE_SEC_A_COMPLETER','Code_HTTP_SEC':getattr(exc,'code',''),'Type_erreur_SEC':type(exc).__name__}
 cache[cik]=result;return result
def executer():
 now=datetime.now(timezone.utc);out=BASE/'AUDITS/RECENSEMENT_US_EODHD'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 key=os.getenv('EODHD_API_KEY','').strip();client=None
 bilan={'date_utc':now.isoformat(),'secret_disponible':bool(key),'source_script_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'perimetre':'CATALOGUE_COMPLET_COTATIONS_US_EODHD_50_300_MEUR','depend_des_172':False,
  'recensement_termine':False,'origine_US_verifiee':False,'notes_SSI_attribuees':0,'positions_modifiees':False}
 try:
  if not key:raise RuntimeError('EODHD_API_KEY_ABSENTE_DU_DEPOT_MICRO_CAPS')
  client=Client(key,out);usage=client.get('user',archive=False)
  compte={k:usage.get(k) for k in ['subscriptionType','apiRequests','apiRequestsDate','dailyRateLimit']}
  bilan['quota_avant']=compte
  used=int(usage.get('apiRequests') or 0) if str(usage.get('apiRequestsDate',''))[:10]==now.date().isoformat() else 0
  restant=int(usage.get('dailyRateLimit') or 0)-used
  reserve=10000
  client.budget=min(30000,max(0,restant-reserve));bilan['reserve_credits_autres_outils']=reserve
  if client.budget<100:raise RuntimeError('QUOTA_INSUFFISANT_SANS_TOUCHER_RESERVE_AUTRES_OUTILS')
  cat=client.get('exchange-symbol-list/US',{'delisted':0})
  if not isinstance(cat,list) or not cat:raise RuntimeError('CATALOGUE_US_VIDE_OU_SCHEMA_INVALIDE')
  if len({r.get('Code') for r in cat})!=len(cat):raise RuntimeError('DOUBLONS_CATALOGUE_US')
  bilan.update(cotations_catalogue_US=len(cat),actions_ordinaires_catalogue=sum(r.get('Type')=='Common Stock' for r in cat))
  fin=(now-timedelta(days=1)).date().isoformat();debut=(now-timedelta(days=14)).date().isoformat()
  cours=client.get('eod/EURUSD.FOREX',{'from':debut,'to':fin,'period':'d','order':'a'})
  disponibles=[r for r in cours if debut<=r.get('date','')<=fin and r.get('close') is not None]
  if not disponibles:raise RuntimeError('FX_OFFICIEL_FOURNISSEUR_NON_DISPONIBLE')
  fxrow=max(disponibles,key=lambda r:r['date']);fx=Decimal(str(fxrow['close']))
  if not fx.is_finite() or fx<=0:raise RuntimeError('FX_EURUSD_INVALIDE')
  lo=int((MIN_EUR*fx).to_integral_value(rounding=ROUND_FLOOR));hi=int((MAX_EUR*fx).to_integral_value(rounding=ROUND_CEILING))
  def fetch(lo,hi,offset):
   f=[['exchange','=','us'],['market_capitalization','>=',lo],['market_capitalization','<=',hi]]
   obj=client.get('screener',{'filters':json.dumps(f,separators=(',',':')),'sort':'market_capitalization.asc','limit':100,'offset':offset},cout=5)
   return obj.get('data') if isinstance(obj,dict) else obj
  partitions=[];rows=recenser_bande(fetch,lo,hi,partitions)
  # Un doublon peut cacher une pagination instable : bloquer au lieu de l'effacer silencieusement.
  if len({r.get('code') for r in rows})!=len(rows):raise RuntimeError('PAGINATION_SCREEENER_DOUBLONS_A_REPRENDRE')
  candidats,attente=normaliser(rows,cat,fx,fxrow['date'],now.date().isoformat())
  client.archiver('RESULTATS_SCREEENER_NORMALISES',{'candidats':candidats,'attente_ou_hors_bande':attente})
  bilan.update(resultats_screener=len(rows),candidats_cotation_US_50_300_MEUR=len(candidats),
   cas_a_revoir_ou_hors_bande=len(attente),pagination_complete=True,partitions=partitions,
   FX_EURUSD=str(fx),date_FX=fxrow['date'],inventaire_catalogue_screener_termine=True)
  dossiers=[];profils={};agent=os.getenv('SEC_USER_AGENT','').strip()
  for r in candidats:
   symbol=r['Ticker_US']
   try:
    f=client.get('fundamentals/'+symbol,cout=10)
    if not isinstance(f,dict) or not isinstance(f.get('General'),dict):raise RuntimeError('FONDAMENTAUX_SCHEMA_INVALIDE')
    g=f['General']
    if g.get('Code')!=symbol[:-3]:raise RuntimeError('IDENTITE_CODE_EODHD_INCOHERENTE')
    origine=profil_sec(g.get('CIK',''),agent,client,profils)
    dossiers.append(dict(r,CIK=g.get('CIK',''),ISIN=g.get('ISIN',''),Pays_cotation_EODHD=g.get('CountryName',''),
     Type_EODHD=g.get('Type',''),Ticker_primaire_EODHD=g.get('PrimaryTicker',''),
     Fondamentaux_presents=bool(f.get('Financials')),**origine))
   except RuntimeError as exc:
    if 'QUOTA_' in str(exc) or str(exc) in ['EODHD_HTTP_401','EODHD_HTTP_403']:raise
    dossiers.append(dict(r,Statut_collecte=str(exc)))
   if len(dossiers)%100==0:print('EODHD :',len(dossiers),'/',len(candidats),'dossiers traités',flush=True)
  client.archiver('DOSSIERS_EODHD_A_VERIFIER',dossiers)
  bilan.update(fondamentaux_collectes=sum('Statut_collecte' not in r for r in dossiers),
   echecs_fondamentaux=sum('Statut_collecte' in r for r in dossiers),
   pistes_emetteurs_US=sum(r.get('Statut_origine')=='PISTE_US_CONCORDANTE' for r in dossiers),
   repartition_origine={k:int(v) for k,v in pd.Series([r.get('Statut_origine','COLLECTE_INCOMPLETE') for r in dossiers],dtype=str).value_counts().items()},
   recensement_termine=True,statut='RECENSEMENT_FOURNISSEUR_TERMINE_IDENTITES_ET_PREUVES_A_VERIFIER')
 except Exception as exc:
  message=str(exc).replace(key,'[MASQUE]') if key else str(exc)
  bilan.update(statut='BLOQUE_OU_PARTIEL',blocage=message[:200] if isinstance(exc,RuntimeError) else type(exc).__name__)
 finally:
  if client:
   (out/'INDEX_REQUETES.json').write_text(json.dumps(client.index,ensure_ascii=False,indent=2))
   bilan['credits_estimes_utilises']=client.cout
  bilan['fichiers']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
  (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(bilan,ensure_ascii=False));return bilan
if __name__=='__main__':
 b=executer();sys.exit(0 if b['recensement_termine'] and not b.get('echecs_fondamentaux') else 1)

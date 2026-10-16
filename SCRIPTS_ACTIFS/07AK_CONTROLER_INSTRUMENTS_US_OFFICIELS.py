"""Contrôle les libellés d'instruments des cotations US sur Nasdaq Trader.

Les deux répertoires officiels couvrent Nasdaq et les autres places US listées,
pas tout l'OTC. Une absence reste à compléter ; aucun émetteur ni SSI n'est
validé par le seul libellé. Aucune heuristique sur la dernière lettre du ticker.
"""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import urlparse
import csv,gzip,hashlib,io,json,re,time
import pandas as pd

BASE=Path(__file__).resolve().parents[1]
SOURCES=['https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt',
         'https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lire_repertoire(raw):
 texte=raw.decode('utf-8-sig');lignes=texte.splitlines()
 pied=[l for l in lignes if l.startswith('File Creation Time:')]
 if len(pied)!=1:raise RuntimeError('HORODATAGE_REPERTOIRE_ABSENT_OU_AMBIGU')
 horodatage=pied[0].split('|',1)[0].split(':',1)[1].strip()
 creation=datetime.strptime(horodatage,'%m%d%Y%H:%M')
 if creation.date()>datetime.now(timezone.utc).date():raise RuntimeError('REPERTOIRE_FUTUR')
 table=list(csv.DictReader(io.StringIO('\n'.join(l for l in lignes if not l.startswith('File Creation Time:'))),delimiter='|'))
 if not table or not {'Security Name','Test Issue','ETF'}.issubset(table[0]):raise RuntimeError('SCHEMA_REPERTOIRE_INVALIDE')
 return table,horodatage
def classer(r):
 if r.get('Test Issue')=='Y':return 'INSTRUMENT_TEST_NON_ADMISSIBLE'
 if r.get('ETF')=='Y' or r.get('NextShares')=='Y':return 'ETF_ETP_NON_ADMISSIBLE'
 nom=r.get('Security Name','').lower();classe=nom.split(' - ',1)[-1]
 if re.search(r'\bwarrants?\b|\brights\b|\bdebentures?\b|\bbonds?\b|\bnotes\b',classe):return 'AUTRE_INSTRUMENT_NON_ORDINAIRE'
 if re.search(r'\bunits?\b',classe):return 'UNITES_A_VERIFIER'
 if re.search(r'\bpreferred (?:stock|shares?)\b',classe):return 'PREFERENTIELLE_NON_ORDINAIRE'
 if re.search(r'\bdeposit[ao]ry\b|\bads\b|\badr\b',classe):return 'REPRESENTATION_DEPOSITAIRE_A_VERIFIER'
 if re.search(r'\bcommon (?:stock|shares?)\b|\bordinary (?:stock|shares?)\b',classe):return 'ACTION_ORDINAIRE_LIBELLE_OFFICIEL'
 return 'TYPE_A_VERIFIER'
def rapprocher(candidats,repertoires):
 index={}
 for url,rows in repertoires:
  for i,r in enumerate(rows):
   for t in {r.get(k,'').strip() for k in ('Symbol','ACT Symbol','CQS Symbol','NASDAQ Symbol')} - {''}:
    index.setdefault(t,{})[(url,i)]=(url,r)
 result=[]
 for r in candidats:
  code=r['Ticker_US'][:-3];matches=list(index.get(code,{}).values())
  row=dict(r,Statut_instrument='ABSENT_REPERTOIRES_LISTES_OTC_OU_IDENTITE_A_COMPLETER',
           Nom_instrument_officiel='',Source_instrument_URL='',Note_SSI='',Admission_SSI='NON')
  if len(matches)>1:row['Statut_instrument']='CONCORDANCE_SYMBOLE_AMBIGUE'
  elif len(matches)==1:
   url,src=matches[0];row.update(Statut_instrument=classer(src),Nom_instrument_officiel=src['Security Name'],
      Source_instrument_URL=url,Statut_financier_cotation=src.get('Financial Status',''),
      Place_source=src.get('Exchange',src.get('Market Category','')))
  result.append(row)
 return result
class RedirectionsOfficielles(HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  u=urlparse(newurl)
  if u.scheme!='https' or u.hostname not in ('www.nasdaqtrader.com','nasdaqtrader.com'):raise RuntimeError('REDIRECTION_HORS_SOURCE_OFFICIELLE')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def executer():
 manifests=sorted((BASE/'AUDITS/RECENSEMENT_US_EODHD').glob('*/MANIFESTE.json'))
 if not manifests:raise RuntimeError('RECENSEMENT_US_ABSENT')
 mp=manifests[-1];m=json.loads(mp.read_text());src=mp.parent/'COUVERTURE_PREUVES_SEC.csv'
 if not m.get('recensement_termine') or m['fichiers'].get(src.name)!=sha(src):raise RuntimeError('RECENSEMENT_INCOMPLET_OU_CORROMPU')
 candidats=pd.read_csv(src,dtype=str,keep_default_na=False).to_dict('records')
 if len({r['Ticker_US'] for r in candidats})!=len(candidats):raise RuntimeError('DOUBLONS_TICKER')
 out=BASE/'AUDITS/INSTRUMENTS_US_OFFICIELS'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out.mkdir(parents=True,exist_ok=False);repertoires=[];sources=[]
 for n,url in enumerate(SOURCES):
  if n:time.sleep(.5)
  with build_opener(RedirectionsOfficielles()).open(Request(url,headers={'User-Agent':'MICRO_CAPS scientific research','Accept-Encoding':'identity'}),timeout=45) as response:
   raw=response.read(5_000_001)
  if len(raw)>5_000_000:raise RuntimeError('REPERTOIRE_TROP_VOLUMINEUX')
  table,date=lire_repertoire(raw);p=out/(Path(url).name+'.gz');p.write_bytes(gzip.compress(raw,mtime=0))
  sources.append({'url':url,'creation_fichier_heure_source':date,'date_collecte_utc':datetime.now(timezone.utc).isoformat(),
   'SHA256_octets_source':hashlib.sha256(raw).hexdigest(),'SHA256_archive':sha(p),'lignes':len(table)})
  repertoires.append((url,table))
 rows=rapprocher(candidats,repertoires);df=pd.DataFrame(rows)
 df.to_csv(out/'CONTROLE_INSTRUMENTS_US.csv',index=False)
 bilan={'date_utc':datetime.now(timezone.utc).isoformat(),'source_recensement':str(mp.relative_to(BASE)),
  'source_manifeste_SHA256':sha(mp),'source_script_SHA256':sha(Path(__file__)),
  'cotations_controlees':len(df),'repartition_instruments':df.Statut_instrument.value_counts().to_dict(),
  'sources':sources,'identites_emetteurs_validees':0,'notes_SSI_attribuees':0,'admissions_SSI':0,
  'statut':'CONTROLE_LIBELLES_OFFICIELS_SANS_ADMISSION_SSI',
  'fichiers':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(bilan,ensure_ascii=False));return bilan
if __name__=='__main__':executer()

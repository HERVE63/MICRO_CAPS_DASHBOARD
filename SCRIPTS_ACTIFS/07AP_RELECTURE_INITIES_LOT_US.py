"""Actualise un lot SCE puis exécute 07Y avec conservation des index et XML SEC.
La période est explicite ; aucun flux n'est assimilé à une détention courante
ou à une décision SSI. Amendements et déclarations conjointes restent visibles.
"""
from pathlib import Path
from datetime import datetime,timezone
from io import BytesIO
from urllib.request import Request,build_opener
from urllib.parse import urlparse
import gzip,hashlib,importlib.util,json,os,re,time
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def charger(nom):
 s=importlib.util.spec_from_file_location(nom[:-3],BASE/'SCRIPTS_ACTIFS'/nom);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Reponse(BytesIO):
 def __enter__(self):return self
 def __exit__(self,*a):self.close()
class ClientSEC:
 def __init__(self,out,agent):
  if '@' not in agent:raise RuntimeError('CONTACT_SEC_INVALIDE')
  self.out=out;self.agent=agent;self.sources=[];self.dernier=0.;self.opener=build_opener(charger('07AF_COLLECTER_DOCUMENTS_US.py').RedirectionsSEC())
 def open(self,req,timeout=35):
  url=req.full_url;u=urlparse(url)
  if u.scheme!='https' or u.username or u.password or u.port not in (None,443):raise ValueError('URL_SEC_INVALIDE')
  if not ((u.hostname=='data.sec.gov' and re.fullmatch(r'/submissions/(?:CIK\d{10}|CIK\d{10}-submissions-\d+)\.json',u.path)) or (u.hostname=='www.sec.gov' and re.fullmatch(r'/Archives/edgar/data/\d+/\d{18}/[A-Za-z0-9_.-]+',u.path))):raise ValueError('URL_HORS_PERIMETRE_SEC')
  time.sleep(max(0,.3-(time.monotonic()-self.dernier)));self.dernier=time.monotonic()
  with self.opener.open(Request(url,headers={'User-Agent':self.agent,'Accept-Encoding':'identity'}),timeout=timeout) as response:data=response.read(30_000_001)
  if not data or len(data)>30_000_000:raise ValueError('REPONSE_SEC_TAILLE_INVALIDE')
  debut=data[:8000].lower()
  if any(x in debut for x in (b'undeclared automated tool',b'request rate threshold exceeded',b'access denied')):raise ValueError('PAGE_REFUS_SEC')
  digest=hashlib.sha256(data).hexdigest();p=self.out/(digest+'.bin.gz');p.write_bytes(gzip.compress(data,mtime=0))
  self.sources.append({'URL':url,'Date_collecte_UTC':datetime.now(timezone.utc).isoformat(),'SHA256_brut':digest,'SHA256_archive':sha(p),'Fichier_brut':str(p.relative_to(BASE))})
  (self.out/'SOURCES_HTTP.json').write_text(json.dumps(self.sources,ensure_ascii=False,indent=2)+'\n')
  return Reponse(data)
def depots(obj,limite):
 q=obj.get('filings',{}).get('recent',{});forms=q.get('form',[])
 if any(len(q.get(k,[]))!=len(forms) for k in ('filingDate','accessionNumber','primaryDocument')):raise ValueError('INDEX_SEC_INCOMPLET')
 rows=[]
 for form,date,acc,doc in zip(forms,q['filingDate'],q['accessionNumber'],q['primaryDocument']):
  datetime.strptime(date,'%Y-%m-%d')
  if date<=limite:rows.append({'Formulaire':form,'Date_depot':date,'Accession':acc,'Document_primaire':doc})
 return rows

def executer():
 now=datetime.now(timezone.utc);limite=now.date().isoformat();debut='2026-01-01'
 source=BASE/'AUDITS/RECHERCHE_COMPLEMENTS_US/2026-10-18_LOT_ORDRE_SCE/LOT_PRIORISATION.csv'
 sm=json.loads((source.parent/'MANIFESTE.json').read_text())
 if sm['fichiers'].get(source.name)!=sha(source):raise RuntimeError('LOT_SCE_CORROMPU')
 lot=pd.read_csv(source,dtype=str,keep_default_na=False)
 if lot.CIK.duplicated().any() or lot.Ticker.duplicated().any():raise RuntimeError('LOT_DUPLIQUE')
 out=BASE/'AUDITS/RELECTURE_INITIES_US'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 brut=out/'BRUTS';brut.mkdir();client=ClientSEC(brut,os.getenv('SEC_USER_AGENT',''))
 y=charger('07Y_EXTRAIRE_FORM4_SEC.py');af=charger('07AF_COLLECTER_DOCUMENTS_US.py');g=charger('07AO_PASSAGES_GOUVERNANCE_US.py')
 index=[];profils=[];documents=[];pagination=[];erreurs=[]
 for _,r in lot.iterrows():
  url='https://data.sec.gov/submissions/CIK'+r.CIK+'.json'
  try:
   with client.open(Request(url)) as response:obj=json.load(response)
   if str(obj.get('cik','')).zfill(10)!=r.CIK:raise RuntimeError('CIK_PROFIL_DIVERGENT')
   if r.Ticker.removesuffix('.US') not in obj.get('tickers',[]):raise RuntimeError('TICKER_NON_CONCORDANT_PROFIL_ACTUEL')
   rows=depots(obj,limite);profils.append({'Ticker':r.Ticker,'CIK':r.CIK,'Nom_SEC':obj.get('name',''),'SIC':obj.get('sic',''),'Source_URL':url,'Statut':'PROFIL_CIK_TICKER_CONCORDANTS','Date_collecte_UTC':client.sources[-1]['Date_collecte_UTC']})
   # Les partitions d'archives dont la période rencontre la fenêtre sont parcourues.
   for old in obj.get('filings',{}).get('files',[]):
    if old.get('filingTo','')<debut:continue
    name=old.get('name','')
    if not re.fullmatch(r'CIK\d{10}-submissions-\d+\.json',name):raise ValueError('PARTITION_SEC_INVALIDE')
    with client.open(Request('https://data.sec.gov/submissions/'+name)) as response:older=json.load(response)
    rows.extend(depots({'filings':{'recent':older}},limite));pagination.append({'CIK':r.CIK,'Partition':name,'Statut':'LUE'})
   seen=set()
   for q in rows:
    if q['Formulaire'] not in ('4','4/A') or not debut<=q['Date_depot']<=limite:continue
    if q['Accession'] in seen:continue
    seen.add(q['Accession']);index.append({'Ticker':r.Ticker,'CIK':r.CIK,**q})
   # Actualiser la description d'activité et les nouvelles informations après le 10-Q.
   for form in ('10-Q','10-K','DEF 14A'):
    qs=[q for q in rows if q['Formulaire']==form]
    if not qs:continue
    q=max(qs,key=lambda q:(q['Date_depot'],q['Accession']))
    docurl=af.url_document(r.CIK,q['Accession'],q['Document_primaire'])
    with client.open(Request(docurl)) as response:data=response.read()
    text=g.texte_brut(data);p=out/(r.CIK+'_'+form.replace(' ','_')+'.txt.gz');p.write_bytes(gzip.compress(text.encode(),mtime=0))
    documents.append({'Ticker':r.Ticker,'CIK':r.CIK,**q,'Source_URL':docurl,'SHA256_brut':hashlib.sha256(data).hexdigest(),'Texte_normalise':str(p.relative_to(BASE)),'Description_blank_check':'OUI' if re.search(r'\bblank[ -]check company\b',text,re.I) else 'NON_REPEREE','Statut':'CONTENU_A_RELIRE_AUCUNE_EXCLUSION_AUTOMATIQUE'})
   for q in rows:
    if q['Formulaire'] not in ('8-K','8-K/A') or q['Date_depot']<'2026-07-01':continue
    row={'Ticker':r.Ticker,'CIK':r.CIK,**q,'Source_URL':af.url_document(r.CIK,q['Accession'],q['Document_primaire']),'Statut':'NOUVELLE_INFORMATION_A_LIRE_AVANT_EXCLUSION_OU_NOTE','Description_blank_check':'NON_TESTEE'}
    # Tous les émetteurs : une annonce postérieure peut modifier bilan, gouvernance ou identité.
    with client.open(Request(row['Source_URL'])) as response:data=response.read()
    text=g.texte_brut(data);p=out/(r.CIK+'_'+q['Accession']+'.txt.gz');p.write_bytes(gzip.compress(text.encode(),mtime=0))
    row.update(Texte_normalise=str(p.relative_to(BASE)),SHA256_brut=hashlib.sha256(data).hexdigest(),Statut='8K_LOT_COLLECTE_A_RELIRE')
    documents.append(row)
  except Exception as exc:
   erreurs.append({'Ticker':r.Ticker,'CIK':r.CIK,'Erreur':type(exc).__name__+': '+str(exc)});print(r.Ticker,'SOURCE_A_COMPLETER',type(exc).__name__,flush=True)
  print('Profils du lot : '+str(len(profils))+'/'+str(len(lot)),flush=True)
 pd.DataFrame(profils).to_csv(out/'PROFILS_ACTUALISES.csv',index=False)
 pd.DataFrame(documents).to_csv(out/'DOCUMENTS_ET_NOUVELLES_INFOS.csv',index=False)
 pd.DataFrame(pagination,columns=['CIK','Partition','Statut']).to_csv(out/'PAGINATION.csv',index=False)
 pd.DataFrame(index,columns=['Ticker','CIK','Formulaire','Date_depot','Accession','Document_primaire']).to_csv(out/'INDEX_FORM4_LOT.csv',index=False)
 pd.DataFrame(erreurs,columns=['Ticker','CIK','Erreur']).to_csv(out/'ERREURS_PROFILS.csv',index=False)
 y.SRC=out/'INDEX_FORM4_LOT.csv';y.OUT=out/'TRANSACTIONS_FORM4_LOT.csv';y.AUD=out/'AUDIT_FORM4_LOT.csv'
 y.urlopen=client.open
 from types import SimpleNamespace
 y.time=SimpleNamespace(sleep=lambda n:None)
 rows=y.executer();audit=pd.read_csv(y.AUD,dtype=str,keep_default_na=False)
 bilan={'date_utc':now.isoformat(),'date_debut_depots':debut,'date_limite_depots':limite,'source_lot':str(source.relative_to(BASE)),'source_lot_SHA256':sha(source),'source_script_SHA256':sha(Path(__file__)),'module_07Y_SHA256':sha(BASE/'SCRIPTS_ACTIFS/07Y_EXTRAIRE_FORM4_SEC.py'),'emetteurs_lot':len(lot),'profils_concordants':len(profils),'profils_en_erreur':len(erreurs),'depots_form4_indexes':len(index),'transactions_non_derivees_extraites':len(rows),'repartition_controles':audit.Statut.value_counts().to_dict(),'reponses_HTTP_archivees':len(client.sources),'notes_SSI_attribuees':0,'detentions_actuelles_reconstituees':False,'historique_depuis_2026_complet_valide':False,'fichiers':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in bilan.items() if k!='fichiers'},ensure_ascii=False))
 return bilan
if __name__=='__main__':
 m=executer()
 if m['profils_en_erreur'] or any(k!='TRANSACTIONS_A_VERIFIER' for k in m['repartition_controles']):raise SystemExit(1)

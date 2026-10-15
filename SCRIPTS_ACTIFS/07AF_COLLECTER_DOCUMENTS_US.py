"""Archive les pièces primaires 10-K/10-Q/DEF 14A des pistes US, sans noter.
Les noms de documents viennent des index SEC conservés, pas d'une recherche floue.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime,timezone
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import urlparse
from urllib.error import HTTPError
import hashlib,json,os,re,time,sys
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
FORMES=['10-K','10-Q','DEF 14A']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def url_document(cik,acc,doc):
 if not cik.isdigit() or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):raise ValueError('IDENTIFIANT_SEC_INVALIDE')
 if not doc or not re.fullmatch(r'[A-Za-z0-9_./-]+',doc) or doc.startswith('/') or '..' in PurePosixPath(doc).parts:raise ValueError('DOCUMENT_SEC_INVALIDE')
 return 'https://www.sec.gov/Archives/edgar/data/'+str(int(cik))+'/'+acc.replace('-','')+'/'+doc
def choisir(obj,limite):
 q=obj.get('filings',{}).get('recent',{});rows=[]
 for i,form in enumerate(q.get('form',[])):
  if form not in FORMES:continue
  try:
   date=q['filingDate'][i];datetime.strptime(date,'%Y-%m-%d')
   if date>limite:continue
   rows.append({'Formulaire':form,'Date_depot':date,'Accession':q['accessionNumber'][i],'Document_primaire':q['primaryDocument'][i]})
  except (KeyError,IndexError,ValueError,TypeError):continue
 return {f:max((r for r in rows if r['Formulaire']==f),key=lambda r:(r['Date_depot'],r['Accession']),default=None) for f in FORMES}
class RedirectionsSEC(HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  u=urlparse(newurl)
  if u.scheme!='https' or u.hostname not in ['www.sec.gov','sec.gov','data.sec.gov'] or u.username or u.password or u.port not in (None,443):raise ValueError('REDIRECTION_HORS_SEC')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def executer():
 agent=os.getenv('SEC_USER_AGENT','').strip()
 if '@' not in agent:raise RuntimeError('SEC_USER_AGENT_ABSENT_OU_INVALIDE')
 now=datetime.now(timezone.utc);limite=now.date().isoformat()
 candidats=sorted((BASE/'AUDITS/UNIVERS_US').glob('*/MANIFESTE.json'))
 if not candidats:raise RuntimeError('UNIVERS_US_ABSENT')
 mp=candidats[-1];m=json.loads(mp.read_text());p=mp.parent/'UNIVERS_US_PROVISOIRE.csv'
 if m['fichiers'].get(p.name)!=sha(p):raise RuntimeError('UNIVERS_US_CORROMPU')
 us=pd.read_csv(p,dtype=str,keep_default_na=False)
 if us.CIK.duplicated().any():raise RuntimeError('DOUBLON_EMETTEUR_US')
 out=BASE/'AUDITS/DOCUMENTS_US'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 cache={};rows=[];dernier=0.;opener=build_opener(RedirectionsSEC())
 for old in sorted((BASE/'AUDITS/DOCUMENTS_US').glob('*/AUDIT_DOCUMENTS.csv')):
  if old.parent==out:continue
  for r in pd.read_csv(old,dtype=str,keep_default_na=False).to_dict('records'):
   if r.get('Statut')=='DOCUMENT_COLLECTE_A_VERIFIER':cache[r['Source_URL']]=r
 for n,(_,r) in enumerate(us.iterrows(),1):
  src=BASE/r.Fichier_brut
  if sha(src)!=r.SHA256:raise RuntimeError('PROFIL_US_CORROMPU')
  obj=json.loads(src.read_text())
  if str(obj.get('cik','')).zfill(10)!=r.CIK:raise RuntimeError('CIK_PROFIL_US_INCOHERENT')
  choix=choisir(obj,limite)
  for form,selection in choix.items():
   row={'CIK':r.CIK,'Ticker_cotation':r.Ticker_cotation,'Nom_SEC':r.Nom_SEC,'Formulaire':form,
        'Statut_identite':'A_VERIFIER_COTATION_EMETTEUR','Notes_attribuees':0,'Source_profil':r.Fichier_brut,
        'Profil_SHA256':r.SHA256,'Date_profil_UTC':r.get('Date_source_UTC','')}
   if selection is None:
    row.update(Statut='DOCUMENT_NON_REFERENCE_DANS_INDEX');rows.append(row);continue
   row.update(selection)
   try:
    url=url_document(r.CIK,selection['Accession'],selection['Document_primaire']);row['Source_URL']=url
    if url in cache:
     c=cache[url];f=BASE/c['Fichier_brut']
     if sha(f)!=c['SHA256']:raise RuntimeError('DOCUMENT_US_CACHE_CORROMPU')
     data=f.read_bytes();date=c['Date_collecte_UTC'];ctype=c.get('Type_contenu','');final=c.get('URL_finale',url)
     row['Reutilise']='OUI'
    else:
     for essai in range(3):
      time.sleep(max(0,.3-(time.monotonic()-dernier)));dernier=time.monotonic()
      try:
       with opener.open(Request(url,headers={'User-Agent':agent,'Accept-Encoding':'identity'}),timeout=35) as response:
        data=response.read(30_000_001);ctype=response.headers.get('Content-Type','');final=response.geturl()
       break
      except HTTPError as exc:
       if exc.code not in (429,500,502,503,504) or essai==2:raise
       time.sleep(2*(essai+1))
     date=datetime.now(timezone.utc).isoformat();row['Reutilise']='NON'
    if not data or len(data)>30_000_000:raise ValueError('TAILLE_DOCUMENT_INVALIDE')
    if not data.startswith(b'%PDF') and '<html' not in data[:5000].decode('utf-8',errors='ignore').lower() and '<!doctype html' not in data[:5000].decode('utf-8',errors='ignore').lower():raise ValueError('DOCUMENT_PDF_HTML_ATTENDU')
    # Une page de refus HTTP 200 n'est pas un dépôt.
    titre=data[:8000].decode('utf-8',errors='ignore').lower()
    if any(t in titre for t in ['your request originates from an undeclared automated tool','request rate threshold exceeded','access denied']):raise ValueError('PAGE_REFUS_SEC')
    h=hashlib.sha256(data).hexdigest();f=out/(h+'.bin');f.write_bytes(data)
    row.update(Statut='DOCUMENT_COLLECTE_A_VERIFIER',SHA256=h,Fichier_brut=str(f.relative_to(BASE)),Date_collecte_UTC=date,
               Date_extraction_UTC=datetime.now(timezone.utc).isoformat(),Type_contenu=ctype,URL_finale=final)
   except Exception as exc:
    if 'CORROMPU' in str(exc):raise
    row.update(Statut='BLOQUE_SOURCE',Code_HTTP=getattr(exc,'code',''),Motif=type(exc).__name__)
   rows.append(row)
   # Point de reprise lisible même si une exécution est interrompue.
   pd.DataFrame(rows).to_csv(out/'AUDIT_DOCUMENTS.csv',index=False)
  print('Documents US:',n,'/',len(us),'émetteurs traités',flush=True)
 docs=pd.DataFrame(rows);docs.to_csv(out/'AUDIT_DOCUMENTS.csv',index=False)
 couverture=us[['CIK','Ticker_cotation','Nom_SEC','Statut_identite']].copy()
 for form in FORMES:
  ok=set(docs.loc[docs.Formulaire.eq(form)&docs.Statut.eq('DOCUMENT_COLLECTE_A_VERIFIER'),'CIK'])
  couverture[form]=couverture.CIK.isin(ok)
 couverture['Trois_documents_collectes']=couverture[FORMES].all(axis=1)
 couverture['SSI_evaluable']=False # Ce collecteur ne vérifie ni les notes ni le registre de preuves.
 couverture.to_csv(out/'COUVERTURE_DOCUMENTAIRE_US.csv',index=False)
 bilan={'date_utc':now.isoformat(),'date_limite':limite,'univers_source':str(p.relative_to(BASE)),'source_script_SHA256':sha(Path(__file__)),
  'emetteurs_US_provisoires':len(us),'documents_attendus':len(us)*len(FORMES),
  'documents_collectes':int(docs.Statut.eq('DOCUMENT_COLLECTE_A_VERIFIER').sum()),
  'sources_bloquees':int(docs.Statut.eq('BLOQUE_SOURCE').sum()),
  'emetteurs_trois_documents_collectes':int(couverture.Trois_documents_collectes.sum()),
  'notes_attribuees':0,'identites_validees_automatiquement':0,'qualification_SSI_effectuee':False,
  'statut':'DOCUMENTS_BRUTS_A_VERIFIER','fichiers':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(bilan,ensure_ascii=False))
 return bilan
if __name__=='__main__':
 result=executer()
 sys.exit(1 if result['sources_bloquees'] else 0)

"""Archive les pièces d'identité, détentions initiales/annuelles et le FX BCE.
Sélection sur les index SEC déjà archivés du lot, sans interprétation ni note.
"""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,build_opener
import gzip,hashlib,importlib.util,json,os,re,xml.etree.ElementTree as ET
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def charger(n):
 s=importlib.util.spec_from_file_location(n[:-3],BASE/'SCRIPTS_ACTIFS'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def choisir(depots,limite):
 rows=[r for r in depots if r['Date_depot']<=limite];extra=[]
 for form in ['3','3/A','5','5/A']:
  extra.extend(r for r in rows if r['Formulaire']==form and r['Date_depot']>='2026-01-01')
 g=[r for r in rows if r['Formulaire'] in ('SCHEDULE 13G','SCHEDULE 13G/A','SC 13G','SC 13G/A')]
 extra.extend(sorted(g,key=lambda r:(r['Date_depot'],r['Accession']),reverse=True)[:3])
 return list({r['Accession']:r for r in extra}.values())
def texte_xml(root,path):
 # namespace toléré, sans ignorer l'identité émetteur.
 for element in root.iter():
  if element.tag.split('}')[-1]==path:return (element.text or '').strip()
 return ''
def controler_ownership(data,cik):
 root=ET.fromstring(data)
 if root.tag.split('}')[-1]!='ownershipDocument':raise ValueError('DOCUMENT_OWNERSHIP_ATTENDU')
 issuer=texte_xml(root,'issuerCik')
 if not issuer.isdigit() or int(issuer)!=int(cik):raise ValueError('CIK_OWNERSHIP_DIVERGENT')
 return texte_xml(root,'documentType'),texte_xml(root,'periodOfReport')
def executer():
 now=datetime.now(timezone.utc);cutoff=now.date().isoformat();mp=sorted((BASE/'AUDITS/RELECTURE_INITIES_US').glob('*/MANIFESTE.json'))[-1];meta=json.loads(mp.read_text())
 if meta.get('profils_en_erreur') or any(k!='TRANSACTIONS_A_VERIFIER' for k in meta['repartition_controles']):raise RuntimeError('SOURCE_LOT_INCOMPLETE')
 src=mp.parent/'BRUTS/SOURCES_HTTP.json'
 if meta['fichiers'].get('BRUTS/SOURCES_HTTP.json')!=sha(src):raise RuntimeError('INDEX_HTTP_CORROMPU')
 http=json.loads(src.read_text());profiles={r['URL']:r for r in http if r['URL'].startswith('https://data.sec.gov/submissions/CIK') and not '-submissions-' in r['URL']}
 lot=pd.read_csv(mp.parent/'PROFILS_ACTUALISES.csv',dtype=str,keep_default_na=False)
 if sha(mp.parent/'PROFILS_ACTUALISES.csv')!=meta['fichiers']['PROFILS_ACTUALISES.csv']:raise RuntimeError('PROFILS_LOT_CORROMPUS')
 out=BASE/'AUDITS/COMPLEMENTS_QUALIFICATION_US'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False);(out/'BRUTS').mkdir()
 ap=charger('07AP_RELECTURE_INITIES_LOT_US.py');af=charger('07AF_COLLECTER_DOCUMENTS_US.py');g=charger('07AO_PASSAGES_GOUVERNANCE_US.py');client=ap.ClientSEC(out/'BRUTS',os.getenv('SEC_USER_AGENT',''))
 rows=[]
 for _,r in lot.iterrows():
  source=profiles[r.Source_URL];p=BASE/source['Fichier_brut']
  if sha(p)!=source['SHA256_archive'] or hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()!=source['SHA256_brut']:raise RuntimeError('PROFIL_SOURCE_CORROMPU')
  if source['Date_collecte_UTC'][:10]!=cutoff:raise RuntimeError('ACTUALISER_PROFILS_AVANT_COMPLEMENTS')
  obj=json.loads(gzip.decompress(p.read_bytes()));dep=ap.depots(obj,cutoff);choix=choisir(dep,cutoff)
  # Le certificat a été repéré dans l'annuel SEC 2026 (exhibit 4.1), pas deviné.
  if r.Ticker=='CCFN.US':
   q=max((d for d in dep if d['Formulaire']=='10-K'),key=lambda d:d['Date_depot']);choix.append(dict(q,Formulaire='EXHIBIT_4_1_CERTIFICAT',Document_primaire='ex4-1.htm'))
  for q in choix:
   url=af.url_document(r.CIK,q['Accession'],Path(q['Document_primaire']).name);row={'Ticker':r.Ticker,'CIK':r.CIK,**q,'Source_URL':url}
   try:
    with client.open(Request(url)) as response:data=response.read()
    if q['Formulaire'] in ['3','3/A','5','5/A']:
     form,period=controler_ownership(data,r.CIK);row.update(Type_XML=form,Date_periode_XML=period)
     if period and period>cutoff:raise ValueError('PERIODE_OWNERSHIP_FUTURE')
    source=client.sources[-1];text=g.texte_brut(data);p=out/(r.CIK+'_'+q['Accession']+'_'+q['Formulaire'].replace('/','_').replace(' ','_')+'.txt.gz');p.write_bytes(gzip.compress(text.encode(),mtime=0))
    row.update(Statut='DOCUMENT_COLLECTE_A_RELIRE',Fichier_brut=source['Fichier_brut'],SHA256_archive=source['SHA256_archive'],SHA256_brut=source['SHA256_brut'],Texte_normalise=str(p.relative_to(BASE)),Date_collecte_UTC=source['Date_collecte_UTC'])
   except Exception as exc:row.update(Statut='BLOQUE_SOURCE',Motif=type(exc).__name__+': '+str(exc))
   rows.append(row)
  print('Compléments SEC : '+r.Ticker+' — '+str(len(choix))+' références',flush=True)
 # FX officiel indépendant des archives fournisseur. Le cours n'est pas un taux d'exécution.
 aa=charger('07AA_COLLECTE_DOCUMENTS_OFFICIELS.py');url='https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml';aa.verifier_url(url,{'www.ecb.europa.eu'})
 with build_opener(aa.Redirections({'www.ecb.europa.eu'})).open(Request(url,headers={'User-Agent':'MICRO_CAPS document research'}),timeout=35) as response:data=response.read(100000)
 root=ET.fromstring(data);rates=[]
 for cube in root.iter():
  if 'time' in cube.attrib:
   date=cube.attrib['time']
   if date>cutoff:raise RuntimeError('FX_BCE_FUTUR')
   for x in cube:
    if x.attrib.get('currency')=='USD':rates.append({'Date_FX':date,'EURUSD':x.attrib['rate'],'Source_URL':url})
 if len(rates)!=1:raise RuntimeError('FX_USD_BCE_AMBIGU')
 p=out/'BCE_FX.xml.gz';p.write_bytes(gzip.compress(data,mtime=0));rates[0].update(Fichier_brut=str(p.relative_to(BASE)),SHA256_archive=sha(p));pd.DataFrame(rates).to_csv(out/'FX_BCE.csv',index=False)
 pd.DataFrame(rows).to_csv(out/'DOCUMENTS_COMPLEMENTAIRES.csv',index=False)
 bilan={'date_UTC':now.isoformat(),'source_lot':str(mp.relative_to(BASE)),'source_lot_SHA256':sha(mp),'documents_configures':len(rows),'documents_collectes':sum(r['Statut']=='DOCUMENT_COLLECTE_A_RELIRE' for r in rows),'sources_bloquees':sum(r['Statut']=='BLOQUE_SOURCE' for r in rows),'FX_BCE_date':rates[0]['Date_FX'],'notes_attribuees':0,'detentions_actuelles_validees':False,'fichiers':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(bilan,ensure_ascii=False));return bilan
if __name__=='__main__':
 r=executer()
 if r['sources_bloquees']:raise SystemExit(1)

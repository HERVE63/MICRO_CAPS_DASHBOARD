"""Orchestration SEC isolée et archivée ; aucun dossier ni portefeuille n'est modifié.
Le secret n'est jamais écrit. Les réponses brutes sont conservées avec SHA256.
Une exécution bloquée produit aussi un manifeste ; elle n'est pas une collecte réussie.
"""
from pathlib import Path
from datetime import datetime, timezone
from io import BytesIO
import hashlib, importlib.util, json, os, re, shutil, subprocess, sys, time
from urllib.request import urlopen
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
MODULES=['07T_ENRICHIR_PREUVES_SEC_EDGAR.py','07U_COLLECTE_COMPANYFACTS_SEC.py',
         '07V_NORMALISER_FAITS_SEC.py','07W_RAPPROCHER_PREUVES_SEC_SSI.py',
         '07X_INDEX_GOUVERNANCE_SEC.py','07Y_EXTRAIRE_FORM4_SEC.py']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def commit_effectif():
 try:return subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True,stderr=subprocess.DEVNULL).strip()
 except subprocess.CalledProcessError:return 'INCONNU_HORS_DEPOT'
def protections():
 return {str(p.relative_to(BASE)):sha(p) for folder in ['DONNEES','SAUVEGARDES']
         for p in (BASE/folder).rglob('*') if p.is_file()}
class Reponse(BytesIO):
 def __enter__(self): return self
 def __exit__(self,*args): self.close()
def executer():
 debut=datetime.now(timezone.utc)
 run=os.getenv('GITHUB_RUN_ID',debut.strftime('%Y%m%dT%H%M%S%fZ'))
 archive=BASE/'AUDITS/SEC'/('RUN_'+run+'_'+os.getenv('GITHUB_RUN_ATTEMPT','1'))
 archive.mkdir(parents=True,exist_ok=False)
 travail=archive/'DONNEES';travail.mkdir()
 bruts=archive/'BRUTS';bruts.mkdir()
 avant=protections()
 manifest={'date_utc':debut.isoformat(),'date_limite':debut.date().isoformat(),
           'commit':commit_effectif(),
           'commit_declencheur':os.getenv('GITHUB_SHA',''),
           'statut':'EN_COURS','etapes':[],'notes_attribuees':0,'secret_contact_valide':False,
           'portefeuilles_modifies':False,'collecte_exhaustive':False}
 requetes=[];dernier=[0.0];cache={}
 # Réutilisation uniquement des réponses du même jour UTC, sans supprimer les archives.
 # Chaque réponse est recontrôlée par SHA256 avant lecture.
 def charger_cache():
  for index in sorted((BASE/'AUDITS/SEC').glob('RUN_*/SOURCES_BRUTES.json')):
   for source in json.loads(index.read_text()):
    date=datetime.fromisoformat(source['date_collecte_utc'])
    if date.date()==debut.date() and date<=debut:
     cache[source['url']]=(index.parent/'BRUTS'/(source['sha256']+'.bin'),source)
 def collecter(req,timeout=25):
  # Un plafond global de 4 requêtes/seconde, y compris les XML.
  url=req.full_url
  if not re.match(r'^https://(?:www\.sec\.gov|data\.sec\.gov)/',url):
   raise ValueError('Source hors SEC')
  if url in cache:
   chemin,source=cache[url]
   if not chemin.exists() or sha(chemin)!=source['sha256']:
    raise ValueError('CACHE_SEC_INTEGRITE_INVALIDE')
   data=chemin.read_bytes();(bruts/(source['sha256']+'.bin')).write_bytes(data)
   requetes.append(dict(source,archive_cache=str(chemin.parent.parent.relative_to(BASE)),
                        date_relecture_utc=datetime.now(timezone.utc).isoformat()))
   return Reponse(data)
  time.sleep(max(0,.25-(time.monotonic()-dernier[0])))
  dernier[0]=time.monotonic()
  with urlopen(req,timeout=timeout) as resp: data=resp.read()
  digest=hashlib.sha256(data).hexdigest();(bruts/(digest+'.bin')).write_bytes(data)
  requetes.append({'url':url,'sha256':digest,'date_collecte_utc':datetime.now(timezone.utc).isoformat()})
  return Reponse(data)
 try:
  charger_cache()
  for n in ['DOSSIERS_SSI_A_QUALIFIER.csv','UNIVERS_INVESTISSABLE_MICRO_CAPS.csv']:
   shutil.copy2(BASE/'DONNEES'/n,travail/n)
  # Périmètre de qualification figé : les dossiers retenus, sans nouvelle chasse.
  u=pd.read_csv(travail/'DOSSIERS_SSI_A_QUALIFIER.csv',dtype=str,keep_default_na=False)
  manifest['univers_collecte']=len(u)
  agent=os.getenv('SEC_USER_AGENT','').strip()
  if not agent or '@' not in agent: raise RuntimeError('SEC_USER_AGENT_ABSENT_OU_INVALIDE')
  manifest['secret_contact_valide']=True
  # Lot technique déterministe : pas de présélection économique.
  # Le pays de cotation ne prouve pas le domicile de l'émetteur.
  # 07T découvre les pistes dans le registre officiel et limite les appels par ticker.
  limite=int(os.getenv('SEC_BATCH_SIZE','100'))
  if limite<=0: raise RuntimeError('SEC_BATCH_SIZE_INVALIDE')
  offset=int(os.getenv('SEC_BATCH_OFFSET','0'))
  if offset<0: raise RuntimeError('SEC_BATCH_OFFSET_INVALIDE')
  u.to_csv(travail/'UNIVERS_SEC_LOT.csv',index=False)
  manifest.update({'offset_pistes_SEC':offset,'taille_max_lot_SEC':limite})
  for name in MODULES:
   print('SEC : démarrage '+name,flush=True)
   spec=importlib.util.spec_from_file_location(name[:-3],BASE/'SCRIPTS_ACTIFS'/name)
   mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
   mod.D=travail
   for attr in ['SRC','OUT','AUD','DOS','SEC','FACT']:
    if hasattr(mod,attr): setattr(mod,attr,travail/getattr(mod,attr).name)
   if name.startswith('07T_'): mod.SRC=travail/'UNIVERS_SEC_LOT.csv'
   if hasattr(mod,'urlopen'): mod.urlopen=collecter
   mod.executer()
   manifest['etapes'].append({'module':name,'statut':'EXECUTE'})
  sec=pd.read_csv(travail/'PREUVES_SEC_EDGAR_SSI.csv',keep_default_na=False)
  manifest['statuts_SEC']=sec.Statut_SEC.value_counts().to_dict()
  audit=pd.read_csv(travail/'AUDIT_PREUVES_SEC_SSI.csv',keep_default_na=False).iloc[0]
  manifest['pistes_SEC_uniques']=int(audit['Pistes_uniques'])
  manifest['pistes_SEC_dans_lot']=int(audit['Pistes_dans_lot'])
  manifest['pistes_SEC_hors_lot']=int(sec.Statut_SEC.eq('PISTE_SEC_HORS_LOT').sum())
  errors=sec.Statut_SEC.eq('ERREUR_SOURCE').sum()
  for n in ['AUDIT_FAITS_FINANCIERS_SEC_SSI.csv','AUDIT_TRANSACTIONS_DIRIGEANTS_SEC_SSI.csv']:
   a=pd.read_csv(travail/n,keep_default_na=False)
   if 'Statut' in a: errors+=a.Statut.str.startswith('ERREUR').sum()
  manifest['erreurs_sources']=int(errors)
  manifest['statut']='COLLECTE_PARTIELLE_ERREURS_SOURCE' if errors else 'LOT_COLLECTE_A_VERIFIER'
 except Exception as exc:
  manifest['statut']='BLOQUE';manifest['blocage']=str(exc)
 finally:
  apres=protections()
  differences=sorted(k for k in set(avant)|set(apres) if avant.get(k)!=apres.get(k))
  manifest['integrite_entrees']='OK' if not differences else 'ECHEC'
  manifest['fichiers_entrees_modifies']=differences
  manifest['reponses_reutilisees']=sum('archive_cache' in s for s in requetes)
  manifest['reponses_reseau']=sum('archive_cache' not in s for s in requetes)
  manifest['fin_utc']=datetime.now(timezone.utc).isoformat()
  manifest['fichiers']={str(p.relative_to(archive)):sha(p) for p in archive.rglob('*') if p.is_file()}
  (archive/'SOURCES_BRUTES.json').write_text(json.dumps(requetes,ensure_ascii=False,indent=2)+'\n')
  (archive/'MANIFESTE.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(manifest,ensure_ascii=False,indent=2),flush=True)
 return 0 if manifest['statut']=='LOT_COLLECTE_A_VERIFIER' and not differences else 1
if __name__=='__main__':sys.exit(executer())

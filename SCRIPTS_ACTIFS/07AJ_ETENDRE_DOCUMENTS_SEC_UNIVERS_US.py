"""Raccorde tous les profils SEC du recensement EODHD aux collecteurs existants.

Pas de retour au pilote de 172 titres ni de présélection financière. Les profils
sont déchiffrés seulement après contrôle d'empreinte ; seules les sources SEC
sont publiées. Les origines inconnues restent visibles, sans admission SSI.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os
import pandas as pd

BASE=Path(__file__).resolve().parents[1]
def charger(nom):
 s=importlib.util.spec_from_file_location(nom[:-3],BASE/'SCRIPTS_ACTIFS'/nom)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def preparer(source,cle,dechiffrer):
 source=Path(source);m=json.loads((source/'MANIFESTE.json').read_text())
 if not m.get('recensement_termine'):raise RuntimeError('RECENSEMENT_INCOMPLET')
 util=charger('07AI_RACCORDER_COMPTES_US_SSI.py')
 index=json.loads(util.verifier_fichier(source,m,'INDEX_REQUETES.json').read_text())
 f=util.verifier_fichier(source,m,'COUVERTURE_PREUVES_SEC.csv')
 candidats=pd.read_csv(f,dtype=str,keep_default_na=False)
 if candidats.Ticker_US.duplicated().any():raise RuntimeError('TICKERS_RECENSEMENT_DUPLIQUES')
 profils={}
 for r in index:
  route=r.get('route','')
  if route.startswith('SEC:https://data.sec.gov/submissions/CIK'):
   profils[route[4:]]=r
 out=BASE/'AUDITS/PROFILS_SEC_UNIVERS_US'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out.mkdir(parents=True,exist_ok=False);rows=[];anomalies=[]
 for cik,group in candidats[candidats.CIK.ne('')].groupby('CIK',sort=True):
  url='https://data.sec.gov/submissions/CIK'+cik+'.json'
  if url not in profils:
   anomalies.append({'CIK':cik,'Statut':'PROFIL_ARCHIVE_ABSENT'});continue
  r=profils[url];p=util.verifier_fichier(source,m,r['archive_chiffree'])
  raw=dechiffrer(json.loads(p.read_text()),cle);obj=json.loads(raw)
  if str(obj.get('cik','')).zfill(10)!=cik:
   anomalies.append({'CIK':cik,'Statut':'CIK_PROFIL_INCOHERENT'});continue
  fp=out/('CIK'+cik+'.json');fp.write_bytes(raw)
  # Toutes les cotations sont conservées dans la liste, même si plusieurs classes
  # partagent le même émetteur et donc les mêmes documents.
  rows.append({'CIK':cik,'Ticker_cotation':group.iloc[0]['Ticker_US'],
    'Tickers_recenses':'|'.join(sorted(group.Ticker_US)), 'Nb_cotations':len(group),
    'Nom_SEC':obj.get('name',''),'Statut_origine':group.iloc[0]['Statut_origine'],
    'Statut_identite':'COTATION_ET_TYPE_INSTRUMENT_A_VERIFIER',
    'Fichier_brut':str(fp.relative_to(BASE)),'SHA256':sha(fp),
    'Date_source_UTC':r['date_collecte_utc'],'Source_URL':url})
 table=pd.DataFrame(rows)
 if table.empty:raise RuntimeError('AUCUN_PROFIL_RESOLU')
 table.to_csv(out/'UNIVERS_SEC_COTATIONS_US.csv',index=False)
 pd.DataFrame(anomalies,columns=['CIK','Statut']).to_csv(out/'ANOMALIES_PROFILS.csv',index=False)
 # Le tableau intégral reste la référence du dénominateur : absence de profil
 # ou de document ne devient pas un rejet pour mauvaise qualité financière.
 candidats.to_csv(out/'TOUTES_COTATIONS_RECENSEES.csv',index=False)
 bilan={'date_utc':datetime.now(timezone.utc).isoformat(),'source_recensement':str(source.relative_to(BASE)),
  'source_manifeste_SHA256':sha(source/'MANIFESTE.json'),'source_script_SHA256':sha(Path(__file__)),
  'cotations_recensees':len(candidats),'profils_distincts_prepares':len(table),
  'cotations_avec_profil':int(table.Nb_cotations.sum()),'anomalies_identite':len(anomalies),
  'origines':table.Statut_origine.value_counts().to_dict(),'notes_SSI_attribuees':0,
  'statut':'PROFILS_SEC_PREPARES_DOCUMENTS_ET_IDENTITES_A_VERIFIER',
  'fichiers':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(bilan,ensure_ascii=False));return out/'UNIVERS_SEC_COTATIONS_US.csv'

def executer():
 cle=os.getenv('EODHD_API_KEY','').strip()
 if not cle:raise RuntimeError('CLE_ARCHIVES_ABSENTE')
 sources=sorted((BASE/'AUDITS/RECENSEMENT_US_EODHD').glob('*/MANIFESTE.json'))
 if not sources:raise RuntimeError('RECENSEMENT_ABSENT')
 eod=charger('07AH_RECENSER_MICROCAPS_US_EODHD.py')
 univers=preparer(sources[-1].parent,cle,eod.dechiffrer)
 docs=charger('07AF_COLLECTER_DOCUMENTS_US.py')
 bilan=docs.executer(univers_source=univers,compression=True)
 controle=charger('07AG_CONTROLER_DOCUMENTS_US.py').executer()
 if bilan['sources_bloquees'] or controle['repartition_controles'].get('CIK_XBRL_DIVERGENT',0):
  raise RuntimeError('PREUVES_DOCUMENTAIRES_PARTIELLES_OU_IDENTITES_A_RESOUDRE')
 return bilan

if __name__=='__main__':executer()

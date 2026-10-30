"""Consolide les archives vérifiées sans effacer leurs bruts ni valider de scores."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from decimal import Decimal,InvalidOperation
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
KEYS=['Ticker','CIK','Taxonomie_SEC','Concept','Tag_SEC','Unite','Debut_periode','Fin_periode','Date_depot','Accession']
def empreinte(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cik_normalise(v):
 s=str(v).strip()
 return str(int(s)).zfill(10) if s.isdigit() else ''
def verifier_manifest_consolidation(dossier):
 dossier=Path(dossier)
 manifeste=json.loads((dossier/'MANIFESTE.json').read_text())
 attendu=manifeste.get('fichiers_sha256',{})
 if set(attendu)!={'FAITS_SEC_BRUTS_CONSOLIDES.csv','COUVERTURE.csv','COUVERTURE_TITULAIRES.csv'}:
  raise RuntimeError('MANIFESTE_CONSOLIDATION_INCOMPLET')
 for nom,sha in attendu.items():
  p=dossier/nom
  if not p.is_file() or empreinte(p)!=sha:raise RuntimeError('SORTIE_CONSOLIDATION_SHA256_DIVERGENT:'+nom)
 return manifeste
def valeur_comparable(v):
 try:
  n=Decimal(str(v))
  if n.is_finite():return format(n.normalize(),'f')
 except InvalidOperation:pass
 raise RuntimeError('VALEUR_SEC_NON_NUMERIQUE')
def verifier_chronologie_sec(faits, reference_utc=None):
 """Contrôle les dates de chaque observation sans supprimer les bruts ni inventer de preuve.

 Debut_periode facultatif (concept SEC instantané) ; fin de période et date
 de dépôt indispensables pour exploiter chronologiquement un fait.
 """
 reference=pd.Timestamp(reference_utc) if reference_utc is not None else pd.Timestamp.now(tz='UTC')
 if reference.tzinfo is None:raise ValueError('REFERENCE_UTC_SANS_FUSEAU')
 reference=reference.tz_convert('UTC').normalize().tz_localize(None)
 debut=faits['Debut_periode'].astype(str).str.strip()
 fin=faits['Fin_periode'].astype(str).str.strip()
 depot=faits['Date_depot'].astype(str).str.strip()
 d0=pd.to_datetime(debut,format='%Y-%m-%d',errors='coerce')
 d1=pd.to_datetime(fin,format='%Y-%m-%d',errors='coerce')
 d2=pd.to_datetime(depot,format='%Y-%m-%d',errors='coerce')
 statut=pd.Series('OK',index=faits.index,dtype=object)
 def marquer(masque,motif):
  statut.loc[masque & statut.eq('OK')]=motif
 marquer(fin.eq('') | depot.eq(''),'DATE_OBLIGATOIRE_ABSENTE')
 marquer((debut.ne('') & d0.isna()) | (fin.ne('') & d1.isna()) | (depot.ne('') & d2.isna()),'FORMAT_DATE_INVALIDE')
 marquer(debut.ne('') & d0.gt(d1),'PERIODE_INVERSEE')
 marquer(d2.lt(d1),'DEPOT_AVANT_FIN_PERIODE')
 marquer(d2.gt(reference),'DEPOT_POSTERIEUR_REFERENCE')
 return statut

def executer():
 scope=pd.read_csv(BASE/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv',dtype=str,keep_default_na=False)
 if scope.Ticker.duplicated().any():raise RuntimeError('DOUBLON_DOSSIER')
 scope=scope[['Ticker','Societe','Pays']].copy()
 scope['Origine']='CANDIDAT_SSI'
 titulaires=pd.DataFrame(columns=['ID_position','Ticker','Societe','Pays'])
 cohorte=BASE/'DONNEES/COHORTE_MICRO_CAPS_T0.csv'
 if cohorte.exists():
  c=pd.read_csv(cohorte,dtype=str,keep_default_na=False,encoding='utf-8-sig')
  champs={'ID_ligne','Ticker_cotation','Societe','Pays'}
  if not champs.issubset(c.columns) or len(c)!=40 or c.ID_ligne.duplicated().any() or c.Ticker_cotation.duplicated().any():
   raise RuntimeError('COHORTE_T0_40_INVALIDE')
  titulaires=c[['ID_ligne','Ticker_cotation','Societe','Pays']].rename(columns={'ID_ligne':'ID_position','Ticker_cotation':'Ticker'}).copy()
  if titulaires.Ticker.str.strip().eq('').any():raise RuntimeError('TICKER_TITULAIRE_ABSENT')
  # La seule normalisation explicite est le suffixe .US des archives SEC ;
  # aucun rapprochement approximatif de noms ou de places de cotation.
  titulaires.loc[titulaires.Pays.eq('USA'),'Ticker']=titulaires.loc[titulaires.Pays.eq('USA'),'Ticker'].map(lambda x:x if x.endswith('.US') else x+'.US')
  if titulaires.Ticker.duplicated().any():raise RuntimeError('TICKER_TITULAIRE_AMBIGU')
  t=titulaires[['Ticker','Societe','Pays']].copy();t['Origine']='TITULAIRE'
  scope=pd.concat([scope,t],ignore_index=True)
  scope=scope.groupby('Ticker',as_index=False,sort=False).agg({'Societe':'first','Pays':'first','Origine':lambda x:'|'.join(sorted(set(x)))})
 lignes=[];archives=[];identites={}
 for p in sorted((BASE/'AUDITS/SEC').glob('RUN_*/MANIFESTE.json')):
  manifest=json.loads(p.read_text());src=p.parent/'DONNEES/FAITS_FINANCIERS_SEC_SSI.csv'
  if not src.exists():continue
  rel=str(src.relative_to(p.parent))
  if manifest.get('fichiers',{}).get(rel)!=empreinte(src):raise RuntimeError('ARCHIVE_SEC_SHA256_DIVERGENT: '+str(src.relative_to(BASE)))
  d=pd.read_csv(src,dtype=str,keep_default_na=False)
  if 'Taxonomie_SEC' not in d:d['Taxonomie_SEC']='us-gaap'
  if not set(KEYS).issubset(d.columns):raise RuntimeError('SCHEMA_ARCHIVE_SEC_INCOMPLET')
  d=d[d.Ticker.isin(scope.Ticker)].copy()
  if not d.empty:
   d['Archive_source']=str(p.parent.relative_to(BASE));lignes.append(d)
  # Les pistes sans fait financier restent visibles dans la couverture.
  idx=p.parent/'DONNEES/PREUVES_SEC_EDGAR_SSI.csv'
  if idx.exists():
   if manifest.get('fichiers',{}).get(str(idx.relative_to(p.parent)))!=empreinte(idx):raise RuntimeError('INDEX_SEC_SHA256_DIVERGENT')
   s=pd.read_csv(idx,dtype=str,keep_default_na=False)
   for _,r in s.iterrows():
    if r.Ticker in set(scope.Ticker) and str(r.get('CIK','')).isdigit():
     identites.setdefault(r.Ticker,set()).add(cik_normalise(r.CIK))
  archives.append(str(p.parent.relative_to(BASE)))
 # Archives historiques US du module 07U/07V/07W : reutiliser les BRUTS SEC
 # et leur index de couverture sans promouvoir une piste en preuve validee.
 archives_qualification=[]
 for p in sorted((BASE/'AUDITS/QUALIFICATION_US').glob('*/MANIFESTE.json')):
  manifest=json.loads(p.read_text())
  fichiers=manifest.get('fichiers',{})
  cover=p.parent/'COUVERTURE_QUALIFICATION_US.csv'
  bruts=p.parent/'BRUTS.csv.gz'
  for fichier in (cover,bruts):
   if not fichier.is_file() or fichiers.get(fichier.name)!=empreinte(fichier):
    raise RuntimeError('ARCHIVE_QUALIFICATION_US_SHA256_DIVERGENT: '+str(fichier.relative_to(BASE)))
  index_us=pd.read_csv(cover,dtype=str,keep_default_na=False)
  if not {'Ticker_US','CIK'}.issubset(index_us.columns) or index_us.Ticker_US.duplicated().any():
   raise RuntimeError('INDEX_QUALIFICATION_US_INVALIDE')
  scope_us=set(scope.Ticker)
  for _,r in index_us[index_us.Ticker_US.isin(scope_us)].iterrows():
   if str(r.CIK).isdigit():
    identites.setdefault(r.Ticker_US,set()).add(cik_normalise(r.CIK))
  for bloc in pd.read_csv(bruts,compression='gzip',dtype=str,keep_default_na=False,chunksize=100000):
   if 'Taxonomie_SEC' not in bloc:bloc['Taxonomie_SEC']='us-gaap'
   if not set(KEYS+['Valeur']).issubset(bloc.columns):
    raise RuntimeError('SCHEMA_BRUTS_QUALIFICATION_US_INCOMPLET')
   subset=bloc[bloc.Ticker.isin(scope_us)].copy()
   if not subset.empty:
    subset['Archive_source']=str(p.parent.relative_to(BASE))
    lignes.append(subset)
  archives_qualification.append(str(p.parent.relative_to(BASE)))
 faits=pd.concat(lignes,ignore_index=True) if lignes else pd.DataFrame(columns=KEYS+['Valeur','Archive_source'])
 conflits=pd.Series(dtype=int)
 # Une même observation peut figurer dans plusieurs archives ; aucune provenance n'est perdue.
 if not faits.empty:
  # Les CIK présents dans les faits sont des pistes indépendantes des index.
  # Un index et un fait portant des CIK différents doivent être signalés.
  for ticker,cik in faits[['Ticker','CIK']].itertuples(index=False,name=None):
   normalise=cik_normalise(cik)
   if normalise:identites.setdefault(ticker,set()).add(normalise)
  faits['Valeur_comparable']=faits.Valeur.map(valeur_comparable)
  versions=KEYS+['Valeur_comparable']
  provenance=faits.groupby(versions,dropna=False)['Archive_source'].agg(lambda x:'|'.join(sorted(set(x)))).reset_index(name='Archives_sources')
  representations=faits.groupby(versions,dropna=False)['Valeur'].agg(lambda x:'|'.join(sorted(set(x)))).reset_index(name='Representations_brutes')
  conflits=faits.groupby(KEYS,dropna=False).Valeur_comparable.nunique()
  ambigues={k for k,n in conflits.items() if n>1}
  faits=faits.drop_duplicates(versions).drop(columns='Archive_source').merge(provenance,on=versions,validate='one_to_one').merge(representations,on=versions,validate='one_to_one')
  faits['Statut_observation']=faits.apply(lambda r:'VALEURS_DIVERGENTES_A_RELIRE' if tuple(r[k] for k in KEYS) in ambigues else 'BRUT_A_VERIFIER',axis=1)
  faits['Statut_chronologie']=verifier_chronologie_sec(faits)
 couverture=scope[['Ticker','Societe','Pays']].copy()
 counts=faits.groupby('Ticker').size() if not faits.empty else pd.Series(dtype=int)
 couverture['Nb_faits_bruts']=couverture.Ticker.map(counts).fillna(0).astype(int)
 utilisables=faits.loc[faits.Statut_chronologie.eq('OK')].groupby('Ticker').size() if not faits.empty else pd.Series(dtype=int)
 couverture['Nb_faits_chronologie_OK']=couverture.Ticker.map(utilisables).fillna(0).astype(int)
 couverture['CIK_pistes']=couverture.Ticker.map(lambda t:'|'.join(sorted(identites.get(t,set()))))
 couverture['Statut_identite']=couverture.Ticker.map(lambda t:'IDENTITE_DIVERGENTE_A_RELIRE' if len(identites.get(t,set()))>1 else 'A_VERIFIER')
 couverture_titulaires=titulaires[['ID_position','Ticker','Societe','Pays']].merge(
  couverture[['Ticker','Nb_faits_bruts','Nb_faits_chronologie_OK','CIK_pistes','Statut_identite']],on='Ticker',how='left',validate='one_to_one')
 if len(titulaires) and (len(couverture_titulaires)!=40 or couverture_titulaires.Nb_faits_bruts.isna().any()):
  raise RuntimeError('COUVERTURE_TITULAIRES_INCOMPLETE')
 couverture_titulaires['Statut_SSI']='EN_ATTENTE_DATA'
 couverture_titulaires['Statut_MCPA']='EN_ATTENTE_DATA'
 out=BASE/'AUDITS/SEC_CONSOLIDE'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 faits.to_csv(out/'FAITS_SEC_BRUTS_CONSOLIDES.csv',index=False)
 couverture.to_csv(out/'COUVERTURE.csv',index=False)
 couverture_titulaires.to_csv(out/'COUVERTURE_TITULAIRES.csv',index=False)
 bilan={'archives_controlees':len(archives),'archives_qualification_us_controlees':len(archives_qualification),'archives_sources':archives+archives_qualification,'observations_brutes_distinctes':len(faits),
        'dossiers_avec_faits':int(couverture.Nb_faits_bruts.gt(0).sum()),'dossiers':len(scope),
        'observations_valeurs_divergentes':int(conflits.gt(1).sum()),
        'observations_chronologie_non_validee':int(faits.Statut_chronologie.ne('OK').sum()) if not faits.empty else 0,
        'notes_attribuees':0,'identites_validees_automatiquement':0,
        'titulaires_couverts':len(couverture_titulaires),
        'titulaires_avec_pistes_SEC':int(couverture_titulaires.Nb_faits_bruts.gt(0).sum()) if len(couverture_titulaires) else 0,'statut':'BRUTS_CONSOLIDES_A_VERIFIER'}
 bilan['fichiers_sha256']={p.name:empreinte(p) for p in out.iterdir() if p.is_file()}
 bilan['manifestes_sources_sha256']={str((BASE/rel/'MANIFESTE.json').relative_to(BASE)):empreinte(BASE/rel/'MANIFESTE.json') for rel in archives+archives_qualification}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
 verifier_manifest_consolidation(out)
 print(json.dumps({k:v for k,v in bilan.items() if k!='archives_sources'},ensure_ascii=False),flush=True)
 return bilan
if __name__=='__main__':executer()

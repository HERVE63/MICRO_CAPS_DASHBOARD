"""Consolide les archives vérifiées sans effacer leurs bruts ni valider de scores."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
KEYS=['Ticker','CIK','Taxonomie_SEC','Concept','Tag_SEC','Unite','Debut_periode','Fin_periode','Date_depot','Accession']
def empreinte(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def executer():
 scope=pd.read_csv(BASE/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv',dtype=str,keep_default_na=False)
 if scope.Ticker.duplicated().any():raise RuntimeError('DOUBLON_DOSSIER')
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
     identites.setdefault(r.Ticker,set()).add(r.CIK)
  archives.append(str(p.parent.relative_to(BASE)))
 faits=pd.concat(lignes,ignore_index=True) if lignes else pd.DataFrame(columns=KEYS+['Valeur','Archive_source'])
 conflits=pd.Series(dtype=int)
 # Une même observation peut figurer dans plusieurs archives ; aucune provenance n'est perdue.
 if not faits.empty:
  versions=KEYS+['Valeur']
  provenance=faits.groupby(versions,dropna=False)['Archive_source'].agg(lambda x:'|'.join(sorted(set(x)))).reset_index(name='Archives_sources')
  conflits=faits.groupby(KEYS,dropna=False).Valeur.nunique()
  ambigues={k for k,n in conflits.items() if n>1}
  faits=faits.drop_duplicates(versions).drop(columns='Archive_source').merge(provenance,on=versions,validate='one_to_one')
  faits['Statut_observation']=faits.apply(lambda r:'VALEURS_DIVERGENTES_A_RELIRE' if tuple(r[k] for k in KEYS) in ambigues else 'BRUT_A_VERIFIER',axis=1)
 couverture=scope[['Ticker','Societe','Pays']].copy()
 counts=faits.groupby('Ticker').size() if not faits.empty else pd.Series(dtype=int)
 couverture['Nb_faits_bruts']=couverture.Ticker.map(counts).fillna(0).astype(int)
 couverture['CIK_pistes']=couverture.Ticker.map(lambda t:'|'.join(sorted(identites.get(t,set()))))
 couverture['Statut_identite']=couverture.Ticker.map(lambda t:'IDENTITE_DIVERGENTE_A_RELIRE' if len(identites.get(t,set()))>1 else 'A_VERIFIER')
 out=BASE/'AUDITS/SEC_CONSOLIDE'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 faits.to_csv(out/'FAITS_SEC_BRUTS_CONSOLIDES.csv',index=False)
 couverture.to_csv(out/'COUVERTURE.csv',index=False)
 bilan={'archives_controlees':len(archives),'archives_sources':archives,'observations_brutes_distinctes':len(faits),
        'dossiers_avec_faits':int(couverture.Nb_faits_bruts.gt(0).sum()),'dossiers':len(scope),
        'observations_valeurs_divergentes':int(conflits.gt(1).sum()),
        'notes_attribuees':0,'identites_validees_automatiquement':0,'statut':'BRUTS_CONSOLIDES_A_VERIFIER'}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in bilan.items() if k!='archives_sources'},ensure_ascii=False),flush=True)
 return bilan
if __name__=='__main__':executer()

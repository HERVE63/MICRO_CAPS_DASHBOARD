"""Premier périmètre US provisoire sur archives SEC, sans note ni sélection.
Une immatriculation ET une adresse d'activité US concordantes donnent une piste,
jamais une identité de cotation vérifiée ni une couverture mondiale exhaustive.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, math, subprocess
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
ETATS_US=set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC'.split())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def classer(obj,cik):
 if str(obj.get('cik','')).zfill(10)!=cik.zfill(10):return 'CIK_INCOHERENT'
 inc=obj.get('stateOfIncorporation') or ''
 adr=obj.get('addresses',{}).get('business',{}) or {}
 pays=adr.get('stateOrCountry') or ''
 if not inc or not pays:return 'ORIGINE_A_COMPLETER'
 if inc in ETATS_US and pays in ETATS_US:
  if adr.get('isForeignLocation') in (True,1):return 'ORIGINE_A_CLARIFIER'
  return 'PISTE_US_CONCORDANTE' if obj.get('entityType')=='operating' else 'TYPE_EMETTEUR_A_CLARIFIER'
 if inc not in ETATS_US and pays not in ETATS_US:return 'HORS_PISTE_US'
 return 'ORIGINE_A_CLARIFIER'
def executer():
 now=datetime.now(timezone.utc);d=pd.read_csv(BASE/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv',dtype=str,keep_default_na=False)
 if d.empty or d.Ticker.duplicated().any():raise RuntimeError('PERIMETRE_INVALIDE')
 manifests=[]
 for p in (BASE/'AUDITS/SEC').glob('RUN_*/MANIFESTE.json'):
  m=json.loads(p.read_text());date=datetime.fromisoformat(m['date_utc'])
  if date<=now and (p.parent/'DONNEES/PREUVES_SEC_EDGAR_SSI.csv').exists():manifests.append((date,p,m))
 if not manifests:raise RuntimeError('AUCUN_INDEX_SEC_ARCHIVE')
 _,mp,m=max(manifests,key=lambda z:(z[0],str(z[1])))
 idx=mp.parent/'DONNEES/PREUVES_SEC_EDGAR_SSI.csv'
 if m['fichiers'].get(str(idx.relative_to(mp.parent)))!=sha(idx):raise RuntimeError('INDEX_SEC_CORROMPU')
 index=pd.read_csv(idx,dtype=str,keep_default_na=False)
 if index.Ticker.duplicated().any():raise RuntimeError('INDEX_SEC_DOUBLON')
 index=index.set_index('Ticker');sources={}
 for _,p,_ in sorted(manifests):
  src=p.parent/'SOURCES_BRUTES.json'
  if not src.exists():continue
  for r in json.loads(src.read_text()):
   if not r['url'].startswith('https://data.sec.gov/submissions/CIK') or not r['url'].endswith('.json'):continue
   # Ne pas assimiler les fichiers historiques CIK...-submissions-... au profil courant.
   suffix=r['url'].split('/CIK')[-1][:-5]
   if not suffix.isdigit() or len(suffix)!=10:continue
   date=datetime.fromisoformat(r['date_collecte_utc'])
   if date>now:continue
   if suffix not in sources or date>sources[suffix][0]:sources[suffix]=(date,p.parent,r)
 out=BASE/'AUDITS/UNIVERS_US'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 # Le validateur existant conserve ses exigences ; seules ses sorties vont dans l'audit.
 spec=importlib.util.spec_from_file_location('ssi_us',BASE/'SCRIPTS_ACTIFS/07R_VALIDER_NOTES_SSI.py')
 gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
 gate.D=BASE/'DONNEES';gate.SRC=gate.D/'DOSSIERS_SSI_A_QUALIFIER.csv'
 gate.OUT=out/'RESULTATS_SSI_CONTROLES.csv';gate.AUD=out/'AUDIT_SSI.csv'
 ssi=gate.executer().set_index('Ticker');rows=[];bruts={}
 for _,r in d.iterrows():
  row={'Ticker_cotation':r.Ticker,'Societe_dossier':r.Societe,'Pays_cotation':r.Pays,
       'Statut_origine':'ORIGINE_NON_DOCUMENTEE','Statut_identite':'A_VERIFIER_COTATION_EMETTEUR',
       'Statut_SSI':ssi.loc[r.Ticker,'Statut_SSI'],'SSI_evaluable':ssi.loc[r.Ticker,'Statut_SSI'] in ['ADMIS_SSI','REFUSE_SSI','ELIMINE']}
  if r.Ticker in index.index:
   z=index.loc[r.Ticker];cik=z.get('CIK','').zfill(10)
   row.update(CIK=cik if cik.isdigit() else '',Methode_rapprochement=z.get('Methode_rapprochement',''))
   if cik in sources:
    date,a,src=sources[cik];f=a/'BRUTS'/(src['sha256']+'.bin')
    if sha(f)!=src['sha256']:raise RuntimeError('PROFIL_SEC_CORROMPU: '+cik)
    obj=json.loads(f.read_bytes());adr=obj.get('addresses',{}).get('business',{}) or {}
    row.update(Statut_origine=classer(obj,cik),Nom_SEC=obj.get('name',''),
       Etat_immatriculation_SEC=obj.get('stateOfIncorporation',''),Etat_adresse_activite_SEC=adr.get('stateOrCountry',''),
       Tickers_SEC='|'.join(obj.get('tickers',[])),SIC=str(obj.get('sic') or ''),Secteur_SEC=obj.get('sicDescription',''),Source_URL=src['url'],
       Date_source_UTC=src['date_collecte_utc'],Fichier_brut=str(f.relative_to(BASE)),SHA256=src['sha256'])
    bruts[str(f.relative_to(BASE))]=src['sha256']
  rows.append(row)
 result=pd.DataFrame(rows);us=result[result.Statut_origine.eq('PISTE_US_CONCORDANTE')].copy()
 # Plusieurs cotations d'un même émetteur ne gonflent pas le dénominateur.
 emit=us.sort_values('Ticker_cotation').drop_duplicates('CIK').copy()
 emit['Cotations_dossiers']=emit.CIK.map(us.groupby('CIK').Ticker_cotation.agg(lambda x:'|'.join(sorted(x))))
 emit['SSI_evaluable']=emit.CIK.map(us.groupby('CIK').SSI_evaluable.any())
 n=len(emit);valid=int(emit.SSI_evaluable.sum())
 result.to_csv(out/'COUVERTURE_ORIGINE_1361.csv',index=False)
 us.to_csv(out/'PISTES_US_PAR_COTATION.csv',index=False)
 emit.to_csv(out/'UNIVERS_US_PROVISOIRE.csv',index=False)
 secteurs=emit.groupby(['SIC','Secteur_SEC'],dropna=False).agg(Emetteurs_pistes=('CIK','size'),Evaluables_SSI=('SSI_evaluable','sum')).reset_index()
 secteurs['Couverture_SSI_pct']=100*secteurs.Evaluables_SSI/secteurs.Emetteurs_pistes
 secteurs.to_csv(out/'COUVERTURE_SECTORIELLE_US.csv',index=False)
 bilan={'date_utc':now.isoformat(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),
  'dossiers_initials':len(d),'index_SEC_source':str(idx.relative_to(BASE)),'source_script_SHA256':sha(Path(__file__)),
  'repartition_origine':result.Statut_origine.value_counts().to_dict(),'cotations_pistes_US':len(us),
  'emetteurs_US_provisoires':n,'emetteurs_US_evaluables_SSI':valid,
  'seuil_minimum_US_50pct':math.ceil(n*.5),'cible_US_90pct':math.ceil(n*.9),
  'couverture_SSI_US_pct':100*valid/n if n else None,
  'origine_complete_des_1361':False,'identites_validees_automatiquement':0,'notes_attribuees':0,
  'selection_finale_autorisee':False,'statut':'PERIMETRE_US_PROVISOIRE_A_VERIFIER',
  'restrictions':['Sous-ensemble du périmètre existant, pas un recensement complet des microcaps US',
   'Immatriculation et adresse US ne valident pas le lien cotation-ISIN-émetteur',
   'Données brutes, admission SSI et couverture SSI sont des mesures distinctes',
   'Les seuils US ne remplacent pas les objectifs mondiaux 681/1225'],
  'preuves_brutes':bruts,'fichiers':{p.name:sha(p) for p in out.glob('*.csv')}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in bilan.items() if k not in ['preuves_brutes','fichiers','restrictions']},ensure_ascii=False))
 return bilan
if __name__=='__main__':executer()

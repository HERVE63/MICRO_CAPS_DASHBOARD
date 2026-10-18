"""Ordre SCE maître appliqué au recensement, puis sas SSI sur preuves existantes.

L'ordre n'est ni une notation financière ni une sélection finale. La table
humaine est lue uniquement et reste distincte des collectes réexécutables.
"""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import hashlib,importlib.util,json,os,re
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def charger(nom):
 s=importlib.util.spec_from_file_location(nom[:-3],BASE/'SCRIPTS_ACTIFS'/nom)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def isin_valide(v):
 if not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}[0-9]',v):return False
 chiffres=''.join(str(ord(c)-55) if c.isalpha() else c for c in v)
 total=0
 for i,c in enumerate(reversed(chiffres)):
  n=int(c)*(2 if i%2 else 1);total+=n//10+n%10
 return total%10==0
def empreinte(ticker,isin):return hashlib.sha256(('SCE20260812 | '+ticker+' | '+isin).encode()).hexdigest()
def ordonner(dossiers,instruments):
 comptes={}
 for r in dossiers:
  isin=str(r.get('ISIN') or r.get('ISIN_catalogue') or '').strip().upper()
  if isin_valide(isin):comptes[isin]=comptes.get(isin,0)+1
 rows=[]
 for r in dossiers:
  t=r['Ticker_US'];isin=str(r.get('ISIN') or r.get('ISIN_catalogue') or '').strip().upper()
  instrument=instruments.get(t,{});type_=instrument.get('Statut_instrument','CONTROLE_OFFICIEL_ABSENT')
  motifs=[]
  try:
   cap=Decimal(str(r['Capitalisation_EUR']))
   if not cap.is_finite() or not Decimal(50000000)<=cap<=Decimal(300000000):motifs.append('HORS_MANDAT_CAPITALISATION')
  except Exception:motifs.append('CAPITALISATION_A_COMPLETER')
  if type_!='ACTION_ORDINAIRE_LIBELLE_OFFICIEL':motifs.append(type_)
  if not isin_valide(isin):motifs.append('ISIN_MANQUANT_OU_INVALIDE')
  elif comptes[isin]>1:motifs.append('DOUBLON_ISIN_COTATION_PRIMAIRE_A_CONFIRMER')
  if r.get('Lien_ticker_CIK')!='CONCORDANCE_EXACTE_SEC':motifs.append('LIEN_TICKER_CIK_A_COMPLETER')
  if r.get('Statut_origine')!='PISTE_US_CONCORDANTE':motifs.append('ORIGINE_EMETTEUR_A_VERIFIER')
  # Les sources disponibles ne prouvent pas encore tous les contrôles du maître.
  motifs.extend(['ISIN_ET_IDENTITE_A_CONFIRMER_SUR_PREUVE','FONDS_SPAC_ET_EXCLUSIONS_A_VERIFIER'])
  rows.append({'Ticker':t,'Societe':r.get('Nom_SEC',''),'CIK':r.get('CIK',''),
   'Hash_SCE':empreinte(t,isin) if isin_valide(isin) else '',
   'ISIN_present_checksum_valide':'OUI' if isin_valide(isin) else 'NON',
   'ISIN_SHA256':hashlib.sha256(isin.encode()).hexdigest() if isin else '',
   'Doublons_ISIN':comptes.get(isin,0),'Statut_instrument':type_,
   'Statut_SCE':'CONTROLES_MAITRES_A_COMPLETER','Motifs':';'.join(motifs),
   'Rang_controle_SCE':'','SCE_valide':'NON','SSI':'MANQUANTE'})
 # Même ordre pour les entrées identiques, sans dépendre de l'ordre du fournisseur.
 classes=sorted((r for r in rows if r['Hash_SCE']),key=lambda r:(r['Hash_SCE'],r['Ticker']))
 for rang,r in enumerate(classes,1):r['Rang_controle_SCE']=rang
 return sorted(rows,key=lambda r:(not bool(r['Hash_SCE']),r['Hash_SCE'],r['Ticker']))
def appliquer_revues(ordre,revues,preuves,base,recensement_sha,limite=None):
 """Une revue primaire identifiée lève les contrôles ; aucune collecte ne s'auto-valide."""
 from preuves_ssi import verifier
 if revues.Ticker.duplicated().any():raise RuntimeError('REVUES_IDENTITE_DUPLIQUEES')
 index={r['Ticker']:r for r in ordre}
 for _,v in revues.iterrows():
  if v.Ticker not in index:raise RuntimeError('REVUE_IDENTITE_HORS_UNIVERS')
  r=index[v.Ticker];erreurs=[]
  if v.Recensement_SHA256!=recensement_sha:erreurs.append('REVUE_RECENSEMENT_DIFFERENT')
  if v.CIK!=r['CIK'] or not re.fullmatch(r'[0-9]{10}',v.CIK):erreurs.append('CIK_REVUE_DIVERGENT')
  if not isin_valide(v.ISIN) or hashlib.sha256(v.ISIN.encode()).hexdigest()!=r['ISIN_SHA256']:erreurs.append('ISIN_REVUE_DIVERGENT')
  if v.Statut_revue!='VERIFIEE':erreurs.append('REVUE_NON_VERIFIEE')
  if r['Doublons_ISIN']!=1:erreurs.append('DOUBLON_ISIN')
  # Une revue primaire explicite peut documenter une action OTC absente des répertoires Nasdaq.
  permis={'ACTION_ORDINAIRE_LIBELLE_OFFICIEL','ABSENT_REPERTOIRES_LISTES_OTC_OU_IDENTITE_A_COMPLETER'}
  if r['Statut_instrument'] not in permis:erreurs.append('INSTRUMENT_NON_ORDINAIRE_OU_NON_CONTROLE')
  motifs=r['Motifs'].split(';')
  if any(x in motifs for x in ['HORS_MANDAT_CAPITALISATION','CAPITALISATION_A_COMPLETER','LIEN_TICKER_CIK_A_COMPLETER']):erreurs.append('CONTROLE_DUR_NON_RESOLU')
  for champ,bloc in [('Preuves_identite','IDENTITE_SCE'),('Preuve_exclusions','EXCLUSIONS')]:
   ids=v[champ].split('|');z=preuves[preuves.ID_preuve.isin(ids)]
   if not ids or len(ids)!=len(set(ids)) or len(z)!=len(ids):erreurs.append('PREUVES_REVUE_ABSENTES')
   for _,q in z.iterrows():
    erreurs.extend(verifier(q,v.Ticker,bloc,base,limite))
    if q.Identifiant_emetteur!='CIK:'+v.CIK:erreurs.append('IDENTITE_PREUVE_DIVERGENTE')
   if bloc=='IDENTITE_SCE' and (len(z)<2 or z.Source_URL.nunique()<2):erreurs.append('DEUX_SOURCES_IDENTITE_REQUISES')
  if erreurs:
   r['Motifs']+=';'+';'.join(sorted(set(erreurs)));continue
  r.update(SCE_valide='OUI',Statut_SCE='IDENTITE_EXCLUSIONS_VERIFIEES',Motifs='REVUE_PRIMAIRE_IDENTIFIEE',Preuve_controle_exclusions=v.Preuve_exclusions,Preuves_identite_SCE=v.Preuves_identite)
 return ordre
def dossiers_ssi(ordre,humains,documentaires=None,notes_documentaires=None):
 if humains.Ticker.duplicated().any():raise RuntimeError('REGISTRE_HUMAIN_US_DUPLIQUE')
 reg=humains.set_index('Ticker');rows=[]
 docs={}
 notes={}
 if notes_documentaires is not None:
  attendus={'Ticker',*[p+'B'+str(n) for n in range(1,8) for p in ('Note_','Preuve_')]}
  if set(notes_documentaires.columns)!=attendus or notes_documentaires.Ticker.duplicated().any():raise RuntimeError('NOTES_DOCUMENTAIRES_SCHEMA_INVALIDE')
  if set(notes_documentaires.Ticker)-{r['Ticker'] for r in ordre}:raise RuntimeError('NOTES_DOCUMENTAIRES_HORS_UNIVERS')
  for _,q in notes_documentaires.iterrows():
   for n in range(1,8):
    note=str(q['Note_B'+str(n)]).strip();preuve=str(q['Preuve_B'+str(n)]).strip()
    if bool(note)!=bool(preuve):raise RuntimeError('NOTE_DOCUMENTAIRE_SANS_PREUVE_OU_INVERSEMENT')
  notes=notes_documentaires.set_index('Ticker').to_dict('index')
 if documentaires is not None:
  if set(documentaires.columns)!={'Ticker','Decision_eliminatoire','Motif_eliminatoire'} or documentaires.Ticker.duplicated().any():
   raise RuntimeError('REGISTRE_DOCUMENTAIRE_SCHEMA_INVALIDE')
  if not documentaires.Decision_eliminatoire.eq('OUI').all():raise RuntimeError('REVUE_DOCUMENTAIRE_LIMITEE_AUX_EXCLUSIONS')
  inconnus=set(documentaires.Ticker)-{r['Ticker'] for r in ordre}
  if inconnus:raise RuntimeError('REVUE_DOCUMENTAIRE_HORS_UNIVERS')
  docs=documentaires.set_index('Ticker').to_dict('index')
 for r in ordre:
  d={k:r[k] for k in ('Ticker','Societe','CIK','Statut_SCE','SCE_valide','Rang_controle_SCE')}
  d['Preuves_identite_SCE']=r.get('Preuves_identite_SCE','MANQUANTE')
  d.update(Decision_eliminatoire='NON' if r['SCE_valide']=='OUI' else 'A_VERIFIER',Motif_eliminatoire=r.get('Preuve_controle_exclusions','MANQUANTE'))
  for b in range(1,8):d['Note_B'+str(b)]='MANQUANTE';d['Preuve_B'+str(b)]='MANQUANTE'
  if r['Ticker'] in notes:d.update({k:v for k,v in notes[r['Ticker']].items() if str(v).strip()})
  if r['Ticker'] in docs:d.update(docs[r['Ticker']])
  # Les corrections humaines explicites priment ; aucune collecte n'écrit ces registres.
  if r['Ticker'] in reg.index:
   for k,v in reg.loc[r['Ticker']].items():
    if k.startswith(('Note_','Preuve_','Validation_','Correction_')) or k in ('Decision_eliminatoire','Motif_eliminatoire'):
     if str(v).strip():d[k]=v
  rows.append(d)
 return pd.DataFrame(rows)
def executer():
 util=charger('07AI_RACCORDER_COMPTES_US_SSI.py');eod=charger('07AH_RECENSER_MICROCAPS_US_EODHD.py')
 sources=sorted((BASE/'AUDITS/RECENSEMENT_US_EODHD').glob('*/MANIFESTE.json'))
 officiels=sorted((BASE/'AUDITS/INSTRUMENTS_US_OFFICIELS').glob('*/MANIFESTE.json'))
 if not sources or not officiels:raise RuntimeError('SOURCES_SCE_ABSENTES')
 mp=sources[-1];m=json.loads(mp.read_text());ip=officiels[-1];im=json.loads(ip.read_text())
 if not m.get('recensement_termine') or im['source_manifeste_SHA256']!=sha(mp):raise RuntimeError('SOURCES_SCE_INCOHERENTES')
 cle=os.getenv('EODHD_API_KEY','').strip()
 if not cle:raise RuntimeError('CLE_ARCHIVES_ABSENTE')
 p=util.verifier_fichier(mp.parent,m,'DOSSIERS_EODHD_A_VERIFIER.enc.json')
 dossiers=json.loads(eod.dechiffrer(json.loads(p.read_text()),cle))
 if len({r['Ticker_US'] for r in dossiers})!=len(dossiers):raise RuntimeError('DOUBLONS_TICKERS_SCE')
 p=util.verifier_fichier(ip.parent,im,'CONTROLE_INSTRUMENTS_US.csv')
 ins=pd.read_csv(p,dtype=str,keep_default_na=False)
 if ins.Ticker_US.duplicated().any():raise RuntimeError('INSTRUMENTS_DUPLIQUES')
 ordre=ordonner(dossiers,ins.set_index('Ticker_US').to_dict('index'))
 identite_path=BASE/'CONFIG/REVUES_IDENTITE_SCE_US.csv'
 if identite_path.exists():
  from preuves_ssi import registre
  ordre=appliquer_revues(ordre,pd.read_csv(identite_path,dtype=str,keep_default_na=False),registre(BASE),BASE,sha(mp))
 out=BASE/'AUDITS/SCE_DISCOVERY_US'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out.mkdir(parents=True,exist_ok=False)
 pd.DataFrame(ordre).to_csv(out/'ORDRE_CONTROLES_SCE.csv',index=False)
 ledger=BASE/'CONFIG/QUALIFICATIONS_SSI_US_HUMAINES.csv';avant=sha(ledger)
 humains=pd.read_csv(ledger,dtype=str,keep_default_na=False)
 documentaire=BASE/'CONFIG/EXCLUSIONS_US_REVUES_DOCUMENTAIRES.csv'
 revue=pd.read_csv(documentaire,dtype=str,keep_default_na=False) if documentaire.exists() else None
 documentaire_sha=sha(documentaire) if documentaire.exists() else None
 notes_path=BASE/'CONFIG/NOTES_SSI_US_REVUES_DOCUMENTAIRES.csv'
 notes=pd.read_csv(notes_path,dtype=str,keep_default_na=False) if notes_path.exists() else None
 notes_sha=sha(notes_path) if notes_path.exists() else None
 dossiers_ssi(ordre,humains,revue,notes).to_csv(out/'DOSSIERS_SSI_A_QUALIFIER.csv',index=False)
 ssi=charger('07R_VALIDER_NOTES_SSI.py');ssi.SRC=out/'DOSSIERS_SSI_A_QUALIFIER.csv'
 ssi.OUT=out/'RESULTATS_SSI.csv';ssi.AUD=out/'AUDIT_SSI.csv';result=ssi.executer()
 if sha(ledger)!=avant:raise RuntimeError('REGISTRE_HUMAIN_MODIFIE')
 if notes_path.exists() and sha(notes_path)!=notes_sha:raise RuntimeError('REGISTRE_NOTES_DOCUMENTAIRES_MODIFIE')
 bilan={'date_utc':datetime.now(timezone.utc).isoformat(),'source_recensement':str(mp.relative_to(BASE)),
  'source_instruments':str(ip.relative_to(BASE)),'source_script_SHA256':sha(Path(__file__)),
  'protocole_SHA256':sha(BASE/'CONFIG/PROTOCOLE_SCE_DISCOVERY_MICROCAPS.json'),
  'notes_documentaires_SHA256':notes_sha,'registre_documentaire_SHA256':documentaire_sha,'registre_humain_SHA256':avant,'cotations_conservees':len(ordre),
  'ISIN_checksum_valides':sum(r['ISIN_present_checksum_valide']=='OUI' for r in ordre),
  'doublons_ISIN_cotations':sum(r['Doublons_ISIN']>1 for r in ordre),
  'identites_revues_SHA256':sha(identite_path) if identite_path.exists() else None,'SCE_valides':sum(r['SCE_valide']=='OUI' for r in ordre),'repartition_SSI':result.Statut_SSI.value_counts().to_dict(),
  'selection_finale_autorisee':False,'panel_SCE_experimental_modifie':False,
  'statut':'ORDRE_SCE_MAITRE_APPLIQUE_IDENTITES_ET_PREUVES_A_COMPLETER',
  'fichiers':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(bilan,ensure_ascii=False));return bilan
if __name__=='__main__':executer()

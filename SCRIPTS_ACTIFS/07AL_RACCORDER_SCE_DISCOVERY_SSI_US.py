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
def dossiers_ssi(ordre,humains):
 if humains.Ticker.duplicated().any():raise RuntimeError('REGISTRE_HUMAIN_US_DUPLIQUE')
 reg=humains.set_index('Ticker');rows=[]
 for r in ordre:
  d={k:r[k] for k in ('Ticker','Societe','CIK','Statut_SCE','SCE_valide','Rang_controle_SCE')}
  d.update(Decision_eliminatoire='A_VERIFIER',Motif_eliminatoire='MANQUANTE')
  for b in range(1,8):d['Note_B'+str(b)]='MANQUANTE';d['Preuve_B'+str(b)]='MANQUANTE'
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
 out=BASE/'AUDITS/SCE_DISCOVERY_US'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out.mkdir(parents=True,exist_ok=False)
 pd.DataFrame(ordre).to_csv(out/'ORDRE_CONTROLES_SCE.csv',index=False)
 ledger=BASE/'CONFIG/QUALIFICATIONS_SSI_US_HUMAINES.csv';avant=sha(ledger)
 humains=pd.read_csv(ledger,dtype=str,keep_default_na=False)
 dossiers_ssi(ordre,humains).to_csv(out/'DOSSIERS_SSI_A_QUALIFIER.csv',index=False)
 ssi=charger('07R_VALIDER_NOTES_SSI.py');ssi.SRC=out/'DOSSIERS_SSI_A_QUALIFIER.csv'
 ssi.OUT=out/'RESULTATS_SSI.csv';ssi.AUD=out/'AUDIT_SSI.csv';result=ssi.executer()
 if sha(ledger)!=avant:raise RuntimeError('REGISTRE_HUMAIN_MODIFIE')
 bilan={'date_utc':datetime.now(timezone.utc).isoformat(),'source_recensement':str(mp.relative_to(BASE)),
  'source_instruments':str(ip.relative_to(BASE)),'source_script_SHA256':sha(Path(__file__)),
  'protocole_SHA256':sha(BASE/'CONFIG/PROTOCOLE_SCE_DISCOVERY_MICROCAPS.json'),
  'registre_humain_SHA256':avant,'cotations_conservees':len(ordre),
  'ISIN_checksum_valides':sum(r['ISIN_present_checksum_valide']=='OUI' for r in ordre),
  'doublons_ISIN_cotations':sum(r['Doublons_ISIN']>1 for r in ordre),
  'SCE_valides':0,'repartition_SSI':result.Statut_SSI.value_counts().to_dict(),
  'selection_finale_autorisee':False,'panel_SCE_experimental_modifie':False,
  'statut':'ORDRE_SCE_MAITRE_APPLIQUE_IDENTITES_ET_PREUVES_A_COMPLETER',
  'fichiers':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(bilan,ensure_ascii=False));return bilan
if __name__=='__main__':executer()

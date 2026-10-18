"""Assemble les pistes financières/documentaires et raccorde 07X au recensement US.

La matrice indique les pièces à vérifier, pas des blocs SSI validés. Les XML
Form 4 non extraits restent explicitement à collecter ; aucun achat personnel,
pourcentage de détention ou score n'est déduit de l'index des dépôts.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,re
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def charger(nom):
 s=importlib.util.spec_from_file_location(nom[:-3],BASE/'SCRIPTS_ACTIFS'/nom)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def depots(obj,cik,limite,formes):
 q=obj.get('filings',{}).get('recent',{});forms=q.get('form',[])
 if any(len(q.get(k,[]))!=len(forms) for k in ('filingDate','accessionNumber')):raise RuntimeError('PARSING_INDEX_INCOMPLET')
 rows=[]
 for form,date,acc in zip(forms,q.get('filingDate',[]),q.get('accessionNumber',[])):
  if form not in formes:continue
  try:datetime.strptime(date,'%Y-%m-%d')
  except (ValueError,TypeError):raise RuntimeError('DATE_DEPOT_INDEX_INVALIDE')
  if date>limite or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):continue
  rows.append({'form':form,'date':date,'accession':acc,
    'url_archive_officielle':'https://www.sec.gov/Archives/edgar/data/'+str(int(cik))+'/'+acc.replace('-','')+'/'})
 # Aucun plafond de 30 dépôts : tout le tableau recent connu est parcouru.
 return rows
def dernier(dossier):
 p=sorted((BASE/'AUDITS'/dossier).glob('*/MANIFESTE.json'))
 if not p:raise RuntimeError('SOURCE_ABSENTE:'+dossier)
 return p[-1],json.loads(p[-1].read_text())
def sources_ir(util,univers):
 # Dernière collecte du registre US uniquement ; les anciennes collectes non-US
 # ne doivent jamais se substituer à ce périmètre.
 for mp in sorted((BASE/'AUDITS/SOURCES_OFFICIELLES').glob('*/MANIFESTE.json'),reverse=True):
  meta=json.loads(mp.read_text())
  if Path(meta.get('registre_source','')).name!='DOCUMENTS_OFFICIELS_US_A_COLLECTER.csv':continue
  if meta.get('couverture_source_SHA256')!=sha(univers):raise RuntimeError('PERIMETRE_IR_US_INCOHERENT')
  docs=pd.read_csv(util.verifier_fichier(mp.parent,meta,'AUDIT_DOCUMENTS.csv'),dtype=str,keep_default_na=False)
  result={}
  for _,r in docs.iterrows():
   if r.Statut!='DOCUMENT_COLLECTE_A_VERIFIER':continue
   raw=(BASE/r.Fichier_brut).resolve()
   if raw.parent!=mp.parent.resolve():raise RuntimeError('CHEMIN_SOURCE_IR_INVALIDE')
   util.verifier_fichier(mp.parent,meta,raw.name)
   if sha(raw)!=r.SHA256:raise RuntimeError('EMPREINTE_DOCUMENT_IR_INCOHERENTE')
   result.setdefault(r.Ticker,[]).append(r.to_dict())
  return result,mp
 return {},None
def complement(util,dossier,fichier,univers):
 fichiers=sorted((BASE/'AUDITS'/dossier).glob('*/MANIFESTE.json'))
 if not fichiers:return {},None
 mp=fichiers[-1];meta=json.loads(mp.read_text())
 if meta.get('source_univers_SHA256')!=sha(univers):raise RuntimeError('PERIMETRE_COMPLEMENT_US_INCOHERENT:'+dossier)
 d=pd.read_csv(util.verifier_fichier(mp.parent,meta,fichier),dtype=str,keep_default_na=False)
 if 'Ticker' not in d or d.Ticker.duplicated().any():raise RuntimeError('COMPLEMENT_US_IDENTITES_DUPLIQUEES')
 attendu=pd.read_csv(univers,dtype=str,keep_default_na=False)
 if set(d.Ticker)!=set(attendu.Ticker_US):raise RuntimeError('COMPLEMENT_US_UNIVERS_TRONQUE')
 if dossier=='MARCHE_US_EODHD' and not meta.get('volumes_monetaires_corriges_splits'):
  d['Volume_monetaire_63s_disponible']='NON'
 return d.set_index('Ticker').to_dict('index'),mp
def lot_inities(util):
 fichiers=sorted((BASE/'AUDITS/RELECTURE_INITIES_US').glob('*/MANIFESTE.json'))
 if not fichiers:return {},None
 mp=fichiers[-1];meta=json.loads(mp.read_text())
 if meta.get('profils_en_erreur') or any(k!='TRANSACTIONS_A_VERIFIER' for k in meta.get('repartition_controles',{})):
  raise RuntimeError('LOT_INITIES_INCOMPLET_OU_AMBIGU')
 profils=pd.read_csv(util.verifier_fichier(mp.parent,meta,'PROFILS_ACTUALISES.csv'),dtype=str,keep_default_na=False)
 transactions=pd.read_csv(util.verifier_fichier(mp.parent,meta,'TRANSACTIONS_FORM4_LOT.csv'),dtype=str,keep_default_na=False)
 if profils.Ticker.duplicated().any() or len(profils)!=meta['emetteurs_lot'] or len(transactions)!=meta['transactions_non_derivees_extraites']:
  raise RuntimeError('LOT_INITIES_DECOMPTE_DIVERGENT')
 mapping=profils.set_index('Ticker').CIK.to_dict()
 if any(mapping.get(r.Ticker)!=r.CIK for _,r in transactions.iterrows()):raise RuntimeError('LOT_INITIES_CIK_DIVERGENT')
 return {t:{'CIK':c,'lignes':int(transactions.Ticker.eq(t).sum()),'date_limite':meta['date_limite_depots']} for t,c in mapping.items()},mp
def executer():
 util=charger('07AI_RACCORDER_COMPTES_US_SSI.py');x=charger('07X_INDEX_GOUVERNANCE_SEC.py')
 pp,pm=dernier('PROFILS_SEC_UNIVERS_US');dp,dm=dernier('DOCUMENTS_US')
 fp,fm=dernier('QUALIFICATION_US');sp,sm=dernier('SCE_DISCOVERY_US');cp,cm=dernier('CONTROLE_DOCUMENTS_US')
 if dm['univers_source']!=str((pp.parent/'UNIVERS_SEC_COTATIONS_US.csv').relative_to(BASE)):
  raise RuntimeError('DOCUMENTS_HORS_RECENSEMENT_ELARGI')
 if cm['archive_source']!=str(dp.relative_to(BASE)):raise RuntimeError('CONTROLES_DOCUMENTAIRES_NON_CONCORDANTS')
 if fm['source_recensement']!=pm['source_recensement'] or sm['source_recensement']!=pm['source_recensement']+'/MANIFESTE.json':
  raise RuntimeError('PERIMETRES_PREUVES_DIFFERENTS')
 profils=pd.read_csv(util.verifier_fichier(pp.parent,pm,'UNIVERS_SEC_COTATIONS_US.csv'),dtype=str,keep_default_na=False)
 tous=pd.read_csv(util.verifier_fichier(pp.parent,pm,'TOUTES_COTATIONS_RECENSEES.csv'),dtype=str,keep_default_na=False)
 docs=pd.read_csv(util.verifier_fichier(dp.parent,dm,'AUDIT_DOCUMENTS.csv'),dtype=str,keep_default_na=False)
 finances=pd.read_csv(util.verifier_fichier(fp.parent,fm,'COUVERTURE_QUALIFICATION_US.csv'),dtype=str,keep_default_na=False).set_index('Ticker_US')
 ssi=pd.read_csv(util.verifier_fichier(sp.parent,sm,'RESULTATS_SSI.csv'),dtype=str,keep_default_na=False).set_index('Ticker')
 ordre=pd.read_csv(util.verifier_fichier(sp.parent,sm,'ORDRE_CONTROLES_SCE.csv'),dtype=str,keep_default_na=False).set_index('Ticker')
 controles=pd.read_csv(util.verifier_fichier(cp.parent,cm,'CONTROLES_DOCUMENTS.csv'),dtype=str,keep_default_na=False)
 if tous.Ticker_US.duplicated().any() or not finances.index.is_unique or not ssi.index.is_unique:raise RuntimeError('IDENTITES_DUPLIQUEES')
 out=BASE/'AUDITS/MATRICE_PREUVES_US'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out.mkdir(parents=True,exist_ok=False);sources=[];pagination=[]
 for _,r in profils.iterrows():
  raw=BASE/r.Fichier_brut
  if sha(raw)!=r.SHA256 or pm['fichiers'].get(raw.name)!=r.SHA256:raise RuntimeError('PROFIL_SOURCE_CORROMPU')
  obj=json.loads(raw.read_text())
  if str(obj.get('cik','')).zfill(10)!=r.CIK:raise RuntimeError('CIK_PROFIL_DIVERGENT')
  limite=r.Date_source_UTC[:10]
  known=depots(obj,r.CIK,limite,x.FORMES)
  sources.append({'Ticker':r.Ticker_cotation,'Societe':r.Nom_SEC,'CIK':r.CIK,
   'Statut_SEC':'A_VERIFIER_IDENTITE_ET_CONTENU','Depots':json.dumps(known,ensure_ascii=False)})
  anciens=obj.get('filings',{}).get('files',[])
  pagination.append({'CIK':r.CIK,'Depots_recent_indexes':len(known),'Fichiers_anciens_a_paginer':len(anciens),
    'Historique_transactions_complet':'NON_VERIFIE','Archives_anciennes_referencees':json.dumps(anciens,ensure_ascii=False)})
 pd.DataFrame(sources).to_csv(out/'INDEX_SEC_GOUVERNANCE.csv.gz',index=False)
 pd.DataFrame(pagination).to_csv(out/'COMPLETUDE_INDEX.csv',index=False)
 x.SRC=out/'INDEX_SEC_GOUVERNANCE.csv.gz';x.OUT=out/'PISTES_GOUVERNANCE_SEC_SSI.csv.gz';x.AUD=out/'AUDIT_GOUVERNANCE_SEC_SSI.csv'
 gouvernance=x.executer();forms4={}
 for r in gouvernance:
  if r['Formulaire'] in ('4','4/A'):forms4[r['CIK']]=forms4.get(r['CIK'],0)+1
 pieces={}
 for _,r in docs.iterrows():
  if r.Statut=='DOCUMENT_COLLECTE_A_VERIFIER':pieces.setdefault(r.CIK,set()).add(r.Formulaire)
 ir,ip=sources_ir(util,pp.parent/'TOUTES_COTATIONS_RECENSEES.csv')
 marche,mp=complement(util,'MARCHE_US_EODHD','COUVERTURE_MARCHE_US.csv',pp.parent/'TOUTES_COTATIONS_RECENSEES.csv')
 passages,gp=complement(util,'PASSAGES_GOUVERNANCE_US','COUVERTURE_PASSAGES_US.csv',pp.parent/'TOUTES_COTATIONS_RECENSEES.csv')
 inities,yp=lot_inities(util)
 matrice=[]
 for _,r in tous.iterrows():
  ticker=r.Ticker_US;f=finances.loc[ticker] if ticker in finances.index else {};s=ssi.loc[ticker] if ticker in ssi.index else {}
  o=ordre.loc[ticker] if ticker in ordre.index else {}
  hist=marche.get(ticker,{});gov=passages.get(ticker,{});initie=inities.get(ticker,{})
  if initie and initie['CIK']!=r.CIK:raise RuntimeError('LOT_INITIES_HORS_IDENTITE_UNIVERS')
  c=controles[controles.CIK.eq(r.CIK)]
  p=pieces.get(r.CIK,set())
  autres=ir.get(ticker,[])
  if any(q.get('Identifiant_emetteur')!='CIK:'+r.CIK for q in autres):raise RuntimeError('CIK_SOURCE_IR_INCOHERENT')
  matrice.append({'Ticker':ticker,'CIK':r.CIK,'Statut_origine':r.Statut_origine,
    'Statut_instrument':o.get('Statut_instrument','VOIR_CONTROLE_INSTRUMENTS_US'),
    'Faits_comparables':f.get('Faits_comparables','0'),'Concepts_financiers':f.get('Concepts_comparables',''),
    'Dernier_depot_financier_comparable':f.get('Dernier_depot_comparable',''),
    'Rapport_10K_collecte':'OUI' if '10-K' in p else 'NON',
    'Rapport_10Q_collecte':'OUI' if '10-Q' in p else 'NON',
    'Proxy_DEF14A_collecte':'OUI' if 'DEF 14A' in p else 'NON',
    'Documents_IR_collectes_a_verifier':sum(q.get('Nature_document')!='INDEX_DOCUMENTAIRE_PAS_COMPTES' for q in autres),
    'Index_IR_sans_comptes':sum(q.get('Nature_document')=='INDEX_DOCUMENTAIRE_PAS_COMPTES' for q in autres),
    'Sources_IR':';'.join(q.get('Source_URL','') for q in autres),
    'Dates_publication_IR':'|'.join(q.get('Date_publication','') or 'INCONNUE' for q in autres),
    'Documents_CIK_concordants':int(c.Controle_document.eq('CIK_XBRL_CONCORDANT').sum()),
    'Documents_CIK_divergents':int(c.Controle_document.eq('CIK_XBRL_DIVERGENT').sum()),
    'Documents_CIK_absent_a_relire':int(c.Controle_document.eq('CIK_XBRL_ABSENT_A_RELIRE').sum()),
    'Form4_references_dans_index':forms4.get(r.CIK,0),'Form4_contenu':'LOT_2026_EXTRAIT_INTERPRETATION_PARTIELLE' if initie else 'A_EXTRAIRE_ET_VERIFIER',
    'Form4_lignes_lot_extraites':initie.get('lignes',0),'Form4_date_limite_depots_lot':initie.get('date_limite',''),
    'Form4_detentions_actuelles_reconstituees':'NON',
    'Statut_B1_B2_B3':'DONNEES_A_VERIFIER','Statut_B4_B5':'DOCUMENTS_ET_TRANSACTIONS_A_VERIFIER',
    'Statut_B6':'CONTENU_ET_REGULARITE_A_VERIFIER',
    'Statut_B7':'VOLUMES_RECUS_TURNOVER_SPREAD_ET_IDENTITE_A_VERIFIER' if hist.get('Volume_monetaire_63s_disponible')=='OUI' else 'VOLUMES_ET_SPREAD_A_DOCUMENTER',
    'Statut_collecte_marche':hist.get('Statut_collecte','NON_EXECUTEE'),
    'Date_reference_marche':hist.get('Date_reference',''),
    'Momentum_1_3_6_12_disponibles':hist.get('Momentum_1_3_6_12_disponibles','NON'),
    'Volumes_monetaires_63s_disponibles':hist.get('Volume_monetaire_63s_disponible','NON'),
    'Passages_detention_groupe':gov.get('DETENTION_GROUPE','0'),
    'Passages_droits_60_jours':gov.get('DROITS_A_60_JOURS','0'),
    'Passages_dilution_remuneration':gov.get('DILUTION_REMUNERATION','0'),
    'Statut_SCE':s.get('Statut_SCE','A_COMPLETER'),'SCE_valide':s.get('SCE_valide','NON'),
    'SSI':s.get('SSI','MANQUANTE'),'Statut_SSI':s.get('Statut_SSI','A_COMPLETER_PREUVES_SSI'),
    'Candidat_selection_autorise':'OUI' if s.get('SCE_valide')=='OUI' and s.get('Statut_SSI')=='ADMIS_SSI' else 'NON'})
 result=pd.DataFrame(matrice);result.to_csv(out/'MATRICE_PREUVES_SSI_US.csv',index=False)
 bilan={'date_utc':datetime.now(timezone.utc).isoformat(),'source_script_SHA256':sha(Path(__file__)),
  'sources':{str(p.relative_to(BASE)):sha(p) for p in (pp,dp,fp,sp,cp,ip,mp,gp,yp) if p is not None},'cotations_conservees':len(result),
  'emetteurs_profils_distincts':len(profils),'pistes_gouvernance':len(gouvernance),
  # L'index historique global ne se confond pas avec les 216 dépôts du lot 2026.
  'Form4_references_non_extraits':sum(forms4.values()),
  'Form4_sens_compteur_historique':'REFERENCES_GLOBALES_NON_RAPPROCHEES_DU_LOT_2026',
  'Form4_cotations_avec_lot_extrait':len(inities),'Form4_lignes_lot_extraites':sum(q['lignes'] for q in inities.values()),
  'documents_IR_hors_index_a_verifier':int(result.Documents_IR_collectes_a_verifier.sum()),
  'index_IR_sans_comptes':int(result.Index_IR_sans_comptes.sum()),
  'cotations_volumes_63s_disponibles':int(result.Volumes_monetaires_63s_disponibles.eq('OUI').sum()),
  'cotations_momentum_1_3_6_12_disponibles':int(result.Momentum_1_3_6_12_disponibles.eq('OUI').sum()),
  'cotations_passages_detention_groupe':int(pd.to_numeric(result.Passages_detention_groupe).gt(0).sum()),
  'cotations_avec_trois_documents':int((result.Rapport_10K_collecte.eq('OUI')&result.Rapport_10Q_collecte.eq('OUI')&result.Proxy_DEF14A_collecte.eq('OUI')).sum()),
  'notes_SSI_attribuees_par_ce_module':0,'candidats_selection_autorises':int(result.Candidat_selection_autorise.eq('OUI').sum()),
  'statut':'MATRICE_PREUVES_ET_INDEX_GOUVERNANCE_EXECUTES_CONTENU_A_QUALIFIER',
  'fichiers':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(bilan,ensure_ascii=False));return bilan
if __name__=='__main__':executer()

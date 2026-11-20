#!/usr/bin/env python3
"""Examine les dossiers momentum, confronte les actifs et exécute si admissible.
Reprend le calcul 40M, l'exécuteur 10 et le replay 05C ; aucun ordre réel.
"""
import argparse,csv,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import importlib.util
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
KEYS=['Variation_derniere_seance_pct','Variation_5_seances_pct','Momentum_1m_pct','Momentum_2m_pct','Momentum_3m_pct']
def load(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'SCRIPTS_ACTIFS'/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows,keys=None):
 keys=keys or list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def assess(row,event,friction):
 if row.get('Statut')!='CALCULABLE_ZONEBOURSE_VERIFIE':return 'DOSSIER_INCOMPLET'
 if event and event.get('type')=='OFFRE_NUMERAIRE':
  remaining=100*(event['prix_offre_devise']/float(row['Cours_devise'])-1)
  if remaining<=friction:return 'OFFRE_NUMERAIRE_ECART_INFERIEUR_AUX_FRAIS'
 if not all(float(row[k])>0 for k in KEYS):return 'MOMENTUM_NON_CONFIRME_SUR_CINQ_HORIZONS'
 if int(row['Volume_derniere_seance'])<=0:return 'VOLUME_NUL'
 return 'ADMISSIBLE_ACHAT'

def main(root=ROOT,asof=None,execute=False):
 asof=asof or datetime.now(timezone.utc);day=asof.astimezone(ZoneInfo('Europe/Paris')).date().isoformat();d=root/'DONNEES'
 config=json.loads((root/'CONFIG/CANDIDATS_EXTERNES_MOMENTUM.json').read_text())
 engine=load('40M_MOMENTUM_EXPERIENCE.py');engine.main(root,asof)
 adapter=load('40E_EXECUTER_MOMENTUM_VIRTUEL.py');rep=adapter.replay(root);state=rep.executer()
 active={str(p.Ticker):str(p.ID_position) for p in state['positions'][state['positions'].Statut=='ACTIF'].itertuples()}
 portfolio=[r for r in read(d/'EXPERIENCE_MOMENTUM_40.csv') if r['Ticker'] in active and r['Arbitrage_autorise']=='OUI']
 fees=read(root/'CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv');fees={x['Parametre']:x['Valeur'] for x in fees}
 ta=float(fees['Frais_achat'])/100;tv=float(fees['Frais_vente'])/100;friction=100*(1-(1-tv)/(1+ta))
 initials={r['Ticker'] for r in read(d/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv')}
 known_isins=set()
 for folder in (d/'ZONEBOURSE_NAVIGATEUR').glob('????-??-??'):
  if folder.name>day:continue
  for receipt in folder.glob('*.json'):
   raw=json.loads(receipt.read_text());match=re.search(r'\n([A-Z]{2}[A-Z0-9]{9}\d)\n',raw.get('body',''))
   if match:known_isins.add(match[1])
 registry={}
 for name in ['CHASSE_CANDIDATS.csv','SORTIE_CHASSEUR_EXISTANT.csv']:
  for x in read(d/name):
   if x['Ticker'] not in initials:registry[x['Ticker']]=x
 sources={x['ticker']:x for x in config['prioritaires']}
 for t,x in sources.items():
  source=registry.pop(x['alias_registre'],{})
  registry[t]=dict(source,**{'Ticker':t,'Societe':x['societe'],'Devise':x['devise'],'Alias_registre':x['alias_registre']})
 external=[];watch=[]
 for t,x in sorted(registry.items()):
  row={'Ticker':t,'Societe':x['Societe'].strip(),'Devise':x.get('Devise',''),'Alias_registre':x.get('Alias_registre',''),'Date_source_archive':x.get('Date_source',''),'Statut':'NON_COLLECTE_ACTUEL','Decision_externe':'DOSSIER_INCOMPLET','Manquants':'Identité/ISIN et cotation principale ; clôture attendue, volume, ancrages 1/5 séances et 1/2/3 mois, URL et preuve datée'}
  folders=sorted((d/'ZONEBOURSE_EXTERNES').glob('????-??-??'),reverse=True)
  p=next((p/(t+'.json') for p in folders if p.name<=day and (p/(t+'.json')).exists()),None)
  if p:
   try:
    raw=json.loads(p.read_text());isin=re.search(r'\n([A-Z]{2}[A-Z0-9]{9}\d)\n',raw['body'])
    if not isin:raise ValueError('ISIN non observé')
    if sources.get(t,{}).get('isin') and sources[t]['isin']!=isin[1]:raise ValueError('ISIN divergent')
    row.update(engine.calculate(raw,t,asof));row['ISIN']=isin[1];row['SHA256_preuve']=hashlib.sha256(p.read_bytes()).hexdigest()
    if row['Devise']!=x.get('Devise'):raise ValueError('Devise divergente')
    row['Decision_externe']=assess(row,config['evenements'].get(t),friction)
    if isin[1] in known_isins:row['Decision_externe']='DOUBLON_EMETTEUR_COHORTE_T0'
    row['Manquants']='' if row['Statut']=='CALCULABLE_ZONEBOURSE_VERIFIE' else row['Limites']
    external.append(row)
   except (ValueError,KeyError,IndexError) as e:row.update(Statut='PREUVE_INEXPLOITABLE',Manquants=str(e));external.append(row)
  if row['Statut']!='CALCULABLE_ZONEBOURSE_VERIFIE':
   row['Priorite_collecte']=0 if p else 1 if x.get('Alias_registre') else 2
   row['Date_prochaine_verification']=day;watch.append(row)
 watch.sort(key=lambda r:(r['Priorite_collecte'],r['Ticker']))
 write(d/'CANDIDATS_EXTERNES_MOMENTUM.csv',external,['Ticker','Societe','Statut','Decision_externe','Manquants'] if not external else None)
 write(d/'VIGILANCE_EXTERNES_QUOTIDIENNE.csv',watch)
 duels=[]
 for ext in external:
  for held in portfolio:
   better=tuple(float(ext[k]) for k in KEYS)>tuple(float(held[k]) for k in KEYS) if ext['Statut']=='CALCULABLE_ZONEBOURSE_VERIFIE' else False
   accepted=ext['Decision_externe']=='ADMISSIBLE_ACHAT' and better and all(float(held[k])<0 for k in KEYS)
   duels.append({'Titulaire':held['Ticker'],'Candidat':ext['Ticker'],'Decision':'ROTATION_POSSIBLE' if accepted else 'CONSERVER_TITULAIRE','Motif':ext['Decision_externe'] if not accepted else 'MOMENTUM_CONFIRME_PLUS_FORT','Friction_rotation_pct':friction})
 write(d/'CONFRONTATION_MOMENTUM_EXTERNES.csv',duels,['Titulaire','Candidat','Decision','Motif','Friction_rotation_pct'])
 journal=d/'JOURNAL_ARBITRAGES_GERE.csv';before=journal.read_bytes();ops=0
 mandate=config['mandat'];window=day==mandate['execution_exceptionnelle'] or asof.astimezone(ZoneInfo('Europe/Paris')).weekday()==mandate['jour_hebdomadaire']
 candidates=[x for x in external if x['Decision_externe']=='ADMISSIBLE_ACHAT' and x['Ticker'] not in active]
 candidates.sort(key=lambda r:tuple(float(r[k]) for k in KEYS),reverse=True)
 pair=None
 for ext in candidates:
  held=[r for r in portfolio if r['Devise']==ext['Devise'] and any(v['Titulaire']==r['Ticker'] and v['Candidat']==ext['Ticker'] and v['Decision']=='ROTATION_POSSIBLE' for v in duels)]
  if held:pair=max(held,key=lambda r:int(r['Rang_momentum'])),ext;break
 if execute and window and len(portfolio)>=35 and pair:
  source,destination=pair
  old=read(journal);opid='MC_'+day.replace('-','')+'_'+active[source['Ticker']]+'_SORTIE'
  if not any(x['ID_operation']==opid for x in old):
   fx=json.loads((d/'FX_REFERENCE_BCE_20261119.json').read_text())
   if any(r['Date_historique']!=fx['date'] for r in pair):raise ValueError('FX et clôtures de dates différentes')
   executor=load('10_EXECUTION_MENSUELLE.py');executor.JOURNAL=journal;executor.PARAMS=root/'CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv';oldload=executor.charger
   executor.charger=lambda n:adapter.replay(root) if n=='05C_REPLAY_PORTEFEUILLE_GERE.py' else oldload(n)
   context={'autorisation_date':day,'mode':'VIRTUEL_MOMENTUM_COMMANDE_UTILISATEUR','valides':len(portfolio),
    'prix':{r['Ticker']:float(r['Cours_devise']) for r in pair},'fx':{r['Devise']:{'fx_vers_eur':1/float(fx['par_eur'][r['Devise']])} for r in pair},
    'revue':[{'ID_position':'EXT_'+destination['Ticker'],'Societe':destination['Societe'],'Ticker':destination['Ticker'],'Devise':destination['Devise']}],
    'duels':pd.DataFrame([{'ID_position_source':active[source['Ticker']],'ID_position_destination':'EXT_'+destination['Ticker'],'Type_destination':'CHALLENGER','Part_allocation':1,'Statut_duel':'ALLOCATION_DETERMINEE'}]),
    'commentaire':'SIMULATION VIRTUELLE décision '+day+' sur clôtures connues du '+source['Date_historique']+' ; challenger externe '+destination['Source']+' ; aucune note MCPA/SSI.'}
   ops=len(executor.executer(momentum_context=context));rep.executer()
 result={'date_execution':day,'asof_utc':asof.isoformat(),'candidats_repertories':len(registry),'dossiers_relus':len(external),'dossiers_momentum_complets':sum(r['Statut']=='CALCULABLE_ZONEBOURSE_VERIFIE' for r in external),'admissibles_achat':len(candidates),'dossiers_incomplets':len(watch),'positions_actives':len(active),'titulaires_valides_actifs':len(portfolio),'duels_calcules':len(duels),'rotations_possibles':sum(r['Decision']=='ROTATION_POSSIBLE' for r in duels),'operations_ajoutees':ops,'journal_modifie':journal.read_bytes()!=before,'mode_execution_demande':execute,'fenetre_execution':window,'decision':'ARBITRAGE_VIRTUEL_EXECUTE' if ops else 'AUCUN_ACHAT_EXTERNE_ADMISSIBLE' if not candidates else 'PAS_DE_ROTATION_EXECUTABLE','strategie':'MOMENTUM_UNIQUEMENT','seuil':35,'exclusions_portefeuille':json.loads((d/'ETAT_MOMENTUM_QUOTIDIEN.json').read_text())['lignes_exclues'],'surveillance':'File complète réévaluée quotidiennement ; collecte navigateur progressive par priorité, sans prétendre avoir visité tous les dossiers.'}
 (d/'ETAT_CONFRONTATION_EXTERNES.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args();main(execute=args.execute)

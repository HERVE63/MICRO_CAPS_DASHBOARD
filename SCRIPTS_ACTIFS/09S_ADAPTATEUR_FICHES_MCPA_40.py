#!/usr/bin/env python3
"""Validate 40 JSON dossiers and export a review compatible with 09_CONTROLE_REVUE_MCPA_IPS.
Never replace the live review unless every dossier is complete and validated.
"""
import csv,json,math
from datetime import date
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
F=BASE/'DOSSIERS_MCPA_IPS_40'
D=BASE/'DONNEES'
COLS=['Date_revue','Type','ID_position','Societe','Ticker','Devise','SSI','Q','V','G','R','M','D','MCPA','IC','CX','Delta','WWWS','Catalyseurs','Risques','Scenario_bear','Prob_bear','Scenario_central','Prob_central','Scenario_bull','Prob_bull','Role_IPS','Challengers_compares','Decision','Condition_renforcement','Condition_allegement_sortie','Sources','Date_sources','Statut_analyse']
BLOCKS={'Q':'qualite','V':'valorisation','G':'croissance','R':'risque','M':'momentum','D':'diversification'}
def validation_individuelle(x):
 """Enforce existing SSI/MCPA limits and required review inputs before export."""
 issues=[];n=x['notation'];notes=n['notes'];comp=x['blocs']['complements']
 def numeric(v,lo,hi):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and lo<=v<=hi
 expected={'qualite':30,'valorisation':20,'croissance':20,'risque':10,'momentum':10,'diversification':10}
 if n['bareme']!=expected:issues.append('BAREME_DIVERGENT')
 for block,maximum in expected.items():
  if not numeric(notes.get(block),0,maximum):issues.append('SOUS_NOTE_INVALIDE:'+block)
  if not n.get('justifications',{}).get(block):issues.append('JUSTIFICATION_ABSENTE:'+block)
 if all(numeric(notes.get(b),0,m) for b,m in expected.items()):
  if not numeric(n.get('total_mcpa'),0,100) or abs(sum(notes.values())-n['total_mcpa'])>.01:issues.append('TOTAL_MCPA_INCOHERENT')
 required=['ssi','ic_sur_5','cx_sur_5','delta','wwws','role_ips','decision','condition_renforcement','condition_allegement_sortie','challengers_compares']
 for k in required:
  v=comp[k]['valeur']
  if v is None or (isinstance(v,str) and not v.strip()):issues.append('COMPLEMENT_MANQUANT:'+k)
 for k,lo,hi in [('ssi',0,100),('ic_sur_5',0,5),('cx_sur_5',0,5),('wwws',0,100)]:
  v=comp[k]['valeur']
  if v is not None and not numeric(v,lo,hi):issues.append('COMPLEMENT_HORS_BORNES:'+k)
 if numeric(comp['ssi']['valeur'],0,100) and comp['ssi']['valeur']<65:issues.append('SSI_SOUS_SEUIL_65')
 for horizon in ('3m','6m'):
  ps=[]
  for case in ('bear','central','bull'):
   k='scenario_'+case+'_'+horizon+'_pct';v=comp[k]['valeur']
   if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v):issues.append('SCENARIO_MANQUANT_OU_INVALIDE:'+k)
   k='prob_'+case+'_'+horizon+'_pct';v=comp[k]['valeur']
   if not numeric(v,0,100):issues.append('PROBABILITE_MANQUANTE_OU_INVALIDE:'+k)
   else:ps.append(v)
  if len(ps)==3 and abs(sum(ps)-100)>.1:issues.append('PROBABILITES_INCOHERENTES:'+horizon)
 for b,k in [('croissance','catalyseurs_dates'),('risque','risque_gouvernance')]:
  if not x['blocs'][b][k]['valeur']:issues.append('REVUE_CHAMP_MANQUANT:'+b+'.'+k)
 sources=sorted({c['source_url'] for block in x['blocs'].values() for c in block.values() if c.get('valeur') is not None and c.get('source_url')})
 if not sources:issues.append('SOURCES_ABSENTES')
 try:
  rd=date.fromisoformat(x['date_revue'])
  if rd.weekday()!=1:issues.append('REVUE_HORS_MARDI')
  if rd>date.today():issues.append('REVUE_FUTURE')
  if any(date.fromisoformat(c['date_source'])>rd for block in x['blocs'].values() for c in block.values() if c.get('valeur') is not None and c.get('date_source')):issues.append('SOURCES_POSTERIEURES_A_REVUE')
 except (ValueError,TypeError):issues.append('DATE_INVALIDE')
 decision=comp['decision']['valeur']
 if decision and decision not in {'RENFORCER','CONSERVER','ALLEGER','ALLÉGER','VENDRE','SONDE','INCUBATION','ATTENTE','SURVEILLER'}:issues.append('DECISION_NON_AUTORISEE')
 return issues
def main():
 paths=sorted(F.glob('*.json'))
 if len(paths)!=40:raise RuntimeError(f'Expected 40 dossiers, got {len(paths)}')
 with (D/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv').open(encoding='utf-8-sig',newline='') as f:positions={int(r['ID_position']):r for r in csv.DictReader(f)}
 if len(positions)!=40:raise RuntimeError('Initial holdings mismatch')
 audit=[];export=[]
 for p in paths:
  x=json.loads(p.read_text(encoding='utf-8'));n=x['id_position'];issues=[]
  original=positions.get(n)
  if not original or (x['ticker'],x['societe'],x['devise'])!=(original['Ticker'],original['Societe'],original['Devise']):issues.append('IDENTITE_DIVERGENTE')
  for block in ('identite','qualite','valorisation','croissance','risque','momentum','diversification','complements'):
   if block not in x['blocs']:issues.append('BLOC_ABSENT:'+block)
  for block in x['blocs'].values():
   for key,cell in block.items():
    if not isinstance(cell,dict) or not {'valeur','unite','periode','date_source','source_url','statut','commentaire'}.issubset(cell):issues.append('SCHEMA_CHAMP:'+key)
  issues.extend(validation_individuelle(x))
  notes=x['notation']['notes']
  if x['notation']['statut']!='VALIDEE':issues.append('NOTATION_NON_VALIDEE')
  if any(notes.get(block) is None for block in BLOCKS.values()):issues.append('SOUS_NOTES_MANQUANTES')
  if x['notation']['total_mcpa'] is None:issues.append('TOTAL_MCPA_MANQUANT')
  if x['arbitrage_autorise'] is not True:issues.append('ARBITRAGE_NON_AUTORISE')
  audit.append({'ID_position':n,'Ticker':x['ticker'],'Statut':'PRET' if not issues else 'INCOMPLET','Problemes':' | '.join(issues)})
  if not issues:
   c=x['blocs']['complements'];v=lambda k:c[k]['valeur']
   row={'Date_revue':x['date_revue'],'Type':'TITULAIRE','ID_position':n,'Societe':x['societe'],'Ticker':x['ticker'],'Devise':x['devise'],'SSI':v('ssi'),'Q':notes['qualite'],'V':notes['valorisation'],'G':notes['croissance'],'R':notes['risque'],'M':notes['momentum'],'D':notes['diversification'],'MCPA':x['notation']['total_mcpa'],'IC':v('ic_sur_5'),'CX':v('cx_sur_5'),'Delta':v('delta'),'WWWS':v('wwws'),'Catalyseurs':x['blocs']['croissance']['catalyseurs_dates']['valeur'],'Risques':x['blocs']['risque']['risque_gouvernance']['valeur'],'Scenario_bear':v('scenario_bear_6m_pct'),'Prob_bear':v('prob_bear_6m_pct'),'Scenario_central':v('scenario_central_6m_pct'),'Prob_central':v('prob_central_6m_pct'),'Scenario_bull':v('scenario_bull_6m_pct'),'Prob_bull':v('prob_bull_6m_pct'),'Role_IPS':v('role_ips'),'Challengers_compares':v('challengers_compares'),'Decision':v('decision'),'Condition_renforcement':v('condition_renforcement'),'Condition_allegement_sortie':v('condition_allegement_sortie'),'Sources':' | '.join(sorted({c['source_url'] for block in x['blocs'].values() for c in block.values() if c.get('valeur') is not None and c.get('source_url')})),'Date_sources':max(c['date_source'] for block in x['blocs'].values() for c in block.values() if c.get('valeur') is not None and c.get('date_source')),'Statut_analyse':'VALIDE'}
   export.append(row)
 with (D/'AUDIT_DOSSIERS_MCPA_IPS_40.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=['ID_position','Ticker','Statut','Problemes']);w.writeheader();w.writerows(sorted(audit,key=lambda r:r['ID_position']))
 # Export de diagnostic distinct : jamais consomme par le validateur 09 ni les duels.
 # Conserve uniquement les fiches individuellement admissibles, sans modifier la revue officielle.
 with (D/'FICHES_MCPA_IPS_ELIGIBLES_40.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=COLS);w.writeheader();w.writerows(sorted(export,key=lambda r:int(r['ID_position'])))
 print(f'Couverture individuelle prouvee : {len(export)}/40 ; arbitrage verrouille tant que la revue stricte echoue')
 if len(export)==40:
  with (D/'REVUE_HEBDOMADAIRE_MCPA_IPS.csv').open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=COLS);w.writeheader();w.writerows(sorted(export,key=lambda r:int(r['ID_position'])))
  print('40 dossiers validated and exported')
 else:
  print(f'{len(export)}/40 dossiers eligible; review unchanged')
 return len(export)
if __name__=='__main__':main()

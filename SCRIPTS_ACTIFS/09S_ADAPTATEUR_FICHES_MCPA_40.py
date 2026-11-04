#!/usr/bin/env python3
"""Validate 40 JSON dossiers and export a review compatible with 09_CONTROLE_REVUE_MCPA_IPS.
Never replace the live review unless every dossier is complete and validated.
"""
import csv,json,math
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
F=BASE/'DOSSIERS_MCPA_IPS_40'
D=BASE/'DONNEES'
COLS=['Date_revue','Type','ID_position','Societe','Ticker','Devise','SSI','Q','V','G','R','M','D','MCPA','IC','CX','Delta','WWWS','Catalyseurs','Risques','Scenario_bear','Prob_bear','Scenario_central','Prob_central','Scenario_bull','Prob_bull','Role_IPS','Challengers_compares','Decision','Condition_renforcement','Condition_allegement_sortie','Sources','Date_sources','Statut_analyse']
BLOCKS={'Q':'qualite','V':'valorisation','G':'croissance','R':'risque','M':'momentum','D':'diversification'}
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
  notes=x['notation']['notes']
  if x['notation']['statut']!='VALIDEE':issues.append('NOTATION_NON_VALIDEE')
  if any(notes.get(block) is None for block in BLOCKS.values()):issues.append('SOUS_NOTES_MANQUANTES')
  if x['notation']['total_mcpa'] is None:issues.append('TOTAL_MCPA_MANQUANT')
  if x['arbitrage_autorise'] is not True:issues.append('ARBITRAGE_NON_AUTORISE')
  audit.append({'ID_position':n,'Ticker':x['ticker'],'Statut':'PRET' if not issues else 'INCOMPLET','Problemes':' | '.join(issues)})
  if not issues:
   c=x['blocs']['complements'];v=lambda k:c[k]['valeur']
   row={'Date_revue':x['date_revue'],'Type':'TITULAIRE','ID_position':n,'Societe':x['societe'],'Ticker':x['ticker'],'Devise':x['devise'],'SSI':v('ssi'),'Q':notes['qualite'],'V':notes['valorisation'],'G':notes['croissance'],'R':notes['risque'],'M':notes['momentum'],'D':notes['diversification'],'MCPA':x['notation']['total_mcpa'],'IC':v('ic_sur_5'),'CX':v('cx_sur_5'),'Delta':v('delta'),'WWWS':v('wwws'),'Catalyseurs':x['blocs']['croissance']['catalyseurs_dates']['valeur'],'Risques':x['blocs']['risque']['risque_gouvernance']['valeur'],'Scenario_bear':v('scenario_bear_6m_pct'),'Prob_bear':v('prob_bear_6m_pct'),'Scenario_central':v('scenario_central_6m_pct'),'Prob_central':v('prob_central_6m_pct'),'Scenario_bull':v('scenario_bull_6m_pct'),'Prob_bull':v('prob_bull_6m_pct'),'Role_IPS':v('role_ips'),'Challengers_compares':v('challengers_compares'),'Decision':v('decision'),'Condition_renforcement':v('condition_renforcement'),'Condition_allegement_sortie':v('condition_allegement_sortie'),'Sources':' | '.join(e.get('url','') for e in x['preuves_complementaires']),'Date_sources':x['date_revue'],'Statut_analyse':'VALIDE'}
   export.append(row)
 with (D/'AUDIT_DOSSIERS_MCPA_IPS_40.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=['ID_position','Ticker','Statut','Problemes']);w.writeheader();w.writerows(sorted(audit,key=lambda r:r['ID_position']))
 if len(export)==40:
  with (D/'REVUE_HEBDOMADAIRE_MCPA_IPS.csv').open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=COLS);w.writeheader();w.writerows(sorted(export,key=lambda r:int(r['ID_position'])))
  print('40 dossiers validated and exported')
 else:
  print(f'{len(export)}/40 dossiers eligible; review unchanged')
 return len(export)
if __name__=='__main__':main()

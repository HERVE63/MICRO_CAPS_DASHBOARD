#!/usr/bin/env python3
"""Adaptateur momentum vers l'exécuteur 10 et le replay 05C existants.
Commande virtuelle ponctuelle, aucune connexion à un courtier.
"""
import argparse,hashlib,importlib.util,json,math
from datetime import date,datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
KEYS=['Variation_derniere_seance_pct','Variation_5_seances_pct','Momentum_1m_pct','Momentum_2m_pct','Momentum_3m_pct']

def load(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'SCRIPTS_ACTIFS'/name)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def replay(root):
 m=load('05C_REPLAY_PORTEFEUILLE_GERE.py')
 m.INITIAL=root/'DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv'
 m.JOURNAL=root/'DONNEES/JOURNAL_ARBITRAGES_GERE.csv'
 m.PARAMS_ARBITRAGE=root/'CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv'
 m.OUTPUT=root/'DONNEES/TEST_ETAT_GERE_RECONSTRUIT.csv'
 return m

def select_pair(rows,active):
 valid=[r for r in rows if r.get('Arbitrage_autorise')=='OUI' and r['Ticker'] in active]
 winners=sorted([r for r in valid if all(float(r[k])>0 for k in KEYS)],key=lambda r:int(r['Rang_momentum']))
 for winner in winners:
  losers=[r for r in valid if r['Devise']==winner['Devise'] and all(float(r[k])<0 for k in KEYS)]
  if losers:return max(losers,key=lambda r:int(r['Rang_momentum'])),winner
 return None

class RotationIndisponible(ValueError):
 pass

def load_fx(data_dir, price_date, currency):
 suffix=date.fromisoformat(price_date).strftime('%Y%m%d')
 path=data_dir/f'FX_REFERENCE_BCE_{suffix}.json'
 try:
  fx=json.loads(path.read_text())
  rate=1.0 if currency=='EUR' else float(fx['par_eur'][currency])
 except (OSError,ValueError,KeyError,TypeError) as exc:
  raise RotationIndisponible(f'Référence BCE {currency} du {price_date} absente ou invalide') from exc
 if fx.get('date')!=price_date or not math.isfinite(rate) or rate<=0:
  raise RotationIndisponible(f'Référence BCE {currency} du {price_date} invalide')
 return fx,rate

def revue_24(root=ROOT,asof=None):
 asof=asof or datetime.now(timezone.utc)
 paris=asof.astimezone(ZoneInfo('Europe/Paris'))
 if paris.date().isoformat()!='2026-11-24' or paris.hour<19:
  return None
 d=root/'DONNEES'
 ready=d/'REVUE_MOMENTUM_PRETE_20261124.json'
 if not ready.exists():
  return None
 if json.loads(ready.read_text()).get('date_prix')!='2026-11-23':
  raise ValueError('Date de clôture incorrecte dans le signal de la revue')
 try:
  result=execute(root,asof,authorization='AUTORISATION_MOMENTUM_VIRTUEL_20261124.json')
  result=dict(result,statut='EXECUTEE')
 except RotationIndisponible as exc:
  result={'date_decision':'2026-11-24','date_prix':'2026-11-23',
          'statut':'SANS_ROTATION','motif':str(exc),'operations_ajoutees':0}
 (d/'REVUE_MOMENTUM_INTERNE_20261124.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False))
 return result

def execute(root=ROOT,asof=None,authorization='AUTORISATION_MOMENTUM_VIRTUEL.json'):
 asof=asof or datetime.now(timezone.utc);day=asof.astimezone(ZoneInfo('Europe/Paris')).date().isoformat()
 auth=json.loads((root/'CONFIG'/authorization).read_text())
 if auth['date']!=day or auth['maximum_rotations']!=1 or auth['type']!='COMMANDE_UTILISATEUR_VIRTUELLE':
  raise ValueError('Commande virtuelle datée absente')
 d=root/'DONNEES';journal=d/'JOURNAL_ARBITRAGES_GERE.csv';before=journal.read_bytes()
 audit=d/('ARBITRAGE_MOMENTUM_'+day+'.json')
 existing=pd.read_csv(journal)
 prefix='MC_'+day.replace('-','')+'_'
 if any(str(x).startswith(prefix) for x in existing['ID_operation']):
  if not audit.exists():raise ValueError('Opérations présentes sans preuve : aucune répétition')
  prior=json.loads(audit.read_text())
  if prior['journal_apres_sha256']!=sha(journal):raise ValueError('Journal différent de la preuve précédente')
  replay(root).executer()
  print('IDEMPOTENT : aucune nouvelle transaction')
  return prior
 protected=[d/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv',d/'COHORTE_MICRO_CAPS_T0.csv']
 initial_hash={str(p):sha(p) for p in protected}
 engine=load('40M_MOMENTUM_EXPERIENCE.py');report=engine.main(root,asof)
 if not report['arbitrage_autorise']:raise RotationIndisponible(f"Seuil de 35/40 non atteint ({report['lectures_exploitables']}/40)")
 state=replay(root).executer();positions=state['positions']
 active={r.Ticker:str(r.ID_position) for r in positions[positions.Statut=='ACTIF'].itertuples()}
 rows=engine.read(d/'EXPERIENCE_MOMENTUM_40.csv');pair=select_pair(rows,active)
 if pair is None:raise RotationIndisponible('Aucun couple de titulaires confirmé sur cinq horizons et dans la même devise')
 outgoing,incoming=pair
 if any(row['Date_historique']!=auth['date_prix'] for row in pair):
  raise RotationIndisponible(f"Clôtures attendues le {auth['date_prix']} pour les deux titres")
 currency=outgoing['Devise']
 fx_data,rate=load_fx(d,auth['date_prix'],currency)
 context={'autorisation_date':day,'mode':'VIRTUEL_MOMENTUM_COMMANDE_UTILISATEUR','valides':report['lectures_exploitables'],
  'prix':{r['Ticker']:float(r['Cours_devise']) for r in pair},'fx':{currency:{'fx_vers_eur':1/rate}},
  'duels':pd.DataFrame([{'ID_position_source':active[outgoing['Ticker']],'ID_position_destination':active[incoming['Ticker']],
   'Type_destination':'TITULAIRE','Part_allocation':1.0,'Statut_duel':'ALLOCATION_DETERMINEE'}]),
  'commentaire':'SIMULATION VIRTUELLE sur clôtures du '+outgoing['Date_historique']+' connues lors de la décision du '+day+
   '; aucun remplissage réel ni backtest causal ; même devise, FX BCE de référence pour comptabilité EUR ; prix et preuves : '+
   ' | '.join(r['Source']+' SHA256 '+r['SHA256_preuve'] for r in pair)}
 exe=load('10_EXECUTION_MENSUELLE.py');exe.JOURNAL=journal;exe.PARAMS=root/'CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv'
 original=exe.charger
 exe.charger=lambda name:replay(root) if name=='05C_REPLAY_PORTEFEUILLE_GERE.py' else original(name)
 added=exe.executer(momentum_context=context)
 if len(added)!=2:raise RuntimeError('Deux écritures attendues pour une rotation')
 after_state=replay(root).executer()
 for ticker in report['lignes_exclues']:
  a=positions[positions.Ticker==ticker];b=after_state['positions'][after_state['positions'].Ticker==ticker]
  if a.Quantite.tolist()!=b.Quantite.tolist():raise RuntimeError('Position exclue modifiée')
 if any(sha(p)!=initial_hash[str(p)] for p in protected):raise RuntimeError('Référence T0 modifiée')
 if not journal.read_bytes().startswith(before.rstrip(b'\r\n')):raise RuntimeError('Journal non append-only')
 result={'date_decision':day,'date_execution_virtuelle':day,'date_prix':outgoing['Date_historique'],
  'mode':'SIMULATION_SUR_CLOTURES_DE_LA_VEILLE','rotation':{'sortie':outgoing['Ticker'],'renforcement':incoming['Ticker']},
  'selection':'Une rotation maximale ; destination positive aux cinq horizons ; source négative aux cinq, même devise, dernière du classement priorisant dernière séance.',
  'operations_ajoutees':len(added),'operations':added.fillna('').to_dict('records'),
  'frais_EUR':float(added.Frais_sortie_EUR.replace('',0).fillna(0).astype(float).sum()+added.Frais_entree_EUR.replace('',0).fillna(0).astype(float).sum()),
  'cash_final_EUR':after_state['cash'],'positions_actives':after_state['nb_actives'],'exclusions_conservees':report['lignes_exclues'],
  'journal_avant_sha256':hashlib.sha256(before).hexdigest(),'journal_apres_sha256':sha(journal),'references_T0_sha256':initial_hash,
  'source_FX':fx_data,'temoin':'STATIQUE_INCHANGE','ordre_reel':False}
 audit.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False));return result

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--revue-24',action='store_true')
 if parser.parse_args().revue_24:
  revue_24()
 else:
  execute()

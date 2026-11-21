import importlib.util,json,csv
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('external',ROOT/'SCRIPTS_ACTIFS/41M_CONFRONTATION_EXTERNES.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def test_no_entry_on_stale_or_incomplete_quote():
 assert m.assess({'Statut':'HISTORIQUE_PERIME'},None,4.878)=='DOSSIER_INCOMPLET'

def test_offer_near_cash_price_does_not_turn_historical_jump_into_profit():
 row={'Statut':'CALCULABLE_ZONEBOURSE_VERIFIE','Cours_devise':2.34}
 assert m.assess(row,{'type':'OFFRE_NUMERAIRE','prix_offre_devise':2.35},4.878)=='OFFRE_NUMERAIRE_ECART_INFERIEUR_AUX_FRAIS'

def test_actual_external_review_preserves_ledger_and_publishes_all_incomplete_tickers(tmp_path):
 import shutil
 d=tmp_path/'DONNEES';d.mkdir();c=tmp_path/'CONFIG';c.mkdir()
 for name in ['ETAT_INITIAL_PORTEFEUILLE_GERE.csv','COHORTE_MICRO_CAPS_T0.csv','CHASSE_CANDIDATS.csv','SORTIE_CHASSEUR_EXISTANT.csv','FX_REFERENCE_BCE_20261119.json']:
  shutil.copy(ROOT/'DONNEES'/name,d/name)
 for name in ['PARAMETRES_ARBITRAGE_MICRO_CAPS.csv','CONTROLES_MARCHE_DOCUMENTES.json','CANDIDATS_EXTERNES_MOMENTUM.json']:
  shutil.copy(ROOT/'CONFIG'/name,c/name)
 for directory in ['ZONEBOURSE_NAVIGATEUR','ZONEBOURSE_EXTERNES']:
  shutil.copytree(ROOT/'DONNEES'/directory/'2026-11-20',d/directory/'2026-11-20')
 proof=json.loads((ROOT/'DONNEES/ARBITRAGE_MOMENTUM_2026-11-20.json').read_text())
 ledger=d/'JOURNAL_ARBITRAGES_GERE.csv'
 fields=(ROOT/'DONNEES/JOURNAL_ARBITRAGES_GERE.csv').read_text().splitlines()[0].split(',')
 with ledger.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(proof['operations'])
 before=ledger.read_bytes()
 r=m.main(tmp_path,datetime(2026,11,20,20,tzinfo=timezone.utc),execute=False)
 assert r['dossiers_relus']==4 and r['dossiers_momentum_complets']==4
 assert r['titulaires_valides_actifs']==37 and r['positions_actives']==39
 assert r['duels_calcules']==148 and r['admissibles_achat']==0
 assert r['dossiers_incomplets']==len(m.read(d/'VIGILANCE_EXTERNES_QUOTIDIENNE.csv'))
 assert ledger.read_bytes()==before

def test_existing_executor_supports_new_external_entry_without_synthetic_mcpa(tmp_path):
 # All prices and the challenger in this test are SYNTHETIC, isolated from live data.
 initial=tmp_path/'initial.csv';initial.write_bytes((ROOT/'DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv').read_bytes())
 ledger=tmp_path/'journal.csv';ledger.write_text((ROOT/'DONNEES/JOURNAL_ARBITRAGES_GERE.csv').read_text().splitlines()[0]+'\n')
 out=tmp_path/'replay.csv';adapter=m.load('40E_EXECUTER_MOMENTUM_VIRTUEL.py')
 def get_replay():
  r=m.load('05C_REPLAY_PORTEFEUILLE_GERE.py');r.INITIAL=initial;r.JOURNAL=ledger;r.OUTPUT=out;return r
 executor=m.load('10_EXECUTION_MENSUELLE.py');executor.JOURNAL=ledger
 original=executor.charger;executor.charger=lambda n:get_replay() if n=='05C_REPLAY_PORTEFEUILLE_GERE.py' else original(n)
 now=datetime(2026,11,20,20,tzinfo=timezone.utc);executor.datetime=SimpleNamespace(now=lambda tz:now.astimezone(tz))
 context={'autorisation_date':'2026-11-20','mode':'VIRTUEL_MOMENTUM_COMMANDE_UTILISATEUR','valides':35,
 'prix':{'IDN':10,'SYNTHETIC_TEST_ONLY':10},'fx':{'USD':{'fx_vers_eur':1}},'commentaire':'FIXTURE SYNTHETIQUE ISOLÉE',
 'revue':[{'ID_position':'EXT_TEST','Societe':'SYNTHETIC TEST ONLY','Ticker':'SYNTHETIC_TEST_ONLY','Devise':'USD'}],
 'duels':pd.DataFrame([{'ID_position_source':'1','ID_position_destination':'EXT_TEST','Type_destination':'CHALLENGER','Part_allocation':1,'Statut_duel':'ALLOCATION_DETERMINEE'}])}
 added=executor.executer(momentum_context=context);state=get_replay().executer()
 assert len(added)==2 and added.iloc[1].Type_operation=='ENTREE'
 assert state['nb_actives']==40 and state['cash']==pytest.approx(0)
 assert 'SYNTHETIC_TEST_ONLY' in state['positions'].Ticker.tolist()
 assert pd.read_csv(ledger).SSI.isna().all()

@pytest.mark.parametrize('isin_correct',[True,False])
def test_hvivo_legacy_symbol_requires_verified_isin(isin_correct):
 # Reçu réel daté, sans transformation des cours ni du symbole de la source.
 raw=json.loads((ROOT/'DONNEES/ZONEBOURSE_EXTERNES/2026-11-21/HVO.L.json').read_text())
 if not isin_correct:raw['body']=raw['body'].replace('GB00B9275X97','GB0000000000')
 engine=m.load('40M_MOMENTUM_EXPERIENCE.py')
 if not isin_correct:
  with pytest.raises(ValueError,match='Ticker'):engine.calculate(raw,'HVO.L',datetime(2026,11,21,23,59,tzinfo=timezone.utc))
 else:
  result=engine.calculate(raw,'HVO.L',datetime(2026,11,21,23,59,tzinfo=timezone.utc))
  assert result['Statut']=='CALCULABLE_ZONEBOURSE_VERIFIE'
  assert result['Devise']=='GBP' and result['Cours_devise']==pytest.approx(.0455)

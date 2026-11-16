"""Real browser receipts + isolation of current data from historical archives."""
import csv,copy,hashlib,importlib.util,sys
from pathlib import Path
from datetime import datetime,timezone
import json,pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('momentum40',ROOT/'SCRIPTS_ACTIFS/40M_MOMENTUM_EXPERIENCE.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ASOF=datetime(2026,11,15,20,tzinfo=timezone.utc)
SOURCE=ROOT/'DONNEES/ZONEBOURSE_NAVIGATEUR/2026-11-15'
def record(t='IDN'):return json.loads((SOURCE/(t+'.json')).read_text())
def test_actual_browser_prices_and_calendar_anchors():
 r=m.calculate(record(),'IDN',ASOF)
 assert r['Statut']=='CALCULABLE_ZONEBOURSE_VERIFIE'
 assert r['Volume_derniere_seance']==479914
 assert r['Variation_derniere_seance_pct']==pytest.approx((1.86/2.24-1)*100)
 assert r['Variation_5_seances_pct']==pytest.approx((1.86/2.04-1)*100)
 assert r['Momentum_1m_pct']==pytest.approx((1.86/2.30-1)*100)
 assert r['Momentum_2m_pct']==pytest.approx((1.86/2.60-1)*100)
 assert r['Momentum_3m_pct']==pytest.approx((1.86/3.75-1)*100)
 assert json.loads(r['Ancrages'])['2m']['date']=='2026-09-11'
 assert 'performance synthétique différente' in r['Limites']
 assert r['Signal']=='DIRECTION_BAISSIERE'
def test_real_infu_deceleration():
 r=m.calculate(record('INFU'),'INFU',ASOF)
 assert r['Variation_derniere_seance_pct']<0<r['Variation_5_seances_pct']
 assert r['Signal']=='DECELERATION_A_SURVEILLER'
 assert r['Momentum_1m_pct']==pytest.approx((14.72/13.49-1)*100)

def test_intraday_missing_current_bar_keeps_last_closed_volume():
 x=record();x['body']=x['body'].replace('Marché Fermé','Temps réel').replace('22:00:00 13/11/2026','15:10:00 16/11/2026')
 x['consulted_at']='2026-11-16T14:15:00+00:00'
 r=m.calculate(x,'IDN',datetime(2026,11,16,14,15,tzinfo=timezone.utc))
 assert r['Nature_cotation']=='INTRADAY'
 assert r['Date_volume_derniere_seance']=='2026-11-13'
 assert r['Volume_derniere_seance']==479914
 assert r['Statut']=='INCOMPLET_SANS_SIGNAL'
 assert r['Signal']=='DONNEES_INSUFFISANTES'
def test_real_london_closing_price_without_intraday_time():
 r=m.calculate(record('MTEC.L'),'MTEC.L',ASOF)
 assert r['Statut']=='CALCULABLE_ZONEBOURSE_VERIFIE'
 assert r['Nature_cotation']=='CLOTURE' and r['Heure_cotation_source'] is None
 assert r['Cours_devise']==pytest.approx(.52) and r['Devise']=='GBP'
def test_old_receipt_never_becomes_current():
 r=m.calculate(record(),'IDN',datetime(2026,11,16,23,tzinfo=timezone.utc))
 assert r['Statut']=='HISTORIQUE_PERIME'
 assert r['Signal']=='DONNEES_PERIMEES_SANS_ARBITRAGE'
def test_missing_anchor_is_not_nearest_future_date():
 x=record();x['history']=[h for h in x['history'] if h['requested']!='2026-09-13']
 r=m.calculate(x,'IDN',ASOF)
 assert r['Momentum_2m_pct'] is None and r['Statut']=='INCOMPLET_SANS_SIGNAL'
def test_conflicting_and_future_bars_rejected():
 x=record();x['history'].append({'text':'13/11/2026\t1\t2\t1\t1,5\t100\t1%'})
 with pytest.raises(ValueError,match='contradictoire'):m.calculate(x,'IDN',ASOF)
 x=record();x['history'].append({'text':'16/11/2026\t1\t2\t1\t1,5\t100\t1%'})
 with pytest.raises(ValueError,match='postérieure'):m.calculate(x,'IDN',ASOF)
def test_wrong_issuer_or_non_browser_source_rejected():
 with pytest.raises(ValueError,match='identité'):m.calculate(record(),'INFU',ASOF)
 x=record();x['method']='ARCHIVES_YAHOO'
 with pytest.raises(ValueError,match='lecture'):m.calculate(x,'IDN',ASOF)
def test_no_stale_yahoo_fallback_and_no_transactions(tmp_path):
 d=tmp_path/'DONNEES';d.mkdir()
 for name in ['ETAT_INITIAL_PORTEFEUILLE_GERE.csv','JOURNAL_ARBITRAGES_GERE.csv']:(d/name).write_bytes((ROOT/'DONNEES'/name).read_bytes())
 # Poison archive: it must never be read or promoted to a verified quote.
 (d/'HISTORIQUES_YAHOO_40.csv').write_text('this is deliberately not valid market data')
 h=hashlib.sha256((d/'JOURNAL_ARBITRAGES_GERE.csv').read_bytes()).hexdigest()
 report=m.main(tmp_path,ASOF,d/'ZONEBOURSE_NAVIGATEUR/2026-11-15')
 assert report['lectures_exploitables']==0
 rows=m.read(d/'EXPERIENCE_MOMENTUM_40.csv')
 assert len(rows)==40 and all(r['Statut']=='NON_COLLECTE' and not r['Rang_momentum'] for r in rows)
 assert hashlib.sha256((d/'JOURNAL_ARBITRAGES_GERE.csv').read_bytes()).hexdigest()==h
 assert report['friction_vente_achat_pct']==pytest.approx(4.8780487804878)
def test_two_replays_identical_without_order(tmp_path):
 import shutil
 d=tmp_path/'DONNEES';d.mkdir()
 for name in ['ETAT_INITIAL_PORTEFEUILLE_GERE.csv','JOURNAL_ARBITRAGES_GERE.csv']:(d/name).write_bytes((ROOT/'DONNEES'/name).read_bytes())
 s=d/'ZONEBOURSE_NAVIGATEUR/2026-11-15';s.mkdir(parents=True)
 for name in ['IDN.json','INFU.json','MANIFESTE.json']:shutil.copy2(SOURCE/name,s/name)
 first=m.main(tmp_path,ASOF,s);csv1=(d/'EXPERIENCE_MOMENTUM_40.csv').read_bytes();second=m.main(tmp_path,ASOF,s)
 assert first==second and csv1==(d/'EXPERIENCE_MOMENTUM_40.csv').read_bytes()
 assert first['lectures_exploitables']==2 and first['transactions']==0
 assert all(r['Arbitrage_autorise']=='NON' for r in m.read(d/'EXPERIENCE_MOMENTUM_40.csv'))
def test_direction_change_is_recomputed_from_previous_session():
 r=m.calculate(record(),'IDN',ASOF)
 assert r['Signal_seance_precedente']=='DECELERATION_A_SURVEILLER'
 assert r['Changement_direction']=='OUI'
 r=m.calculate(record('INFU'),'INFU',ASOF)
 assert r['Changement_direction']=='NON'
def test_pence_are_not_pounds():
 x=record();x['body']=x['body'].replace('1,860 USD','1,860 GBp')
 assert m.calculate(x,'IDN',ASOF)['Cours_devise']==pytest.approx(.0186)
 x['body']=x['body'].replace('1,860 GBp','1,860 GBP')
 assert m.calculate(x,'IDN',ASOF)['Cours_devise']==pytest.approx(1.86)

def test_suspension_requires_documented_resumption():
 controls=json.loads((ROOT/'CONFIG/CONTROLES_MARCHE_DOCUMENTES.json').read_text())
 assert m.market_block(controls,'PULS.L',ASOF)['derniere_cotation']=='2026-10-27'
 assert m.market_block(controls,'IDN',ASOF) is None
 assert m.market_block(controls,'PULS.L',datetime(2026,10,27,20,tzinfo=timezone.utc)) is None
 controls=copy.deepcopy(controls);controls[0]['date_reprise']='2026-11-16'
 assert m.market_block(controls,'PULS.L',ASOF) is not None
 assert m.market_block(controls,'PULS.L',datetime(2026,11,16,20,tzinfo=timezone.utc)) is None

def test_current_looking_quote_does_not_override_suspension(tmp_path,monkeypatch):
 import shutil
 d=tmp_path/'DONNEES';d.mkdir();c=tmp_path/'CONFIG';c.mkdir()
 for name in ['ETAT_INITIAL_PORTEFEUILLE_GERE.csv','JOURNAL_ARBITRAGES_GERE.csv']:(d/name).write_bytes((ROOT/'DONNEES'/name).read_bytes())
 (c/'CONTROLES_MARCHE_DOCUMENTES.json').write_bytes((ROOT/'CONFIG/CONTROLES_MARCHE_DOCUMENTES.json').read_bytes())
 s=d/'ZONEBOURSE_NAVIGATEUR/2026-11-15';s.mkdir(parents=True)
 for name in ['IDN.json','INFU.json','MANIFESTE.json']:shutil.copy2(SOURCE/name,s/name)
 (s/'PULS.L.json').write_text('{}')
 actual_calculate=m.calculate
 def candidate(receipt,ticker,asof):
  if ticker!='PULS.L':return actual_calculate(receipt,ticker,asof)
  return dict(actual_calculate(record(),'IDN',asof),Devise='GBP')
 monkeypatch.setattr(m,'calculate',candidate)
 report=m.main(tmp_path,ASOF,s)
 rows=m.read(d/'EXPERIENCE_MOMENTUM_40.csv');puls=next(r for r in rows if r['Ticker']=='PULS.L')
 assert report['lectures_exploitables']==2 and report['suspensions_documentees']==['PULS.L']
 assert puls['Statut']=='COTATION_NON_NEGOCIABLE' and not puls['Rang_momentum']
 assert puls['Signal']=='MARCHE_SUSPENDU_SANS_ARBITRAGE' and puls['Arbitrage_autorise']=='NON'
 prep=next(r for r in m.read(d/'PREPARATION_HEBDOMADAIRE_MOMENTUM_40.csv') if r['Ticker']=='PULS.L')
 assert prep['Preparation']=='SUSPENSION_NE_PAS_ARBITRER' and prep['Operation_virtuelle']=='AUCUNE'

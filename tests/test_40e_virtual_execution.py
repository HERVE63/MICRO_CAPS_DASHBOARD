import importlib.util,json,shutil
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('exec40',ROOT/'SCRIPTS_ACTIFS/40E_EXECUTER_MOMENTUM_VIRTUEL.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ASOF=datetime(2026,11,20,20,tzinfo=timezone.utc)

def test_selection_ignores_one_day_rebounds_and_excluded_rows():
 rows=list(__import__('csv').DictReader(open(ROOT/'DONNEES/EXPERIENCE_MOMENTUM_40.csv')))
 pair=m.select_pair(rows,{r['Ticker'] for r in rows})
 assert [r['Ticker'] for r in pair]==['SFT.L','MTEC.L']
 pair[1]['Arbitrage_autorise']='NON'
 assert m.select_pair(rows,{r['Ticker'] for r in rows}) is None

def setup(tmp):
 d=tmp/'DONNEES';d.mkdir();c=tmp/'CONFIG';c.mkdir()
 for name in ['ETAT_INITIAL_PORTEFEUILLE_GERE.csv','COHORTE_MICRO_CAPS_T0.csv','FX_REFERENCE_BCE_20261119.json']:
  shutil.copy(ROOT/'DONNEES'/name,d/name)
 # Isolated ledger starts at T0, regardless of the live experiment's history.
 (d/'JOURNAL_ARBITRAGES_GERE.csv').write_text((ROOT/'DONNEES/JOURNAL_ARBITRAGES_GERE.csv').read_text().splitlines()[0]+'\n')
 for name in ['PARAMETRES_ARBITRAGE_MICRO_CAPS.csv','CONTROLES_MARCHE_DOCUMENTES.json','AUTORISATION_MOMENTUM_VIRTUEL.json']:
  shutil.copy(ROOT/'CONFIG'/name,c/name)
 shutil.copytree(ROOT/'DONNEES/ZONEBOURSE_NAVIGATEUR/2026-11-20',d/'ZONEBOURSE_NAVIGATEUR/2026-11-20')
 return d

def test_real_receipts_execute_through_10_and_05c_once(tmp_path,monkeypatch):
 d=setup(tmp_path);original_load=m.load
 def loader(name):
  x=original_load(name)
  if name=='10_EXECUTION_MENSUELLE.py':x.datetime=SimpleNamespace(now=lambda tz:ASOF.astimezone(tz))
  return x
 monkeypatch.setattr(m,'load',loader)
 before=pd.read_csv(d/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv');protected=(d/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv').read_bytes()
 result=m.execute(tmp_path,ASOF)
 assert result['rotation']=={'sortie':'SFT.L','renforcement':'MTEC.L'}
 assert result['operations_ajoutees']==2 and result['cash_final_EUR']==pytest.approx(0,abs=1e-9)
 journal=pd.read_csv(d/'JOURNAL_ARBITRAGES_GERE.csv')
 sale,buy=journal.iloc[0],journal.iloc[1]
 assert sale.Frais_sortie_EUR==pytest.approx(sale.Quantite_vendue*.156/.83581*.025)
 assert buy.Frais_entree_EUR==pytest.approx(buy.Montant_EUR*.025/1.025)
 assert buy.Quantite_achetee==pytest.approx((buy.Montant_EUR-buy.Frais_entree_EUR)/(.524/.83581))
 after=pd.read_csv(d/'TEST_ETAT_GERE_RECONSTRUIT.csv')
 assert after.loc[after.Ticker=='SFT.L','Statut'].iloc[0]=='SORTI'
 assert after.loc[after.Ticker=='MTEC.L','Quantite'].iloc[0]>before.loc[before.Ticker=='MTEC.L','Quantite'].iloc[0]
 for t in ['PLEJD.ST','PULS.L']:
  assert after.loc[after.Ticker==t,'Quantite'].iloc[0]==before.loc[before.Ticker==t,'Quantite'].iloc[0]
 assert (d/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv').read_bytes()==protected
 data=(d/'JOURNAL_ARBITRAGES_GERE.csv').read_bytes()
 assert m.execute(tmp_path,ASOF)==result
 assert (d/'JOURNAL_ARBITRAGES_GERE.csv').read_bytes()==data

def test_expired_authorization_never_modifies_ledger(tmp_path):
 d=setup(tmp_path);before=(d/'JOURNAL_ARBITRAGES_GERE.csv').read_bytes()
 with pytest.raises(ValueError,match='datée'):m.execute(tmp_path,datetime(2026,11,21,20,tzinfo=timezone.utc))
 assert (d/'JOURNAL_ARBITRAGES_GERE.csv').read_bytes()==before

"""Ancre commune, prix ajustés, volumes bruts, absence/futur et chiffrement."""
from pathlib import Path
from datetime import date,timedelta
from tempfile import TemporaryDirectory
from unittest.mock import patch
import importlib.util,json,hashlib,os
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('marche_us',ROOT/'SCRIPTS_ACTIFS/07AN_COMPLETER_MARCHE_US_EODHD.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 dates=pd.bdate_range('2025-09-01','2026-10-16')
 data=[{'date':d.strftime('%Y-%m-%d'),'close':20,'adjusted_close':10+i/100,'volume':100} for i,d in enumerate(dates)]
 index=[dict(r,adjusted_close=100) for r in data]
 a=m.mesurer(data,'2026-10-16',index)
 for k in (1,3,6,12):
  cible=(pd.Timestamp('2026-10-16')-pd.DateOffset(months=k)).strftime('%Y-%m-%d')
  base=[r for r in data if r['date']<=cible][-1]
  attendu=(data[-1]['adjusted_close']/base['adjusted_close']-1)*100
  assert abs(a['Momentum_'+str(k)+'m_pct']-attendu)<1e-10
  assert abs(a['Force_relative_SP500_'+str(k)+'m_pct']-attendu)<1e-10
 assert a['Volume_monetaire_median_63s_USD']==2000 # 20*100, jamais adjusted_close*100.
 assert a['Notes_attribuees']==0 and a['Spread'].startswith('MANQUANT')
 assert 'Momentum_1m_pct' not in m.mesurer(data[:-1],'2026-10-16',index)
 assert m.mesurer([], '2026-10-16')['Statut']=='HISTORIQUE_AJUSTE_ABSENT'
 missing=[dict(r) for r in data];missing[-1]['volume']=None
 assert 'Volume_monetaire_median_63s_USD' not in m.mesurer(missing,'2026-10-16')
 zero=[dict(r,volume=0) for r in data];assert m.mesurer(zero,'2026-10-16')['Seances_volume_nul_63s']==63
 for bad in [data+[data[-1]],[dict(data[-1],date='2026-10-19')],[dict(data[-1],close=float('nan'))],[dict(data[-1],volume=-1)]]:
  try:m.serie(bad,'2026-10-16')
  except ValueError:pass
  else:raise AssertionError('Historique incohérent accepté')
 # Exécution entière isolée : toutes les lignes persistent, chiffres bruts chiffrés.
 with TemporaryDirectory() as tmp:
  root=Path(tmp);src=root/'SCRIPTS_ACTIFS';src.mkdir()
  for nom in ('07AH_RECENSER_MICROCAPS_US_EODHD.py','07AI_RACCORDER_COMPTES_US_SSI.py'):(src/nom).write_bytes((ROOT/'SCRIPTS_ACTIFS'/nom).read_bytes())
  p=root/'AUDITS/PROFILS_SEC_UNIVERS_US/TEST';p.mkdir(parents=True)
  u=p/'TOUTES_COTATIONS_RECENSEES.csv';pd.DataFrame([{'Ticker_US':'AAA.US'},{'Ticker_US':'BBB.US'}]).to_csv(u,index=False)
  (p/'MANIFESTE.json').write_text(json.dumps({'fichiers':{u.name:hashlib.sha256(u.read_bytes()).hexdigest()}}))
  ah=m.charger('07AH_RECENSER_MICROCAPS_US_EODHD.py');original=ah.Client
  class Client(original):
   def get(self,path,params=None,**kwargs):
    if path=='user':return {'dailyRateLimit':100000,'apiRequests':0}
    obj=index if path=='eod/GSPC.INDX' else data
    name=self.archiver('REPONSE_'+str(len(self.index)).zfill(5),obj)
    self.index.append({'route':path,'archive_chiffree':name})
    (self.out/'INDEX_REQUETES.json').write_text(json.dumps(self.index));return obj
  ah.Client=Client;load=m.charger
  def module(nom):return ah if nom.startswith('07AH') else load(nom)
  # Date figée pour tester également la séance de référence du week-end.
  from datetime import datetime,timezone
  class Horloge:
   @staticmethod
   def now(tz):return datetime(2026,10,18,12,tzinfo=timezone.utc)
  with patch.object(m,'BASE',root),patch.object(m,'charger',side_effect=module),patch.object(m,'datetime',Horloge),patch.dict(os.environ,{'EODHD_API_KEY':'TEST_KEY_NOT_SECRET','MICRO_CAPS_MARCHE_TAILLE':'1'}):
   # conserver strptime en plus de now
   Horloge.strptime=staticmethod(datetime.strptime)
   bilan=m.executer()
  out=next((root/'AUDITS/MARCHE_US_EODHD').iterdir());coverage=pd.read_csv(out/'COUVERTURE_MARCHE_US.csv',keep_default_na=False)
  assert len(coverage)==2 and bilan['cotations_tentees']==1
  assert coverage.iloc[1].Statut_collecte=='HORS_LOT_TECHNIQUE'
  assert not any(c in coverage.columns for c in ('Dernier_cours_ajuste','Volume_monetaire_median_63s_USD','Momentum_1m_pct'))
  encrypted=json.loads((out/'METRIQUES_MARCHE_US.enc.json').read_text())
  decoded=json.loads(ah.dechiffrer(encrypted,'TEST_KEY_NOT_SECRET'))
  assert decoded[0]['Ticker']=='AAA.US' and decoded[0]['Volume_monetaire_median_63s_USD']==2000
 print('Marché US : ancre commune, horizons calendaires, prix ajustés, volume brut, absences et archives chiffrées OK')
if __name__=='__main__':test()

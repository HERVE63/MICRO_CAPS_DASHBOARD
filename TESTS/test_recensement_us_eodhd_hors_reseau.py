"""Recensement complet, sans plafond 172, sans confusion EUR/USD ni origine."""
import importlib.util,json
from pathlib import Path
from decimal import Decimal
from tempfile import TemporaryDirectory
from unittest.mock import patch
s=importlib.util.spec_from_file_location('eodhd_us',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AH_RECENSER_MICROCAPS_US_EODHD.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 population=[{'code':str(i),'cap':i} for i in range(1400)]
 def fetch(lo,hi,offset):return [r for r in population if lo<=r['cap']<=hi][offset:offset+100]
 journal=[];r=m.recenser_bande(fetch,0,1399,journal)
 assert len(r)==1400 and len({z['code'] for z in r})==1400 and any(z.get('subdivisee') for z in journal)
 try:m.recenser_bande(lambda *a:[{}]*100,7,7,[])
 except RuntimeError as e:assert 'SATURATION' in str(e)
 else:raise AssertionError('Plafond silencieux accepté')
 cat=[{'Code':c,'Type':t,'Currency':'USD','Country':'USA'} for c,t in [('A','Common Stock'),('B','Common Stock'),('C','Preferred Stock')]]
 rows=[{'code':'A','market_capitalization':100000000,'last_day_data_date':'2026-10-14'},
       {'code':'B','market_capitalization':600000000,'last_day_data_date':'2026-10-14'},
       {'code':'C','market_capitalization':200000000,'last_day_data_date':'2026-10-14'}]
 good,bad=m.normaliser(rows,cat,Decimal(2),'2026-10-14','2026-10-15')
 assert len(good)==2 and len(bad)==1 and Decimal(good[0]['Capitalisation_EUR'])==50000000
 assert all(r['Statut_identite']=='A_VERIFIER_EMETTEUR_US' and r['SSI']=='MANQUANTE' for r in good)
 rows[0]['last_day_data_date']='2026-11-01';good,bad=m.normaliser(rows,cat,Decimal(2),'2026-10-14','2026-10-15')
 assert any(r['Motif']=='DATE_MARCHE_FUTURE' for r in bad)
 with TemporaryDirectory() as tmp,patch.object(m,'BASE',Path(tmp)),patch.dict(m.os.environ,{'EODHD_API_KEY':''}):
  result=m.executer();assert result['recensement_termine'] is False and 'ABSENTE' in result['blocage']
 print('EODHD US: 1400 résultats sans troncature, saturation refusée, bornes EUR, types, dates et absence de clé contrôlés')
if __name__=='__main__':test()

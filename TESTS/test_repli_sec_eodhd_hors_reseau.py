"""Le refus EODHD ne dispense pas de l'identité SEC et des dates financières."""
import importlib.util,json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
s=importlib.util.spec_from_file_location('repli_sec',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AH_RECENSER_MICROCAPS_US_EODHD.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 mapping=m.index_cik_sec({'0':{'ticker':'AP','cik_str':1},'1':{'ticker':'AP','cik_str':2},'2':{'ticker':'P','cik_str':3}})
 assert mapping['AP']=={'0000000001','0000000002'} and mapping['P']=={'0000000003'}
 values=[{'form':'10-Q','filed':'2026-08-01','end':'2026-06-30','val':10},
         {'form':'10-Q','filed':'2026-11-01','end':'2026-09-30','val':20},
         {'form':'10-Q','filed':'2026-08-01','end':'2026-12-31','val':30}]
 obj={'cik':1234,'facts':{'us-gaap':{'Assets':{'units':{'USD':values}}}}}
 assert m.compter_faits(obj,'0000001234','2026-10-15')['Nb_faits_financiers']==1
 assert m.compter_faits(obj,'0000009999','2026-10-15')['Statut_companyfacts']=='CIK_COMPANYFACTS_INCOHERENT'
 raw=b'{ "cik" : 1234, "test" : 1 }'
 class Response:
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def read(self,n):return raw
 class Opener:
  def open(self,req,**kw):
   assert 'api_token' not in req.full_url and 'CLE_FIXTURE' not in req.full_url
   return Response()
 with TemporaryDirectory() as tmp:
  b=Path(tmp)/'run';b.mkdir();c=m.Client('CLE_FIXTURE',b);captured=[]
  def archive(nom,data,raw=None):captured.append(raw);return 'fixture.enc.json'
  with patch.object(m,'build_opener',return_value=Opener()),patch.object(c,'archiver',side_effect=archive),patch.object(m.time,'sleep'):
   assert c.get_sec('https://data.sec.gov/submissions/CIK0000001234.json','Fixture fixture@example.org')['cik']==1234
  assert captured==[raw] and c.cout==0
  assert json.loads((b/'INDEX_REQUETES.json').read_text())[0]['representation']=='OCTETS_HTTP_ORIGINAUX'
 print('REPLI SEC: ambiguïtés de ticker, CIK, dates futures, octets source et absence de clé dans les requêtes SEC contrôlés')
if __name__=='__main__':test()

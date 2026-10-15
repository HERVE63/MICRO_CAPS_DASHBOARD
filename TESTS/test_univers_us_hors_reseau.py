"""Ne pas confondre cotation SEC, domicile US et données SSI vérifiées."""
from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('us',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AE_CADRER_UNIVERS_US.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 def obj(inc='DE',business='CA',cik='1234',typ='operating'):
  return {'cik':cik,'entityType':typ,'stateOfIncorporation':inc,'addresses':{'business':{'stateOrCountry':business}}}
 assert m.classer(obj(),'0000001234')=='PISTE_US_CONCORDANTE'
 assert m.classer(obj('A1','A1'),'1234')=='HORS_PISTE_US'
 assert m.classer(obj('E9','CA'),'1234')=='ORIGINE_A_CLARIFIER'
 assert m.classer(obj('DE','L3'),'1234')=='ORIGINE_A_CLARIFIER'
 assert m.classer(obj('DE',''),'1234')=='ORIGINE_A_COMPLETER'
 assert m.classer(obj(cik='2345'),'1234')=='CIK_INCOHERENT'
 assert m.classer(obj(typ='investment'),'1234')=='TYPE_EMETTEUR_A_CLARIFIER'
 o=obj();o['addresses']['business']['isForeignLocation']=1
 assert m.classer(o,'1234')=='ORIGINE_A_CLARIFIER'
 assert m.classer(obj('PR','PR'),'1234')=='HORS_PISTE_US'
 print('UNIVERS US: immatriculation et activité concordantes, cas mixtes/absents/CIK refusés')
if __name__=='__main__':test()

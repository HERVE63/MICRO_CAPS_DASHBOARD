from datetime import datetime,timezone
import importlib.util,gzip,json
from pathlib import Path
import pytest
S=Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS'
def mod(name):
 s=importlib.util.spec_from_file_location(name,S/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_pence_et_livres_distincts():
 m=mod('marche_public.py')
 assert m.normaliser_cours(14.75,'GBp')==(.1475,'GBP')
 assert m.normaliser_cours(.1475,'GBP')==(.1475,'GBP')
 with pytest.raises(ValueError):m.normaliser_cours(14.75,'INCONNUE')

def test_cotation_perimee_non_reetiquetee(monkeypatch):
 m=mod('03A_MOTEUR_CLOTURES_V3.py');monkeypatch.setattr(m.marche,'suspension',lambda *a:None)
 monkeypatch.setattr(m.marche,'cloture',lambda *a:{'cours':12.,'date':'2026-11-09','devise':'USD','unite_source':'USD','preuve':'fixture'})
 r=m.derniere_cloture_validee('IDN',datetime(2026,11,12,12,tzinfo=timezone.utc))
 assert str(r['date_cotation'])=='2026-11-09' and r['statut']=='ATTENTE_NOUVELLE_COTATION' and not r['negociable']

def test_suspension_derniere_cotation_non_negociable(monkeypatch):
 m=mod('03A_MOTEUR_CLOTURES_V3.py');seen=[]
 monkeypatch.setattr(m.marche,'suspension',lambda *a:{'derniere_cotation':'2026-10-27','sources':['fixture']})
 def quote(t,d):
  seen.append(d);return {'cours':.1475,'date':'2026-10-27','devise':'GBP','unite_source':'GBp','preuve':'fixture'}
 monkeypatch.setattr(m.marche,'cloture',quote)
 r=m.derniere_cloture_validee('PULS.L',datetime(2026,11,12,12,tzinfo=timezone.utc))
 assert seen==['2026-10-27'] and r['statut']=='SUSPENDU_DOCUMENTE' and not r['negociable']
 assert r['cours_cloture']==.1475

def test_cache_capture_intraday_non_promu(monkeypatch,tmp_path):
 m=mod('marche_public.py');monkeypatch.setattr(m,'BASE',tmp_path)
 a=tmp_path/'archives';p=a/'20261111T180000Z';p.mkdir(parents=True)
 raw={'meta':{'symbol':'IDN','currency':'USD','exchangeTimezoneName':'America/New_York','currentTradingPeriod':{'regular':{'end':int(datetime(2026,11,11,21,tzinfo=timezone.utc).timestamp())}}},'timestamp':[int(datetime(2026,11,11,14,30,tzinfo=timezone.utc).timestamp())],'indicators':{'quote':[{'close':[2.]}]}}
 (p/'IDN.json.gz').write_bytes(gzip.compress(json.dumps(raw).encode()))
 monkeypatch.setattr(m,'ARCHIVES',a);monkeypatch.setattr(m,'CACHE',tmp_path/'vide')
 def nope(*a,**k):raise OSError('TEST_RESEAU_INDISPONIBLE')
 monkeypatch.setattr(m.urllib.request,'urlopen',nope)
 with pytest.raises(RuntimeError,match='Cours indisponibles'):m.charger('IDN','2026-11-11')

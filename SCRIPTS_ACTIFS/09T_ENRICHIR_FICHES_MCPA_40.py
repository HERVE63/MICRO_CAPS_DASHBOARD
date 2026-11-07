#!/usr/bin/env python3
"""Enrich 40 MCPA/IPS JSON dossiers from traceable collected evidence.
No synthetic values, no score, no unverified SEC CIK attribution.
"""
import csv,json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];D=BASE/'DONNEES';F=BASE/'DOSSIERS_MCPA_IPS_40'
def load(name):
 p=D/name
 if not p.exists():return []
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def put(doc,block,key,value,unit,period,date,url,status='SOURCE_COLLECTEE',comment=None):
 cell=doc['blocs'][block][key]
 if value is None or str(value).strip()=='':return False
 if cell['valeur'] is not None:return False
 cell.update(valeur=value,unite=unit,periode=period,date_source=date,source_url=url,statut=status,commentaire=comment)
 return True
def main():
 indicators={r['Ticker']:r for r in load('INDICATEURS_YAHOO_40.csv')}
 public=[]
 for source_path in sorted(D.glob('PREUVES_FONDAMENTALES_PUBLIQUES_*.csv')):
  public.extend(load(source_path.name))
 complements={}
 for source_path in sorted(D.glob('COMPLEMENTS_PUBLICS_40_*.json')):
  for observation in json.loads(source_path.read_text(encoding='utf-8')):
   complements[observation['ticker']]=observation
 mapping={'CA':('qualite','ca_ttm'),'Marge_EBITDA':('qualite','marge_ebitda_pct'),'Croissance_CA':('croissance','croissance_ca_1a_pct'),'Croissance_EBITDA':('croissance','croissance_ebitda_pct'),'Croissance_commandes':('croissance','book_to_bill'),'EBITDA':('qualite','marge_ebitda_pct'),'Tresorerie':('risque','cash'),'Dette_nette':('risque','dette_nette'),'Carnet_commandes':('croissance','carnet_commandes')}
 # CA, EBITDA and orders growth cannot be treated as TTM, EBITDA margin or book-to-bill.
 mapping.pop('CA');mapping.pop('EBITDA');mapping.pop('Croissance_commandes')
 # Growth metrics on interim periods cannot be labeled annual.
 mapping.pop('Croissance_CA');mapping.pop('Croissance_EBITDA')
 count=0;updates=0;report=[]
 for path in sorted(F.glob('*.json')):
  x=json.loads(path.read_text(encoding='utf-8'));t=x['ticker'];changed=0
  i=indicators.get(t,{})
  technical={'MM200':('momentum','tendance_mm200',1,'prix'),'Ratio_prix_MM200':('momentum','prix_vers_mm200',1,'ratio'),'Momentum_1m':('momentum','momentum_1m_pct',100,'pct'),'Momentum_3m':('momentum','momentum_3m_pct',100,'pct'),'Momentum_6m':('momentum','momentum_6m_pct',100,'pct'),'Momentum_12m':('momentum','momentum_12m_pct',100,'pct'),'Volume_moyen_20j':('momentum','volume_moyen_20j',1,'titres')}
  for source,(block,key,mult,unit) in technical.items():
   raw=i.get(source,'')
   if not raw:continue
   # MM200 is a price level, not a slope; preserve its meaning in comment.
   if source=='MM200':continue
   # Isoler les observations Yahoo mal formees et sans provenance.
   try:
    value=float(raw)*mult
    if not __import__('math').isfinite(value):continue
   except (TypeError,ValueError,OverflowError):
    continue
   if not i.get('Date_fin') or not i.get('Source'):continue
   changed+=put(x,block,key,value,unit,'cloture '+i['Date_fin'],i['Date_fin'],i['Source'],'SOURCE_MARCHE',source)
  evidence=[r for r in public if r.get('Ticker')==t]
  for e in evidence:
   metric=e['Indicateur']
   if metric not in mapping:continue
   block,key=mapping[metric]
   # Une observation mal formee ne doit pas interrompre les 39 autres titulaires.
   try:
    value=float(e['Valeur'])
    if not __import__('math').isfinite(value):continue
   except (TypeError,ValueError):
    continue
   if not e.get('Source_URL') or not e.get('Date_collecte') or not e.get('Periode') or not e.get('Unite'):
    continue
   changed+=put(x,block,key,value,e['Unite'],e['Periode'],e['Date_collecte'],e['Source_URL'],'SOURCE_PUBLIQUE',metric)
  # 10G supplies secondary-source observations, not automatically validated fundamentals.
  # Preserve provenance and never manufacture a value or an MCPA score.
  observation=complements.get(t,{})
  for section in ('series_annuelles','valorisation_historique','revisions'):
   item=observation.get(section,{})
   if not item or not item.get('statut','').startswith('SOURCE_SECONDAIRE'):continue
   marker=(item.get('url'),section,observation.get('date_collecte'))
   if not any((p.get('url'),p.get('indicateur'),p.get('periode'))==marker for p in x['preuves_complementaires']):
    x['preuves_complementaires'].append({'url':item.get('url'),'indicateur':section,'valeur':None,'unite':None,'periode':observation.get('date_collecte'),'date_collecte':observation.get('date_collecte'),'statut':'A_VERIFIER_AVANT_NOTATION','sha256_reponse':item.get('sha256_reponse'),'donnees_brutes':{k:item[k] for k in ('series','lignes','tendances') if k in item}})
    changed+=1
  existing={(e.get('url'),e.get('indicateur'),e.get('periode')) for e in x['preuves_complementaires']}
  for e in evidence:
   marker=(e['Source_URL'],e['Indicateur'],e['Periode'])
   if marker not in existing:
    x['preuves_complementaires'].append({'url':e['Source_URL'],'indicateur':e['Indicateur'],'valeur':e['Valeur'],'unite':e['Unite'],'periode':e['Periode'],'date_collecte':e['Date_collecte'],'statut':'A_VERIFIER_AVANT_NOTATION'})
    changed+=1
  if changed:path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  count+=1;updates+=changed;report.append({'Ticker':t,'Champs_ajoutes':changed,'Preuves_publiques':len(evidence),'Statut_MCPA':x['notation']['statut']})
 with (D/'AUDIT_ENRICHISSEMENT_40.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(report[0]));w.writeheader();w.writerows(report)
 print(f'Fiches {count}; nouveaux champs/preuves {updates}; scores inchanges')
if __name__=='__main__':main()

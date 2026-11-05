#!/usr/bin/env python3
"""Preserve holdings evidence; import only exhaustive declared AMF windows, never scores."""
import datetime as dt,json,math,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'DONNEES';F=B/'DOSSIERS_MCPA_IPS_40';DATE='2026-11-05'
def number(v):
 if isinstance(v,dict):v=v.get('raw')
 return v if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) else None
def main():
 govpath=D/'GOUVERNANCE_PUBLIQUE_40_20261105.json';amfpath=D/'DECLARATIONS_AMF_14_20261105.json'
 gov={r['ticker']:r for r in json.loads(govpath.read_text())} if govpath.exists() else {};amf={r['ticker']:r for r in json.loads(amfpath.read_text())} if amfpath.exists() else {};imported=0
 for p in F.glob('*.json'):
  d=json.loads(p.read_text());r=gov.get(d['ticker'])
  if r:
   obs={'bloc':'qualite','champ':'dirigeants_et_detentions_documentes','valeur':{'dirigeants_declares_fournisseur':r.get('dirigeants',[]),'detentions_initiees':r.get('detentions_initiees',[]),'fichier_transactions_secondaires':str(govpath.relative_to(B))},'unite':'detentions et profils professionnels','periode':'dates individuelles du fournisseur; collecte '+DATE,'date_source':DATE,'date_collecte':DATE,'source_url':r.get('url'),'statut':'SOURCE_SECONDAIRE_GOUVERNANCE_A_RAPPROCHER','commentaire':'Titres détenus séparés des options/attributions. Dates/fonctions de chaque ligne à contrôler : les anciens dirigeants peuvent subsister. Ne pas additionner les détentions directes et indirectes sans éliminer les doubles comptes. Pas de certification de couverture des transactions, ni note SSI déduite.'}
   if obs not in d['observations_complementaires']:d['observations_complementaires'].append(obs)
   log={'famille':'gouvernance_et_detentions_Yahoo','date':DATE,'url':r.get('url'),'http':r.get('http'),'statut':r['statut'],'limite':r.get('limite','Pas de preuve de l’absence de détentions.')}
   if log not in d['journal_recherches']:d['journal_recherches'].append(log)
  r=amf.get(d['ticker'])
  if r:
   if r['isin']!=d['blocs']['identite']['isin']['valeur']:raise ValueError('ISIN divergent '+d['ticker'])
   for log in r.get('recherches',[]):
    entry={'famille':'registre_AMF_'+log['famille'],'date':DATE,**{k:v for k,v in log.items() if k!='famille'},'jeton':r.get('jeton'),'limite':'Déclarations publiées par l’AMF, établies sous responsabilité du déclarant; ne prouve pas absence de transactions non publiées.'}
    if entry not in d['journal_recherches']:d['journal_recherches'].append(entry)
   url=next((x['url'] for x in r.get('recherches',[]) if x['famille']=='declarations_2026'),None)
   for days,v in r.get('totaux',{}).items():
    c=d['blocs']['risque']['transactions_initiees_net_'+days+'j']
    complete=r.get('pagination_complete') is True and len(r['declarations'])==r.get('nombre_declarations_2026') and v['statut']=='DEPOTS_AMF_FENETRE_CONTROLEE' and not r['erreurs']
    if c['valeur'] is None and v['valeur'] is not None and complete:
     c.clear();c.update(valeur=v['valeur'],unite='EUR',periode=v['debut']+' / '+v['fin']+'; '+days+' jours calendaires',date_source=DATE,date_collecte=DATE,source_url=url,statut='CALCULE_DEPOTS_PRIMAIRES_AMF',commentaire=v['limite']+' Source détaillée et PDF archivés : '+str(amfpath.relative_to(B))+'. Un zéro décrit le net des déclarations couvertes; il ne certifie pas une absence de transactions réelles.');imported+=1
   leis={z['lei'] for z in r['declarations'] if z.get('lei')};c=d['blocs']['identite']['lei']
   if c['valeur'] is None and len(leis)==1:
    lei=next(iter(leis));rec=next(z for z in r['declarations'] if z.get('lei')==lei);c.clear();c.update(valeur=lei,unite='LEI',periode='déclaration publiée '+rec['date_publication'][:10],date_source=rec['date_publication'][:10],date_collecte=DATE,source_url=rec['url'],statut='SOURCE_PRIMAIRE_DECLARANT_AMF',commentaire='Identifiant déclaré, ISIN contrôlé dans le même document et checksum LEI mod-97 valide; statut courant du registre GLEIF non vérifié.');imported+=1
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'champs_primaires_ajoutes':imported,'profils_gouvernance':len(gov),'emetteurs_AMF':len(amf),'notes_attribuees':0}))
 subprocess.check_call([sys.executable,str(B/'SCRIPTS_ACTIFS/10H_IMPORTER_COMPLEMENTS_PUBLICS_40.py')],cwd=B)
if __name__=='__main__':main()

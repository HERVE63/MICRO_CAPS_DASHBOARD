#!/usr/bin/env python3
"""Apply dated analyst judgments. Does not certify dossiers or authorize orders."""
import argparse,calendar,csv,gzip,hashlib,io,json,math,statistics
from datetime import date,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DAY='2026-11-09';CUTOFF='2026-11-06'
BLOCKS={'Q':'qualite','V':'valorisation','G':'croissance','R':'risque','M':'momentum','D':'diversification'}
EXTRA={
 'INFU':['https://ir.infusystem.com/news-events/press-releases/detail/1408/infusystem-announces-financial-results-for-third-quarter'],
 'CXDO':['https://www.sec.gov/Archives/edgar/data/1075736/000165495426009477/cxdo_ex991.htm'],
 'LWAY':['https://lifewaykefir.com/press_releases/'],
 'ELVA.TO':['https://electrovaya.com/press/electrovaya-provides-a-business-update-5/'],
 'ROK.V':['https://www.nasdaq.com/press-release/rok-resources-announces-return-capital-and-expanded-2026-drilling-program-2026-10-14'],
 'HDD.L':['https://www.investegate.co.uk/announcement/rns/hardide--hdd/year-end-trading-update/9832781'],
 'KLD.V':['https://www.kenorlandminerals.com/news/kenorland-minerals-closes-oversubscribed-16-million-financing'],
 'CER.L':['https://www.londonstockexchange.com/en/news/article/CER/full-year-trading-update/17784090'],
 'ALBPK.PA':['https://webdisclosure.fr/press-release/broadpeak-sa-etr-broadpeak-publie-son-chiffre-daffaires-au-30-septembre-2026-HQ6fgjqTJ6a'],
 'ALDMS.PA':['https://www.actusnews.com/fr/dms-group/cp/2026/09/14/acceleration-de-la-rentabilite-et-resultat-net-positif-au-1er-semestre-2026'],
 'ALSOG.PA':['https://markets.ft.markitdigital.com/data/announce/detail?dockey=1330-1001280321fr-0P2S5B45U0JAIQBRNDLOEVO8QC']}

def dump(p,x):
 s=json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
 if not p.exists() or p.read_text()!=s:p.write_text(s)

def calculate(rows):
 # Conflicting duplicate bars are an error, not an opportunity to choose a price.
 uniq={}
 for r in rows:
  if r['Date_UTC']>CUTOFF:continue
  if r['Date_UTC'] in uniq and any(uniq[r['Date_UTC']][k]!=r[k] for k in ('Close','AdjClose','Volume')):raise ValueError('Cotations contradictoires')
  uniq[r['Date_UTC']]=r
 clean=sorted(uniq.values(),key=lambda r:r['Date_UTC'])
 if not clean or clean[-1]['Date_UTC']!=CUTOFF:raise ValueError('Clôture commune absente')
 if any(not r['AdjClose'] or not math.isfinite(float(r['AdjClose'])) or float(r['AdjClose'])<=0 for r in clean):raise ValueError('Cours ajusté absent/invalide')
 prices=[float(r['AdjClose']) for r in clean];end=date.fromisoformat(CUTOFF);anchors={};values={}
 for months in (1,3,6,12):
  y,m=divmod(end.year*12+end.month-1-months,12);m+=1;target=date(y,m,min(end.day,calendar.monthrange(y,m)[1]))
  eligible=[r for r in clean if target-timedelta(days=10)<=date.fromisoformat(r['Date_UTC'])<=target]
  old=eligible[-1] if eligible else None
  anchors[str(months)]={'date':old['Date_UTC'],'cours_ajuste':float(old['AdjClose'])} if old else None
  values[f'momentum_{months}m_pct']=(prices[-1]/float(old['AdjClose'])-1)*100 if old else None
 mm=statistics.mean(prices[-200:]) if len(prices)>=200 else None
 oldmm=statistics.mean(prices[-220:-20]) if len(prices)>=220 else None
 vols=[float(r['Volume']) for r in clean[-20:] if r['Volume']]
 v20=statistics.mean(vols) if len(vols)==20 else None
 values.update(prix_vers_mm200=prices[-1]/mm if mm else None,tendance_mm200=(mm/oldmm-1)*100 if oldmm else None,
   momentum_6_1_pct=(anchors['1']['cours_ajuste']/anchors['6']['cours_ajuste']-1)*100 if anchors['1'] and anchors['6'] else None,
   volume_moyen_20j=v20,ratio_volume=float(clean[-1]['Volume'])/v20 if v20 and clean[-1]['Volume'] else None,
   volatilite_90j_pct=statistics.stdev([math.log(b/a) for a,b in zip(prices[-91:-1],prices[-90:])])*math.sqrt(252)*100 if len(prices)>=91 else None)
 peak=0;dd=0
 for r in clean:
  if r['Date_UTC']<(end-timedelta(days=365)).isoformat():continue
  p=float(r['AdjClose']);peak=max(peak,p);dd=min(dd,p/peak-1)
 values['drawdown_12m_pct']=dd*100 if anchors['12'] else None
 rules=[('prix_vers_mm200',1,2),('tendance_mm200',0,1),('momentum_1m_pct',0,1),('momentum_3m_pct',0,2),('momentum_6m_pct',0,2),('momentum_12m_pct',0,1),('momentum_6_1_pct',0,1)]
 grid=[{'indicateur':k,'seuil_strict':t,'maximum':w,'valeur':values[k],'points':None if values[k] is None else w if values[k]>t else 0} for k,t,w in rules]
 return {'date':CUTOFF,'cours_non_ajuste':float(clean[-1]['Close']),'ancrages':anchors,'indicateurs':values,'grille':grid,'M':sum(r['points'] or 0 for r in grid),'points_non_observables':sum(r['maximum'] for r in grid if r['points'] is None),'source_url':clean[-1]['Source']}

def put(d,b,k,value,unit,period,srcdate,source,status,comment):
 old=d['blocs'][b][k];new=dict(valeur=value,unite=unit,periode=period,date_source=srcdate,source_url=source,statut=status,commentaire=comment,date_collecte=DAY)
 if value is None:new['recherche']={'date':DAY,'statut':status,'motif':comment,'journal':'journal_recherches'}
 if old==new:return
 d.setdefault('historique_relectures',[]).append({'preuve_id':'ANALYSE_20261109_'+k,'champ':b+'.'+k,'ancienne_cellule':old,'motif':comment,'date_relecture':DAY})
 d['blocs'][b][k]=new

def audit(d):
 cells={b+'.'+k:c for b,cs in d['blocs'].items() for k,c in cs.items()};counts={'RENSEIGNE':0,'NON_APPLICABLE':0,'INDISPONIBLE_A_DATE':0,'RECHERCHE_A_POURSUIVRE':0}
 for c in cells.values():
  g='RENSEIGNE' if c['valeur'] is not None else 'NON_APPLICABLE' if c['statut']=='NON_APPLICABLE' else 'INDISPONIBLE_A_DATE' if c['statut']=='HISTORIQUE_INSUFFISANT_AVANT_COTATION' else 'RECHERCHE_A_POURSUIVRE';counts[g]+=1
 missing=[k for k,c in cells.items() if c['valeur'] is None]
 d['audit_couverture'].update(date=DAY,champs_total=len(cells),champs_renseignes=counts['RENSEIGNE'],couverture_pct=round(100*counts['RENSEIGNE']/len(cells),2),champs_secondaires_non_rapproches=sum(c['valeur'] is not None and 'SECONDAIRE' in c['statut'] for c in cells.values()),champs_manquants=missing,cours_date_limite=CUTOFF,statut='ANALYSE_DOCUMENTEE_NON_CERTIFIEE')
 d['audit_poursuite'].update(date=DAY,comptage=counts,couverture_valeurs_pct=round(100*counts['RENSEIGNE']/len(cells),2),couverture_applicable_pct=round(100*counts['RENSEIGNE']/(len(cells)-counts['NON_APPLICABLE']),2),recherches_non_closes=[k for k in missing if cells[k]['statut'] not in {'NON_APPLICABLE','HISTORIQUE_INSUFFISANT_AVANT_COTATION'}],notes_justifiees=True,validation_individuelle='NOTES_SCENARIOS_DOCUMENTES_VALIDATION_REQUISE')

def execute(root,history):
 inputs={r['ticker']:r for r in csv.DictReader((root/'DONNEES/JUGEMENTS_MCPA_40_20261109.tsv').open(),delimiter='\t')}
 docs=[(p,json.loads(p.read_text())) for p in sorted((root/'DOSSIERS_MCPA_IPS_40').glob('*.json'))]
 if len(inputs)!=40 or set(inputs)!={d['ticker'] for p,d in docs}:raise ValueError('Cohorte exactement 40 requise')
 with (gzip.open(history,'rt',newline='') if history.suffix=='.gz' else history.open(newline='')) as f:rows=list(csv.DictReader(f))
 summary=[];calc={}
 for p,d in docs:
  t=d['ticker'];a=inputs[t];m=calculate([r for r in rows if r['Ticker']==t]);calc[t]=m
  sources=sorted({c['source_url'] for b in ('qualite','croissance','risque') for c in d['blocs'][b].values() if c['valeur'] is not None and c.get('source_url') and ('PRIMAIRE' in c['statut'] or 'SEC' in c['statut'])})
  if not sources:sources=sorted({c['source_url'] for b in ('qualite','croissance','risque') for c in d['blocs'][b].values() if c['valeur'] is not None and c.get('source_url')})
  sources=sorted(set(sources+EXTRA.get(t,[])));src=' | '.join(sources)
  for k,v in m['indicateurs'].items():put(d,'momentum',k,v,'titres/jour' if k=='volume_moyen_20j' else 'ratio' if k in ('ratio_volume','prix_vers_mm200') else 'pct','historique ajusté au '+CUTOFF,CUTOFF,m['source_url'],'CALCULE_HISTORIQUE_SECONDAIRE' if v is not None else 'HISTORIQUE_INSUFFISANT_AVANT_COTATION','Calcul reproductible 10Q; ancrage dernière séance <= date calendaire cible, aucune période pré-IPO extrapolée.',)
  price=m['cours_non_ajuste']/(100 if t.endswith('.L') else 1)
  put(d,'valorisation','cours',price,d['devise'],'clôture '+CUTOFF,CUTOFF,m['source_url'],'SOURCE_MARCHE','Cours non ajusté, conversion GBp/100 vers GBP pour Londres.')
  put(d,'valorisation','date_cours',CUTOFF,'date','clôture',CUTOFF,m['source_url'],'SOURCE_MARCHE','Clôture commune aux 40 fiches.')
  notes={b:float(a[k]) if k!='M' else m['M'] for k,b in BLOCKS.items()}
  why={b:a[b] for k,b in BLOCKS.items() if k!='M'};why['momentum']=f"Grille explicite au {CUTOFF}: {m['M']}/10, {m['points_non_observables']} points non observables. Absence d'historique distincte d'un signal baissier; score provisoire si incomplet."
  n=dict(bareme=d['notation']['bareme'],notes=notes,total_mcpa=sum(notes.values()),statut='DOCUMENTEE_NON_VALIDEE',justifications=why,date_analyse=DAY,sources=sources,limite='Notes discrétionnaires provisoires; multiples secondaires à rapprocher, SSI et revue stricte obligatoires. Grille momentum locale ne modifiant pas le maître.')
  if n!=d['notation']:d.setdefault('historique_notations',[]).append(d['notation']);d['notation']=n
  d['calculs_marche']=m;d['analyse_prospective']={'date_analyse':DAY,'date_ancrage':CUTOFF,'cours_ancrage':price,'devise':d['devise'],'incertitude':a['incertitude'],'nature':'Probabilités subjectives non calibrées, incertitude au moins +/-10 points. Rendements du cours en devise locale, hors change, dividendes et frais.','horizons':{}}
  for h,end in [('3','2027-02-06'),('6','2027-05-06')]:
   rets=[float(a[k+h]) for k in ('bear','central','bull')];probs=[float(a[k+h]) for k in ('pb','pc','pu')]
   if sum(probs)!=100 or not -100<=rets[0]<=rets[1]<=rets[2] or min(probs)<0 or max(probs)>100:raise ValueError('Scénarios invalides '+t)
   states=[]
   for case,r,prob,fr in zip(('bear','central','bull'),rets,probs,('baissier','central','haussier')):
    put(d,'complements',f'scenario_{case}_{h}m_pct',r,'pct',h+' mois depuis '+CUTOFF,DAY,src,'HYPOTHESE_PROSPECTIVE_ANALYSTE',a[fr]+' '+a['incertitude'])
    put(d,'complements',f'prob_{case}_{h}m_pct',prob,'pct','probabilité subjective '+h+' mois',DAY,src,'PROBABILITE_SUBJECTIVE_NON_CALIBREE','Pondération par jugement du risque et des opportunités décrits; aucune fréquence statistique. Incertitude au moins +/-10 points. '+a['incertitude'])
    states.append({'cas':case,'rendement_pct':r,'probabilite_pct':prob,'cours_conditionnel':price*(1+r/100),'declencheur':a[fr]})
   expected=sum(r*p/100 for r,p in zip(rets,probs))
   d['analyse_prospective']['horizons'][h+'m']={'echeance_calendaire':end,'scenarios':states,'esperance_subjective_brute_pct':expected,'esperance_apres_rotation_vente_achat_2_5pct':((1+expected/100)*.975/1.025-1)*100,'convention_frais':'Friction théorique: vente 2,5 % du brut, achat 2,5 % du nominal acheté. Pas de transaction.'}
  for k,v,u in [('ic_sur_5',float(a['IC']),'note/5'),('cx_sur_5',float(a['CX']),'note/5'),('delta','MIXTE_SOUS_REVUE','texte'),('role_ips','INCUBATION_VIRTUELLE_SOUS_REVUE','texte'),('decision','ATTENTE','texte'),('condition_renforcement','SSI documenté >=65, MCPA >=80, IC >=3,5, données rapprochées, revue stricte valide et duel favorable après frais.','texte'),('condition_allegement_sortie',a['baissier']+' Contrôle des coûts et de la liquidité avant décision virtuelle.','texte')]:put(d,'complements',k,v,u,'analyse au '+DAY,DAY,src,'ANALYSE_PROVISOIRE_DOCUMENTEE',a['incertitude']+' Aucune opération autorisée.')
  for k in ('interet_strategique','complementarite_portefeuille'):put(d,'diversification',k,a['diversification'],'analyse','cohorte 40 titulaires',DAY,src,'JUGEMENT_ANALYSTE','Diversification sectorielle, sans garantie de décorrélation en crise.')
  d['date_analyse']=DAY;d['statut_fiche']='NOTEE_SCENARISEE_NON_VALIDEE';d['arbitrage_autorise']=False;audit(d);dump(p,d)
  summary.append({'ticker':t,'MCPA_provisoire':sum(notes.values()),'notes':notes,'IC':float(a['IC']),'CX':float(a['CX']),'SSI':d['blocs']['complements']['ssi']['valeur'],'statut':'NON_VALIDEE'})
 dump(root/'DONNEES/CALCULS_MARCHE_40_20261106.json',{'date_analyse':DAY,'historique':history.name,'sha256_historique':hashlib.sha256(history.read_bytes()).hexdigest(),'calculs':calc})
 dump(root/'DONNEES/SYNTHESE_NOTES_SCENARIOS_40_20261109.json',{'date_analyse':DAY,'fiches':summary,'notes_calculees':40,'scenarios':240,'fiches_certifiees_par_ce_script':0})
 return {'fiches_notees':40,'scenarios':240,'arbitrages':0}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--history',type=Path,required=True);args=p.parse_args();print(json.dumps(execute(ROOT,args.history)))

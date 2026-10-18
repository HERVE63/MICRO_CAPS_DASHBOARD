"""Historique EODHD de tout le recensement US : pistes B7 et momentum, pas de notes.
Les données fournisseur et métriques restent chiffrées ; seule la couverture
est publiée. Les cours ajustés recueillis aujourd'hui ne sont pas un historique
point-in-time du 1er octobre. Aucun appel ne modifie CPI ou le T0.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,importlib.util,json,math,os,re
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
def charger(nom):
 s=importlib.util.spec_from_file_location(nom[:-3],BASE/'SCRIPTS_ACTIFS'/nom);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def serie(data,limite):
 if not isinstance(data,list):raise ValueError('HISTORIQUE_SCHEMA_INVALIDE')
 records=[];dates=set()
 for row in data:
  d=row.get('date','')
  try:datetime.strptime(d,'%Y-%m-%d')
  except (TypeError,ValueError):raise ValueError('DATE_HISTORIQUE_INVALIDE')
  if d>limite:raise ValueError('COURS_POSTERIEUR_DATE_LIMITE')
  if d in dates:raise ValueError('DATE_HISTORIQUE_DUPLIQUEE')
  dates.add(d)
  def nombre(k,positif=False):
   x=row.get(k)
   if x is None:return None
   if isinstance(x,bool):raise ValueError('TYPE_NUMERIQUE_INVALIDE')
   v=float(x)
   if not math.isfinite(v) or v<0 or (positif and v==0):raise ValueError('VALEUR_HISTORIQUE_INVALIDE')
   return v
  records.append({'date':d,'adjusted_close':nombre('adjusted_close',True),'close':nombre('close',True),'volume':nombre('volume')})
 return sorted(records,key=lambda r:r['date'])
def ratios_splits(data,limite):
 if not isinstance(data,list):raise ValueError('SPLITS_SCHEMA_INVALIDE')
 result=[];seen=set()
 for r in data:
  d=r.get('date','');datetime.strptime(d,'%Y-%m-%d')
  if d>limite:raise ValueError('SPLIT_FUTUR')
  if d in seen:raise ValueError('SPLIT_DATE_DUPLIQUEE')
  seen.add(d);ratio=str(r.get('split',''))
  if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?/[0-9]+(?:\.[0-9]+)?',ratio):raise ValueError('RATIO_SPLIT_INVALIDE')
  a,b=map(float,ratio.split('/'))
  if not math.isfinite(a) or not math.isfinite(b) or a<=0 or b<=0:raise ValueError('RATIO_SPLIT_INVALIDE')
  result.append((d,a/b))
 return result
def mesurer(data,reference,indice=None,splits=None,date_collecte=None):
 rows=serie(data,reference);prix=[r for r in rows if r['adjusted_close'] is not None]
 r={'Date_reference':reference,'Seances_recues':len(rows),'Seances_ajustees':len(prix),
    'Spread':'MANQUANT_NON_FOURNI_PAR_HISTORIQUE_EOD','Turnover_capital':'MANQUANT_DENOMINATEUR_ACTIONS_A_VERIFIER',
    'SSI':'MANQUANTE','Notes_attribuees':0}
 if not prix:return dict(r,Statut='HISTORIQUE_AJUSTE_ABSENT')
 last=prix[-1];r['Date_dernier_cours']=last['date'];r['Age_cours_jours']=(pd.Timestamp(reference)-pd.Timestamp(last['date'])).days
 # Même ancre pour tous. Une valeur sans cours à l'ancre ne reçoit pas de momentum courant.
 if last['date']!=reference:return dict(r,Statut='COURS_ABSENT_DATE_REFERENCE')
 r['Dernier_cours_ajuste']=last['adjusted_close'];r['Dernier_cours_brut']=last['close']
 for mois in (1,3,6,12):
  cible=(pd.Timestamp(reference)-pd.DateOffset(months=mois)).strftime('%Y-%m-%d')
  precedents=[q for q in prix if q['date']<=cible]
  if not precedents:continue
  q=precedents[-1];r['Date_base_'+str(mois)+'m']=q['date']
  if (pd.Timestamp(cible)-pd.Timestamp(q['date'])).days>7:continue
  r['Momentum_'+str(mois)+'m_pct']=(last['adjusted_close']/q['adjusted_close']-1)*100
  if indice:
   ref=[z for z in indice if z['date']==reference and z['adjusted_close'] is not None]
   base=[z for z in indice if z['date']==q['date'] and z['adjusted_close'] is not None]
   if ref and base:r['Force_relative_SP500_'+str(mois)+'m_pct']=((last['adjusted_close']/q['adjusted_close'])/(ref[0]['adjusted_close']/base[0]['adjusted_close'])-1)*100
 # Close brut x volume fourni : pas de multiplication du volume par un prix ajusté dividendes.
 recent=rows[-63:];valid=[q for q in recent if q['close'] is not None and q['volume'] is not None]
 r['Seances_volume_63s']=len(valid)
 if len(recent)==63 and len(valid)==63:
  if splits is not None:
   events=ratios_splits(splits,date_collecte or reference);values=[]
   for q in valid:
    facteur=math.prod(ratio for d,ratio in events if d>q['date'])
    if not math.isfinite(facteur) or facteur<=0:raise ValueError('PRODUIT_RATIOS_SPLITS_INVALIDE')
    values.append(q['close']*q['volume']/facteur)
   r['Volume_monetaire_median_63s_USD']=float(pd.Series(values).median())
   r['Statut_volume_monetaire']='CORRIGE_EVENEMENTS_SPLITS_FOURNIS'
  else:r['Statut_volume_monetaire']='MANQUANT_CORRECTION_SPLITS_REQUISE'
  r['Volume_titres_median_63s']=float(pd.Series([q['volume'] for q in valid]).median())
  r['Seances_volume_nul_63s']=sum(q['volume']==0 for q in valid)
 r['Statut']='MESURES_A_VERIFIER_IDENTITE_ET_LIQUIDITE'
 return r

def executer():
 now=datetime.now(timezone.utc);out=BASE/'AUDITS/MARCHE_US_EODHD'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 ah=charger('07AH_RECENSER_MICROCAPS_US_EODHD.py');ai=charger('07AI_RACCORDER_COMPTES_US_SSI.py')
 sources=sorted((BASE/'AUDITS/PROFILS_SEC_UNIVERS_US').glob('*/MANIFESTE.json'))
 if not sources:raise RuntimeError('RECENSEMENT_US_PREPARE_ABSENT')
 sp=sources[-1];sm=json.loads(sp.read_text());univers=ai.verifier_fichier(sp.parent,sm,'TOUTES_COTATIONS_RECENSEES.csv')
 u=pd.read_csv(univers,dtype=str,keep_default_na=False)
 if u.Ticker_US.duplicated().any() or not u.Ticker_US.str.fullmatch(r'[A-Z0-9.\-]+\.US').all():raise RuntimeError('UNIVERS_MARCHE_INVALIDE')
 # Périmètre complet, sans présélection selon fondamentaux, performance ou disponibilité.
 tickers=sorted(u.Ticker_US);taille=int(os.getenv('MICRO_CAPS_MARCHE_TAILLE',str(len(tickers))))
 if taille<=0:raise RuntimeError('TAILLE_LOT_INVALIDE')
 key=os.getenv('EODHD_API_KEY','').strip()
 if not key:raise RuntimeError('EODHD_API_KEY_ABSENTE')
 client=ah.Client(key,out,intervalle=.15);rows=[];metrics=[];fatal='';ref='';index=[]
 bilan={'date_utc':now.isoformat(),'source_univers':str(univers.relative_to(BASE)),'source_univers_SHA256':sha(univers),
  'source_script_SHA256':sha(Path(__file__)),'dependances_SHA256':{p:sha(BASE/'SCRIPTS_ACTIFS'/p) for p in ('07AH_RECENSER_MICROCAPS_US_EODHD.py','07AI_RACCORDER_COMPTES_US_SSI.py')},
  'volumes_monetaires_corriges_splits':True,'cotations_recensees':len(u),'notes_attribuees':0,'T0_modifie':False,'selection_terminee':False,
  'formules':{'momentum':'cours_ajuste(ancre)/cours_ajuste(dernier<=ancre-moism)-1 ; base et ancre publiées',
   'force_relative':'ratio des facteurs de performance action/SP500 aux mêmes dates',
   'volume_monetaire':'médiane(close brut x volume ajusté splits / produit ratios splits postérieurs) sur 63 séances complètes'},
  'reference_indice':'GSPC.INDX','limite_force_relative':'ACTION_AJUSTEE_DIVIDENDES_VS_SP500_INDICE_PRIX : pas une comparaison total-return homogène ; aucune note automatique','usage_retrospectif_T0':'INTERDIT_SANS_ARCHIVE_POINT_IN_TIME','reserve_credits_autres_outils':10000}
 try:
  usage=client.get('user',archive=False)
  used=int(usage.get('apiRequests') or 0) if str(usage.get('apiRequestsDate',''))[:10]==now.date().isoformat() else 0
  client.budget=min(5000,max(0,int(usage.get('dailyRateLimit') or 0)-used-10000))
  if client.budget<2*min(taille,len(u))+2:raise RuntimeError('QUOTA_INSUFFISANT_RESERVE_AUTRES_OUTILS')
  # La dernière séance du S&P500 devient l'ancre commune, y compris le dimanche.
  fin=(now-timedelta(days=1)).date().isoformat();debut=(now-timedelta(days=410)).date().isoformat()
  params={'from':debut,'to':fin,'period':'d','order':'a'}
  index=serie(client.get('eod/GSPC.INDX',params),fin)
  valides=[r for r in index if r['adjusted_close'] is not None]
  if not valides:raise RuntimeError('INDICE_REFERENCE_ABSENT')
  ref=valides[-1]['date']
  if (pd.Timestamp(fin)-pd.Timestamp(ref)).days>7:raise RuntimeError('INDICE_REFERENCE_ANCIEN')
  for n,t in enumerate(tickers):
   row={'Ticker':t,'Date_reference':ref,'Notes_attribuees':0,'Statut_B7':'A_VERIFIER_VOLUMES_TURNOVER_SPREAD','Statut_collecte':'HORS_LOT_TECHNIQUE'}
   if n<taille and not fatal:
    try:
     data=client.get('eod/'+t,params);archive_histoire=client.index[-1].get('archive_chiffree','')
     m=mesurer(data,ref,index)
     if m.get('Statut')=='MESURES_A_VERIFIER_IDENTITE_ET_LIQUIDITE' and m.get('Seances_volume_63s')==63:
      try:
       evenements=client.get('splits/'+t,{'from':debut,'to':now.date().isoformat()})
       m=mesurer(data,ref,index,evenements,now.date().isoformat())
      except Exception as exc:
       m['Erreur_splits']=str(exc) if isinstance(exc,(RuntimeError,ValueError)) else type(exc).__name__
       if any(c in m['Erreur_splits'] for c in ('EODHD_HTTP_401','EODHD_HTTP_402','EODHD_HTTP_403','EODHD_HTTP_429','QUOTA_')):fatal=m['Erreur_splits']
     metrics.append(dict(Ticker=t,**m))
     row.update({'Statut_collecte':m['Statut'],'Date_dernier_cours':m.get('Date_dernier_cours',''),
       'Seances_recues':m['Seances_recues'],'Seances_ajustees':m['Seances_ajustees'],
       'Momentum_1_3_6_12_disponibles':'OUI' if all('Momentum_'+str(k)+'m_pct' in m for k in (1,3,6,12)) else 'NON',
       'Volume_monetaire_63s_disponible':'OUI' if 'Volume_monetaire_median_63s_USD' in m else 'NON',
       'Force_relative_1_3_6_12_disponible':'OUI' if all('Force_relative_SP500_'+str(k)+'m_pct' in m for k in (1,3,6,12)) else 'NON',
       'Volume_titres_63s_disponible':'OUI' if 'Volume_titres_median_63s' in m else 'NON',
       'Correction_splits':m.get('Statut_volume_monetaire','NON_APPLICABLE'),
       'Archive_historique_chiffree':archive_histoire})
    except Exception as exc:
     motif=str(exc) if isinstance(exc,(RuntimeError,ValueError)) else type(exc).__name__
     row.update(Statut_collecte='BLOQUE_SOURCE_OU_DONNEES',Motif=motif)
     if any(code in motif for code in ('EODHD_HTTP_401','EODHD_HTTP_402','EODHD_HTTP_403','EODHD_HTTP_429','QUOTA_')):fatal=motif
   elif fatal:row['Statut_collecte']='NON_TENTE_APRES_ERREUR_ACCES_OU_QUOTA'
   rows.append(row)
   if (n+1)%100==0:print('Historique US : '+str(n+1)+'/'+str(len(tickers))+' lignes traitées ; aucune note attribuée',flush=True)
  if fatal:raise RuntimeError(fatal)
 except Exception as exc:
  fatal=str(exc) if isinstance(exc,(ValueError,RuntimeError)) else type(exc).__name__
 finally:
  if not rows:rows=[{'Ticker':t,'Statut_collecte':'NON_TENTE_ERREUR_REFERENCE','Motif':fatal,'Notes_attribuees':0} for t in tickers]
  pub=pd.DataFrame(rows);pub.to_csv(out/'COUVERTURE_MARCHE_US.csv',index=False)
  client.archiver('METRIQUES_MARCHE_US',metrics)
  bilan.update(date_reference=ref,cotations_tentees=sum(r['Statut_collecte'] not in ('HORS_LOT_TECHNIQUE','NON_TENTE_APRES_ERREUR_ACCES_OU_QUOTA','NON_TENTE_ERREUR_REFERENCE') for r in rows),
    historiques_avec_cours_reference=sum(r.get('Statut_collecte')=='MESURES_A_VERIFIER_IDENTITE_ET_LIQUIDITE' for r in rows),
    momentum_1_3_6_12_disponibles=sum(r.get('Momentum_1_3_6_12_disponibles')=='OUI' for r in rows),
    volumes_monetaires_63s_disponibles=sum(r.get('Volume_monetaire_63s_disponible')=='OUI' for r in rows),
    force_relative_1_3_6_12_disponible=sum(r.get('Force_relative_1_3_6_12_disponible')=='OUI' for r in rows),
    requetes_credits_estimes=client.cout,erreur_bloquante=fatal,collecte_tous_dossiers_tentee=len(rows)==len(tickers) and all(r['Statut_collecte'] not in ('HORS_LOT_TECHNIQUE','NON_TENTE_APRES_ERREUR_ACCES_OU_QUOTA','NON_TENTE_ERREUR_REFERENCE') for r in rows))
  bilan['fichiers']={p.name:sha(p) for p in out.iterdir() if p.is_file()}
  (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(bilan,ensure_ascii=False))
 if fatal:raise RuntimeError('COLLECTE_MARCHE_BLOQUEE:'+fatal)
 return bilan
if __name__=='__main__':executer()

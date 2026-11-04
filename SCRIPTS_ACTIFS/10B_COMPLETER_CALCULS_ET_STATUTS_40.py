#!/usr/bin/env python3
"""Offline factual completion, explicit NA and individual residual dependencies.
No scoring function, changed threshold, synthetic scenario or arbitration.
"""
import csv,importlib.util,json,math,statistics
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'DONNEES';F=B/'DOSSIERS_MCPA_IPS_40';DATE='2026-11-04'
s=importlib.util.spec_from_file_location('enrich',B/'SCRIPTS_ACTIFS/09X_ENRICHIR_AUDITER_40.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
def read(p):return json.loads(p.read_text())
def val(x):return e.number(x)
def na(d,b,k,reason,url,period,status='NON_APPLICABLE'):
 c=d['blocs'][b][k]
 if c['valeur'] is not None:return
 c.update(e.cell(None,'sans objet' if status=='NON_APPLICABLE' else None,period,DATE,url,status,reason));c['recherche']={'date':DATE,'statut':status,'motif':reason,'journal':'journal_recherches'}
def put(d,b,k,v,u,p,url,comment,status='CALCULE_SOURCE_SECONDAIRE'):
 return e.put(d,b,k,e.cell(v,u,p,DATE,url,status,comment))
def corr(a,b):
 if len(a)<20 or statistics.pstdev(a)==0 or statistics.pstdev(b)==0:return None
 am=statistics.mean(a);bm=statistics.mean(b)
 return sum((x-am)*(y-bm) for x,y in zip(a,b))/math.sqrt(sum((x-am)**2 for x in a)*sum((y-bm)**2 for y in b))
def main():
 docs=sorted([read(p) for p in F.glob('*.json')],key=lambda x:x['id_position']);stats={x['ticker']:x for x in read(D/'STATISTIQUES_SECONDAIRES_40_20261104.json')};annual={x['ticker']:x for x in read(D/'IDENTITES_CROISSANCE_40_20261104.json')};balances={x['ticker']:x for x in read(D/'BILANS_ANNUELS_40_20261104.json')}
 eo={x['Ticker']:x for x in csv.DictReader((B/'AUDITS/POURSUITE_FICHES_40_20261104/EODHD/COLLECTE_40.csv').open())}
 histories={}
 for r in csv.DictReader((D/'HISTORIQUES_YAHOO_40.csv').open()):
  if r['Date_UTC']<=e.PRICE_CUTOFF:histories.setdefault(r['Ticker'],{})[r['Date_UTC']]=float(r['AdjClose'])
 sectors={d['ticker']:d['blocs']['diversification']['exposition_sectorielle']['valeur'] for d in docs}
 output=[];matrix=[]
 for d in docs:
  t=d['ticker'];st=stats[t];m=st.get('mesures',{});url=st['url'];period='TTM fournisseur, arrêté à rapprocher';net=val(m.get('Net Income'));fcf=val(m.get('Free Cash Flow'));ebitda=val(m.get('EBITDA'));ebit=val(m.get('Operating Income'))
  for b,k,base,label in [('valorisation','pe',net,'résultat net'),('valorisation','p_fcf',fcf,'FCF'),('valorisation','ev_ebitda',ebitda,'EBITDA'),('valorisation','ev_ebit',ebit,'EBIT'),('qualite','conversion_fcf_pct',net,'résultat net')]:
   if base is not None and base<=0:na(d,b,k,label+' TTM non positif : ratio de valorisation ou conversion non interprétable selon cette convention; aucune substitution par zéro.',url,period)
  if fcf is not None and fcf>=0:na(d,'risque','cash_runway_mois','FCF TTM non négatif : extrapolation cash/consommation FCF non applicable. Ne démontre pas absence de risque futur de liquidité.',url,period)
  ar=annual[t].get('annuel',{});rows={r[0]:r[1:] for r in ar.get('lignes',[])};head=rows.get('Fiscal Year',[]);idx=[i for i,h in enumerate(head) if __import__('re').fullmatch('FY ?20[0-9][0-9]',h)]
  if len(idx)>=2:
   i,j=idx[:2]
   for k,label in [('croissance_bpa_pct','EPS (Diluted)'),('croissance_ebitda_pct','EBITDA'),('croissance_fcf_pct','Free Cash Flow')]:
    series=rows.get(label,[])
    if len(series)>j and val(series[j]) is not None and val(series[j])<=0:na(d,'croissance',k,'Base annuelle '+label+' non positive; variation en pourcentage non interprétable. Comparer montants/signes, sans croissance fictive.',ar['url'],head[i]+' / '+head[j])
  br=balances[t];rr={r[0]:r[1:] for r in br.get('lignes',[])};hh=rr.get('Fiscal Year',[]);ii=[i for i,h in enumerate(hh) if __import__('re').fullmatch('FY ?20[0-9][0-9]',h)]
  shares=rr.get('Total Common Shares Outstanding',rr.get('Shares Outstanding',[]))
  if len(ii)>=4:
   i,j=ii[0],ii[3]
   if len(shares)>max(i,j) and int(hh[i][-4:])-int(hh[j][-4:])==3:
    a,b=val(shares[i]),val(shares[j])
    if a is not None and b and b>0:put(d,'risque','dilution_3a_pct',(a/b-1)*100,'pct',hh[j]+' / '+hh[i],br['url'],'Variation des actions ordinaires de clôture sur trois exercices; chiffres fournisseur arrondis. Pas la dilution potentielle options/convertibles; splits à rapprocher.')
  source='DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv | '+annual[t].get('profil',{}).get('url','')
  sector=sectors[t]
  if sector:
   peers=[x['ticker'] for x in docs if sectors[x['ticker']]==sector]
   put(d,'diversification','concentration_theme',dict(classification=sector,nombre_lignes=len(peers),poids_initial_pct=len(peers)*2.5,tickers=peers),'composition T0','40 lignes initiales équipondérées, 01/10/2026',source,'Classification sectorielle secondaire; poids T0 et non poids actualisé, ni exposition économique détaillée. Une industrie n’est pas un thème fin.')
  # Leave-one-out equal-weight basket, local quote returns, not EUR portfolio.
  prices=histories[t];days=sorted(prices);ret={days[i]:prices[days[i]]/prices[days[i-1]]-1 for i in range(1,len(days))};others=[]
  for other in docs:
   ot=other['ticker']
   if ot==t:continue
   pp=histories[ot];dd=sorted(pp);others.append({dd[i]:pp[dd[i]]/pp[dd[i-1]]-1 for i in range(1,len(dd))})
  common=sorted(set(ret).intersection(*(set(o) for o in others)))[-90:]
  if len(common)>=20:
   a=[ret[k] for k in common];b=[statistics.mean(o[k] for o in others) for k in common];c=corr(a,b)
   if c is not None:put(d,'diversification','correlation_portefeuille',c,'Pearson [-1,1]',common[0]+' / '+common[-1]+'; '+str(len(common))+' séances communes','DONNEES/HISTORIQUES_YAHOO_40.csv','Proxy : rendements clôtures ajustées en devises locales, panier quotidien équipondéré des 39 autres lignes. Exclut la ligne; FX et poids réels non intégrés, donc pas corrélation du portefeuille EUR effectif.','CALCULE_PROXY_CORRELATION')
  if t=='ALIEV.PA':
   for k in ['prix_vers_mm200','tendance_mm200','momentum_12m_pct','drawdown_12m_pct']:na(d,'momentum',k,'Historique IPO archivé plus court que la fenêtre requise au 03/11/2026; durée antérieure à la cotation inexistante.', 'DONNEES/HISTORIQUES_YAHOO_40.csv','cotations disponibles au 03/11/2026','INDISPONIBLE_A_DATE_HISTORIQUE_COURT')
  rec={'famille':'EODHD_fondamentaux_execution_GitHub','date':DATE,'endpoint_sans_secret':eo[t]['Endpoint_sans_secret'],'http':eo[t]['HTTP_statut'],'statut':'ACCES_REFUSE' if eo[t]['HTTP_statut']=='403' else 'IDENTITE_FOURNISSEUR_A_RESoudre','preuve':'AUDITS/POURSUITE_FICHES_40_20261104/EODHD/COLLECTE_40.csv','limite':'Échec fournisseur, pas preuve que les données publiques sont inexistantes.'}
  if rec not in d['journal_recherches']:d['journal_recherches'].append(rec)
  rec={'famille':'bilan_annuel_actions','date':DATE,'url':br['url'],'http':br.get('http'),'statut':br['statut']}
  if rec not in d['journal_recherches']:d['journal_recherches'].append(rec)
  counts={'RENSEIGNE':0,'NON_APPLICABLE':0,'INDISPONIBLE_A_DATE':0,'RECHERCHE_A_POURSUIVRE':0};missing=[]
  for block,cc in d['blocs'].items():
   for key,c in cc.items():
    status='RENSEIGNE' if c['valeur'] is not None else ('NON_APPLICABLE' if c['statut']=='NON_APPLICABLE' else ('INDISPONIBLE_A_DATE' if c['statut'].startswith('INDISPONIBLE_A_DATE') else 'RECHERCHE_A_POURSUIVRE'))
    counts[status]+=1
    if status=='RECHERCHE_A_POURSUIVRE':missing.append(block+'.'+key)
    matrix.append(dict(ticker=t,bloc=block,champ=key,statut=status,motif=c.get('commentaire') or c.get('recherche',{}).get('motif'),source=c.get('source_url')))
  d['audit_couverture']['champs_renseignes']=counts['RENSEIGNE']
  d['audit_couverture']['couverture_pct']=round(counts['RENSEIGNE']/108*100,2)
  d['audit_couverture']['champs_manquants']=[b+'.'+k for b,bl in d['blocs'].items() for k,c in bl.items() if c['valeur'] is None]
  d['audit_poursuite']={'date':DATE,'comptage':counts,'couverture_valeurs_pct':round(counts['RENSEIGNE']/108*100,2),'couverture_applicable_pct':round(counts['RENSEIGNE']/(108-counts['NON_APPLICABLE'])*100,2),'recherches_non_closes':missing,'notes_justifiees':False,'validation_individuelle':'BLOQUEE_DONNEES_ET_ANALYSES_RESTANTES','aucune_indisponibilite_definitive_presumee':True}
  for p in F.glob('*.json'):
   if read(p)['ticker']==t:p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n');break
  output.append(dict(Ticker=t,Societe=d['societe'],**counts,Couverture_valeurs_pct=d['audit_poursuite']['couverture_valeurs_pct'],Validation='BLOQUEE'))
 (D/'MATRICE_CHAMPS_POURSUITE_40_20261104.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
 with (D/'COUVERTURE_POURSUITE_40_20261104.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=output[0].keys());w.writeheader();w.writerows(output)
 print({k:sum(r[k] for r in output) for k in counts})
if __name__=='__main__':main()

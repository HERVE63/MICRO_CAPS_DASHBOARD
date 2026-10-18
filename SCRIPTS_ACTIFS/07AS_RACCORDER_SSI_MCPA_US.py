"""Liste permanente US : preuves SSI revalidées puis analyses MCPA documentées.
Aucune note produite, aucun arbitrage ; la couverture du recensement reste visible.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys
import pandas as pd
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE/'SCRIPTS_ACTIFS'))
from preuves_ssi import registre,valider_dossier

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fichier(d,m,n):
 p=d/n
 if not p.is_file() or m['fichiers'].get(n)!=sha(p):raise RuntimeError('ARCHIVE_MCPA_SSI_DIVERGENTE:'+n)
 return p

def valider_analyse(path,ssi,base=BASE):
 m=json.loads(path.read_text());t=m['Ticker'];now=pd.Timestamp.now(tz='UTC');date=pd.to_datetime(m['Date_analyse_UTC'],utc=True,errors='raise')
 if date>now:raise RuntimeError('ANALYSE_MCPA_FUTURE')
 if m.get('reference_notes_SSI')!={k:str(ssi[k]) for k in m.get('reference_notes_SSI',{})} or len(m.get('reference_notes_SSI',{}))!=14:raise RuntimeError('PREUVES_SSI_ANALYSE_PERIMEES')
 if m.get('cohorte_T0_SHA256')!=sha(base/'DONNEES/COHORTE_MICRO_CAPS_T0.csv'):raise RuntimeError('BASE_IPS_COHORTE_DIVERGENTE')
 if m['SSI']!=int(ssi.SSI) or ssi.Statut_SSI!='ADMIS_SSI' or ssi.SCE_valide!='OUI':raise RuntimeError('MCPA_SANS_ADMISSION_SSI_ACTUELLE')
 for name in m['fichiers']:fichier(path.parent,m,name)
 notes=pd.read_csv(fichier(path.parent,m,'NOTES_MCPA_JUSTIFIEES.csv'),keep_default_na=False)
 maxima={'Q':30,'V':20,'G':20,'R':10,'M':10,'D':10}
 if set(notes.Bloc)!=set(maxima) or len(notes)!=6 or set(notes.Ticker)!={t}:raise RuntimeError('BLOCS_MCPA_INCOMPLETS')
 for _,r in notes.iterrows():
  if float(r.Maximum)!=maxima[r.Bloc] or not 0<=float(r.Note)<=maxima[r.Bloc] or not str(r.Justification).strip():raise RuntimeError('NOTE_MCPA_NON_JUSTIFIEE')
 if abs(notes.Note.astype(float).sum()-float(m['MCPA']))>1e-9:raise RuntimeError('TOTAL_MCPA_DIVERGENT')
 for k in ['IC_sur_5','CX_sur_5']:
  if not 0<=float(m[k])<=5:raise RuntimeError('IC_CX_INVALIDES')
 ww=pd.read_csv(fichier(path.parent,m,'WWWS.csv'))
 if len(ww)!=5 or ww.Bloc.nunique()!=5 or not ww.Poids_pct.eq(20).all() or not ww.Note_sur_20.between(0,20).all() or abs(ww.Note_sur_20.sum()-float(m['WWWS']))>1e-9:raise RuntimeError('WWWS_DIVERGENT')
 sc=pd.read_csv(fichier(path.parent,m,'SCENARIOS_3_6_MOIS.csv'))
 if set(sc.Horizon_mois)!={3,6} or len(sc)!=6:raise RuntimeError('SCENARIOS_INCOMPLETS')
 for _,g in sc.groupby('Horizon_mois'):
  if set(g.Scenario)!={'BEAR','CENTRAL','BULL'} or len(g)!=3 or not g.Probabilite_jugement_pct.between(0,100).all() or abs(g.Probabilite_jugement_pct.sum()-100)>1e-9:raise RuntimeError('PROBABILITES_INVALIDES')
  calcul=((1+g.Variation_prix_hypothese_pct/100)*.975/1.025-1)*100
  if not (abs(calcul-g.Rendement_apres_achat_vente_2_5_pct)<1e-8).all():raise RuntimeError('FRAIS_SCENARIOS_DIVERGENTS')
 if bool(m['Candidat_serieux'])!=(m['MCPA']>=80):raise RuntimeError('SEUIL_CANDIDAT_DIVERGENT')
 return m

def executer():
 sources=sorted((BASE/'AUDITS/SCE_DISCOVERY_US').glob('*/MANIFESTE.json'))
 if not sources:raise RuntimeError('SSI_US_ABSENT')
 sp=sources[-1];sm=json.loads(sp.read_text());ssi=pd.read_csv(fichier(sp.parent,sm,'RESULTATS_SSI.csv'),dtype=str,keep_default_na=False)
 if ssi.Ticker.duplicated().any():raise RuntimeError('SSI_US_DUPLIQUE')
 preuves=registre(BASE);admis=[]
 for _,r in ssi[ssi.Statut_SSI.eq('ADMIS_SSI')].iterrows():
  n,e=valider_dossier(r,preuves,BASE)
  if e or sum(n)!=int(r.SSI) or r.SCE_valide!='OUI':raise RuntimeError('ADMISSION_SSI_PERIMEE:'+r.Ticker)
  admis.append(r.Ticker)
 analyses={};sources_hash={str(sp.relative_to(BASE)):sha(sp)}
 for p in sorted((BASE/'AUDITS/MCPA_IPS_DOCUMENTAIRE_US').glob('*/MANIFESTE.json')):
  m=json.loads(p.read_text());t=m['Ticker']
  if t not in admis:raise RuntimeError('ANALYSE_MCPA_EMETTEUR_NON_ADMIS:'+t)
  m=valider_analyse(p,ssi[ssi.Ticker.eq(t)].iloc[0],BASE)
  if t in analyses:raise RuntimeError('ANALYSES_MCPA_MULTIPLES_A_RECONCILIER:'+t)
  analyses[t]=m;sources_hash[str(p.relative_to(BASE))]=sha(p)
 out=BASE/'AUDITS/LISTE_PERMANENTE_US'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 rows=[]
 for t in admis:
  m=analyses.get(t,{});r=ssi[ssi.Ticker.eq(t)].iloc[0]
  rows.append({'Ticker':t,'Societe':r.Societe,'SSI':r.SSI,'MCPA':m.get('MCPA','MANQUANTE'),'IC':m.get('IC_sur_5','MANQUANTE'),'CX':m.get('CX_sur_5','MANQUANTE'),'WWWS':m.get('WWWS','MANQUANTE'),'Statut':'CANDIDATURE_SERIEUSE_A_CONFRONTER' if m.get('Candidat_serieux') else 'WATCHLIST_MCPA_SOUS_80' if m else 'MCPA_A_ANALYSER','Analyse_source':next((p for p in sources_hash if 'MCPA_IPS' in p and json.loads((BASE/p).read_text())['Ticker']==t),''),'Arbitrage_autorise':'NON'})
 pd.DataFrame(rows,columns=['Ticker','Societe','SSI','MCPA','IC','CX','WWWS','Statut','Analyse_source','Arbitrage_autorise']).to_csv(out/'LISTE_PERMANENTE_US.csv',index=False)
 complets=int(ssi.Statut_SSI.isin(['ADMIS_SSI','REFUSE_SSI']).sum());candidats=sum(bool(m['Candidat_serieux']) for m in analyses.values())
 bilan={'Date_UTC':datetime.now(timezone.utc).isoformat(),'sources':sources_hash,'cotations_univers':len(ssi),'dossiers_SSI_complets':complets,'couverture_qualification_pct':complets/len(ssi)*100,'minimum_50_pct_atteint':complets>=len(ssi)*.5,'admis_SSI':len(admis),'analyses_MCPA':len(analyses),'candidatures_MCPA_80':candidats,'Top20_valide':False,'Top5_valide':False,'selection_finale_terminee':False,'motifs':['Couverture SSI insuffisante pour un classement représentatif','Revue financière complète des 40 titulaires non validée','Aucune candidature MCPA >=80 actuellement'] if not candidats else ['Couverture, IPS et confrontation aux 40 à contrôler avant décision'],'operations_ecrites':0,'fichiers':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(bilan,ensure_ascii=False));return bilan
if __name__=='__main__':executer()

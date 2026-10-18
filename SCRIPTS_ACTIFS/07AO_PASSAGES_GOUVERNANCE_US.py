"""Lire les proxies SEC archivés : passages B4/B5, sans interpréter les titres.
Une propriété bénéficiaire peut inclure options, warrants et droits à 60 jours.
Ces passages ne sont ni des détentions personnelles nettes ni des notes SSI.
"""
from pathlib import Path
from datetime import datetime,timezone
from html.parser import HTMLParser
import gzip,hashlib,importlib.util,json,re
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def charger(nom):
 s=importlib.util.spec_from_file_location(nom[:-3],BASE/'SCRIPTS_ACTIFS'/nom);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Texte(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','ix:header'):self.skip+=1
 def handle_endtag(self,tag):
  if tag in ('script','style','ix:header'):self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip and data.strip():self.parts.append(data)
def texte_brut(raw):
 if raw.startswith(b'%PDF'):raise ValueError('PDF_A_LIRE_SEPAREMENT')
 p=Texte();p.feed(raw.decode('utf-8',errors='replace'));p.close();return re.sub(r'\s+',' ',' '.join(p.parts)).strip()
MOTIFS={
 'DETENTION_GROUPE':r'(?:all\s+)?(?:current\s+)?(?:directors?\s+and\s+(?:executive\s+)?officers?|(?:executive\s+)?officers?\s+and\s+directors?)(?:.{0,80}?)as\s+a\s+group',
 'DROITS_A_60_JOURS':r'(?:within\s+60\s+days|within\s+sixty\s+days|right\s+to\s+acquire)',
 'DILUTION_REMUNERATION':r'(?:equity\s+compensation\s+plan\s+information|securities\s+authorized\s+for\s+issuance|outstanding\s+equity\s+awards)'}
def extraire(texte):
 result=[]
 for nature,pattern in MOTIFS.items():
  intervals=[]
  for match in re.finditer(pattern,texte,re.I):
   a=max(0,match.start()-1800);b=min(len(texte),match.end()+6500)
   if intervals and a<=intervals[-1][1]:intervals[-1]=(intervals[-1][0],max(b,intervals[-1][1]))
   else:intervals.append((a,b))
  for a,b in intervals:result.append({'Nature':nature,'Debut_texte_normalise':a,'Fin_texte_normalise':b,'Passage':texte[a:b],
   'Interpretation':'A_VERIFIER_TITRES_REELS_OPTIONS_WARRANTS_DOUBLES_COMPTES_ET_DATE','Note_SSI':'NON_ATTRIBUEE'})
 return result

def executer():
 now=datetime.now(timezone.utc);util=charger('07AI_RACCORDER_COMPTES_US_SSI.py');af=charger('07AF_COLLECTER_DOCUMENTS_US.py')
 def dernier(nom):
  p=sorted((BASE/'AUDITS'/nom).glob('*/MANIFESTE.json'))[-1];return p,json.loads(p.read_text())
 pp,pm=dernier('PROFILS_SEC_UNIVERS_US');dp,dm=dernier('DOCUMENTS_US');cp,cm=dernier('CONTROLE_DOCUMENTS_US')
 if cm['archive_source']!=str(dp.relative_to(BASE)):raise RuntimeError('CONTROLE_DOCUMENTAIRE_NON_CONCORDANT')
 if dm['univers_source']!=str((pp.parent/'UNIVERS_SEC_COTATIONS_US.csv').relative_to(BASE)):raise RuntimeError('DOCUMENTS_HORS_UNIVERS')
 universe=pd.read_csv(util.verifier_fichier(pp.parent,pm,'TOUTES_COTATIONS_RECENSEES.csv'),dtype=str,keep_default_na=False)
 docs=pd.read_csv(util.verifier_fichier(dp.parent,dm,'AUDIT_DOCUMENTS.csv'),dtype=str,keep_default_na=False)
 controls=pd.read_csv(util.verifier_fichier(cp.parent,cm,'CONTROLES_DOCUMENTS.csv'),dtype=str,keep_default_na=False)
 out=BASE/'AUDITS/PASSAGES_GOUVERNANCE_US'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 audit=[];counts={};records=[]
 for _,r in docs[docs.Formulaire.eq('DEF 14A')].iterrows():
  a={'Ticker':r.Ticker_cotation,'CIK':r.CIK,'Source_URL':r.Source_URL,'Date_depot':r.Date_depot,'Passages':0,'Notes_attribuees':0}
  c=controls[controls.CIK.eq(r.CIK)&controls.Formulaire.eq(r.Formulaire)&controls.Source_URL.eq(r.Source_URL)]
  if len(c)!=1:raise RuntimeError('CONTROLE_PROXY_NON_UNIQUE')
  if r.Statut!='DOCUMENT_COLLECTE_A_VERIFIER' or c.iloc[0].Controle_document!='CIK_XBRL_CONCORDANT':
   a['Statut']='SOURCE_OU_CIK_A_VERIFIER';audit.append(a);continue
  raw=(BASE/r.Fichier_brut).resolve()
  if raw.parent!=dp.parent.resolve():raise RuntimeError('CHEMIN_PROXY_HORS_ARCHIVE')
  util.verifier_fichier(dp.parent,dm,raw.name);data=af.lire_document(raw)
  if hashlib.sha256(data).hexdigest()!=r.SHA256:raise RuntimeError('EMPREINTE_PROXY_INCOHERENTE')
  if r.Date_depot>dm['date_limite'] or r.Date_depot>now.date().isoformat():raise RuntimeError('DATE_PROXY_FUTURE')
  text=texte_brut(data);passages=extraire(text)
  for p in passages:records.append(dict(a,**p,SHA256_document=r.SHA256,SHA256_texte_normalise=hashlib.sha256(text.encode()).hexdigest(),Fichier_brut=r.Fichier_brut))
  counts[r.CIK]={nature:sum(p['Nature']==nature for p in passages) for nature in MOTIFS}
  a.update(Statut='PASSAGES_A_INTERPRETER' if passages else 'LIBELLES_NON_REPERES_A_RELIRE',Passages=len(passages));audit.append(a)
 pd.DataFrame(audit).to_csv(out/'AUDIT_PASSAGES.csv',index=False)
 with gzip.open(out/'PASSAGES_GOUVERNANCE.jsonl.gz','wt',encoding='utf-8') as f:
  for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 rows=[]
 for _,r in universe.iterrows():
  n=counts.get(r.CIK,{});rows.append({'Ticker':r.Ticker_US,'CIK':r.CIK,**{k:n.get(k,0) for k in MOTIFS},
   'Statut_B4_B5':'CONTENU_A_INTERPRETER_ET_ACTUALISER' if n else 'SOURCE_OU_SECTION_A_COMPLETER','Note_SSI':'MANQUANTE'})
 pd.DataFrame(rows).to_csv(out/'COUVERTURE_PASSAGES_US.csv',index=False)
 bilan={'date_utc':now.isoformat(),'source_script_SHA256':sha(Path(__file__)),
  'sources':{str(p.relative_to(BASE)):sha(p) for p in (pp,dp,cp)},'source_univers_SHA256':sha(pp.parent/'TOUTES_COTATIONS_RECENSEES.csv'),
  'cotations_conservees':len(rows),'proxies_avec_CIK_concordant_et_passages':sum(r['Statut']=='PASSAGES_A_INTERPRETER' for r in audit),
  'proxies_non_traites_source_ou_CIK':sum(r['Statut']=='SOURCE_OU_CIK_A_VERIFIER' for r in audit),
  'passages_extraits':len(records),'emetteurs_avec_passage_detention_groupe':sum(n.get('DETENTION_GROUPE',0)>0 for n in counts.values()),
  'notes_attribuees':0,'detentions_personnelles_net_stocks_calculees':False,'fichiers':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(bilan,ensure_ascii=False));return bilan
if __name__=='__main__':executer()

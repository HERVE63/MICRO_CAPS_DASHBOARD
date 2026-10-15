"""Intégrité, dates et CIK iXBRL des pièces US. Pas de validation SSI implicite."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import pandas as pd
from html.parser import HTMLParser
BASE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cik_document(data):
 class LecteurCIK(HTMLParser):
  def __init__(self):super().__init__(convert_charrefs=True);self.active=[];self.values=set()
  def handle_starttag(self,tag,attrs):
   if (dict(attrs).get('name') or '').lower()=='dei:entitycentralindexkey':self.active.append([tag,[]])
  def handle_data(self,data):
   for _,texts in self.active:texts.append(data)
  def handle_endtag(self,tag):
   if self.active and self.active[-1][0]==tag:
    _,texts=self.active.pop();v=''.join(texts).strip()
    if v.isdigit():self.values.add(v.zfill(10))
 p=LecteurCIK();p.feed(data.decode('utf-8',errors='replace'));p.close();return p.values
def executer():
 now=datetime.now(timezone.utc);audits=sorted((BASE/'AUDITS/DOCUMENTS_US').glob('*/MANIFESTE.json'))
 if not audits:raise RuntimeError('ARCHIVE_DOCUMENTS_US_ABSENTE')
 p=audits[-1];m=json.loads(p.read_text());f=p.parent/'AUDIT_DOCUMENTS.csv'
 if sha(f)!=m['fichiers'][f.name]:raise RuntimeError('AUDIT_DOCUMENTS_US_CORROMPU')
 d=pd.read_csv(f,dtype=str,keep_default_na=False);rows=[]
 for _,r in d.iterrows():
  row={k:r.get(k,'') for k in ['CIK','Ticker_cotation','Formulaire','Source_URL','Date_depot','Fichier_brut','SHA256']}
  row.update(Statut_identite_cotation='A_VERIFIER',Qualification_SSI='NON_EFFECTUEE')
  if r.Statut!='DOCUMENT_COLLECTE_A_VERIFIER':row['Controle_document']='NON_COLLECTE';rows.append(row);continue
  raw=BASE/r.Fichier_brut
  if sha(raw)!=r.SHA256 or m['fichiers'].get(raw.name)!=r.SHA256:raise RuntimeError('DOCUMENT_US_SHA256_DIVERGENT')
  depot=datetime.strptime(r.Date_depot,'%Y-%m-%d').date()
  if depot>now.date() or r.Date_depot>m['date_limite']:raise RuntimeError('DEPOT_FUTUR_US')
  if datetime.fromisoformat(r.Date_collecte_UTC)>now:raise RuntimeError('COLLECTE_FUTURE_US')
  row['Age_depot_jours']=(now.date()-depot).days
  # Un âge élevé est signalé pour revue, sans inventer un seuil d'exclusion.
  data=raw.read_bytes()
  found=cik_document(data) if not data.startswith(b'%PDF') else set()
  row['CIK_document']='|'.join(sorted(found))
  row['Controle_document']='CIK_XBRL_CONCORDANT' if found=={r.CIK} else 'CIK_XBRL_DIVERGENT' if found else 'CIK_XBRL_ABSENT_A_RELIRE'
  rows.append(row)
 out=BASE/'AUDITS/CONTROLE_DOCUMENTS_US'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 result=pd.DataFrame(rows);result.to_csv(out/'CONTROLES_DOCUMENTS.csv',index=False)
 bilan={'date_utc':now.isoformat(),'source_script_SHA256':sha(Path(__file__)),'archive_source':str(p.relative_to(BASE)),
  'documents_controles':len(result),'repartition_controles':result.Controle_document.value_counts().to_dict(),
  'integrite_fichiers':'OK','dates_non_futures':'OK','identites_cotation_validees':0,'notes_attribuees':0,
  'statut':'CONTROLES_DOCUMENTAIRES_SANS_ADMISSION_SSI',
  'fichiers':{'CONTROLES_DOCUMENTS.csv':sha(out/'CONTROLES_DOCUMENTS.csv')}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(bilan,ensure_ascii=False))
 return bilan
if __name__=='__main__':
 r=executer();sys.exit(1 if r['repartition_controles'].get('CIK_XBRL_DIVERGENT',0) else 0)

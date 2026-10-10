"""Enrichissement officiel SEC EDGAR: identite CIK et metadonnees de depots.
Aucune note SSI automatique. Respecte les identites ambigues et les echecs de source.
Variable SEC_USER_AGENT requise: 'Projet Contact contact@example.org'.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, os, time, re, unicodedata
from urllib.request import Request, urlopen
import pandas as pd

D=Path(__file__).resolve().parents[1]/"DONNEES"
SRC=D/"DOSSIERS_SSI_A_QUALIFIER.csv"
OUT=D/"PREUVES_SEC_EDGAR_SSI.csv"
AUD=D/"AUDIT_PREUVES_SEC_SSI.csv"
BASE="https://www.sec.gov"
DATA="https://data.sec.gov"
FORMES={"10-K","10-K/A","10-Q","10-Q/A","8-K","DEF 14A","4","3","5","20-F","6-K","40-F"}
def lire_json(url,agent):
 req=Request(url,headers={"User-Agent":agent,"Accept":"application/json","Accept-Encoding":"identity"})
 with urlopen(req,timeout=25) as resp: return json.load(resp)
def cle_nom(nom,libelle_cotation=False):
 # Le libellé allemand contient parfois une lettre de classe après un grand espace.
 # Nettoyage pour découverte seulement : aucune preuve d'identité n'en découle.
 nom=str(nom).strip()
 if libelle_cotation: nom=re.sub(r'\s{2,}[A-Z]$','',nom)
 nom=unicodedata.normalize('NFKD',nom).encode('ascii','ignore').decode().upper()
 return ' '.join(re.findall(r'[A-Z0-9]+',nom))
def index_registre(reg):
 tickers={};noms={}
 for v in reg.values():
  cik=str(v['cik_str']).zfill(10)
  ticker=str(v.get('ticker','')).upper().strip()
  if ticker:tickers.setdefault(ticker,set()).add(cik)
  nom=cle_nom(v.get('title',''))
  if nom:noms.setdefault(nom,set()).add(cik)
 return tickers,noms
def candidats_registre(r,tickers,noms):
 ticker=str(r['Ticker']).strip().upper()
 # Un code de cotation étranger ne devient jamais un code SEC en retirant son suffixe.
 if ticker in tickers:return tickers[ticker],'TICKER_SEC_EXACT'
 nom=cle_nom(r.get('Societe',''),True)
 return noms.get(nom,set()),'NOM_EXACT_NORMALISE_PISTE'
def executer():
 agent=os.environ.get("SEC_USER_AGENT","").strip()
 if not agent or "@" not in agent: raise RuntimeError("SEC_USER_AGENT explicite avec contact requis")
 if not SRC.exists(): raise RuntimeError("Dossiers SSI absents")
 df=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 if df.empty or df["Ticker"].duplicated().any(): raise RuntimeError("Dossiers SSI vides ou tickers dupliques")
 reg=lire_json(BASE+"/files/company_tickers.json",agent)
 mapping,noms=index_registre(reg)
 eligibles=sorted(str(r['Ticker']).strip() for _,r in df.iterrows()
                  if len(candidats_registre(r,mapping,noms)[0])==1)
 offset=int(os.getenv('SEC_BATCH_OFFSET','0'));taille=int(os.getenv('SEC_BATCH_SIZE','100'))
 if offset<0 or taille<=0:raise ValueError('LOT_SEC_INVALIDE')
 lot=set(eligibles[offset:offset+taille])
 rows=[]
 for _,r in df.iterrows():
  ticker=str(r["Ticker"]).strip()
  # Les suffixes .TO, .V, .L etc ne sont pas des identifiants SEC.
  candidats,methode=candidats_registre(r,mapping,noms)
  pays=str(r.get("Pays","")).strip().upper()
  # SEC n est pas une preuve universelle: verifier la correspondance emetteur.
  # Les tickers etrangers non apparies restent NON_COUVERT.
  item={"Ticker":ticker,"Societe":r.get("Societe",""),"Date_collecte_UTC":globals().get('DATES_SOURCES',{}).get(BASE+'/files/company_tickers.json',datetime.now(timezone.utc).isoformat()),
        "Source_registre":BASE+"/files/company_tickers.json",
        "CIK":"MANQUANTE","Statut_SEC":"NON_COUVERT","Depots": "[]","Nb_depots":0,
        "Methode_rapprochement":methode,"CIK_verifie":"NON","Identite_a_confirmer":"OUI"}
  if len(candidats)>1:
   item["Statut_SEC"]="IDENTITE_AMBIGUE"
  elif len(candidats)==1:
   cik=next(iter(candidats));item["CIK"]=cik
   records=[v for v in reg.values() if str(v['cik_str']).zfill(10)==cik]
   item['Tickers_SEC']=';'.join(sorted({v.get('ticker','') for v in records}))
   item['Nom_registre_SEC']=';'.join(sorted({v.get('title','') for v in records}))
   if ticker not in lot:
    item['Statut_SEC']='PISTE_SEC_HORS_LOT'
    rows.append(item);continue
   url=DATA+"/submissions/CIK"+cik+".json"
   try:
    sub=lire_json(url,agent)
    item['Date_collecte_UTC']=globals().get('DATES_SOURCES',{}).get(url,datetime.now(timezone.utc).isoformat())
    if str(sub.get("cik","")).zfill(10)!=cik:
     raise ValueError("CIK_SUBMISSIONS_INCOHERENT")
    nom=str(sub.get("name","")).strip()
    # Ne pas associer les preuves si l'identite emetteur reste a confirmer.
    item["Nom_SEC"]=nom;item["Source_depots"]=url
    item["CIK_verifie"]="NON"
    item["Identite_a_confirmer"]="OUI"
    recent=sub.get("filings",{}).get("recent",{})
    depots=[]
    for i,form in enumerate(recent.get("form",[])):
     if form not in FORMES: continue
     acc=recent.get("accessionNumber",[])
     dates=recent.get("filingDate",[])
     if i>=len(acc) or i>=len(dates): continue
     limite=os.getenv("MICRO_CAPS_AS_OF",datetime.now(timezone.utc).date().isoformat())
     try: date_depot=datetime.strptime(dates[i],"%Y-%m-%d").date()
     except (ValueError,TypeError):continue
     if dates[i]>limite or not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}",acc[i]):continue
     archive=BASE+"/Archives/edgar/data/"+str(int(cik))+"/"+acc[i].replace("-","")+"/"
     depots.append({"form":form,"date":dates[i],"accession":acc[i],
                    "url_archive_officielle":archive,
                    "source":url,"statut_preuve":"DOCUMENT_A_LIRE"})
     if len(depots)>=30: break
    item["Depots"]=json.dumps(depots,ensure_ascii=False)
    item["Nb_depots"]=len(depots)
    item["Statut_SEC"]="A_VERIFIER_IDENTITE_ET_CONTENU"
   except Exception as exc:
    item["Statut_SEC"]="ERREUR_SOURCE"
    item["Erreur"]=type(exc).__name__
   time.sleep(0.15)
  rows.append(item)
 out=pd.DataFrame(rows)
 OUT.parent.mkdir(parents=True,exist_ok=True)
 out.to_csv(OUT,index=False)
 counts=out["Statut_SEC"].value_counts().to_dict()
 pd.DataFrame([{"Dossiers":len(out),**counts,"Pistes_uniques":len(eligibles),
                "Pistes_dans_lot":len(lot),"Offset":offset,"Scores_SSI_calcules":0}]).to_csv(AUD,index=False)
 print("SEC EDGAR",counts)
 return out
if __name__=="__main__": executer()

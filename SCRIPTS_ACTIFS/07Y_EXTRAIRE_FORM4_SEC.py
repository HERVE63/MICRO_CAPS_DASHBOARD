"""Extraction conservatrice des transactions Form 4 via XML SEC officiel.
Ne calcule ni pourcentage de detention ni note SSI. Les codes ne prouvent pas
a eux seuls un achat personnel; les transactions sont des observations a auditer.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import json, re, os, time
from datetime import datetime, timezone
import pandas as pd

D=Path(__file__).resolve().parents[1]/"DONNEES"
SRC=D/"PISTES_GOUVERNANCE_SEC_SSI.csv"
OUT=D/"TRANSACTIONS_DIRIGEANTS_SEC_SSI.csv"
AUD=D/"AUDIT_TRANSACTIONS_DIRIGEANTS_SEC_SSI.csv"
ACC=re.compile(r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")
def texte(node,path):
 el=node.find(path)
 return (el.text or "").strip() if el is not None else ""
EXTRA_COLS=['Numero_ligne_XML','Titre_valeur','CIK_declarants','Nombre_declarants','Qualites_declarants_JSON','Plan_10b5_1_declare','Nature_detention_indirecte','Footnotes_ligne_JSON','Footnotes_document_JSON','Date_originale_amendement']
def analyser_xml(xml):
 root=ET.fromstring(xml)
 if root.tag!="ownershipDocument":raise ValueError("Document non ownershipDocument")
 noms=[texte(x,"rptOwnerName") for x in root.findall("./reportingOwner/reportingOwnerId")]
 owners=[]
 for o in root.findall('./reportingOwner'):
  owners.append({'CIK':texte(o,'reportingOwnerId/rptOwnerCik'),'Nom':texte(o,'reportingOwnerId/rptOwnerName'),
   'isDirector':texte(o,'reportingOwnerRelationship/isDirector'),'isOfficer':texte(o,'reportingOwnerRelationship/isOfficer'),
   'isTenPercentOwner':texte(o,'reportingOwnerRelationship/isTenPercentOwner'),'officerTitle':texte(o,'reportingOwnerRelationship/officerTitle')})
 footnotes={z.attrib.get('id',''):''.join(z.itertext()).strip() for z in root.findall('./footnotes/footnote')}
 rows=[]
 for numero,x in enumerate(root.findall("./nonDerivativeTable/nonDerivativeTransaction"),1):
  code=texte(x,"transactionCoding/transactionCode")
  if not code:continue
  refs=[z.attrib.get('id','') for z in x.findall('.//footnoteId')]
  rows.append({'Numero_ligne_XML':numero,'Titre_valeur':texte(x,'securityTitle/value'),
   'CIK_declarants':'|'.join(o['CIK'] for o in owners),'Nombre_declarants':len(owners),
   'Qualites_declarants_JSON':json.dumps(owners,ensure_ascii=False),
   'Plan_10b5_1_declare':texte(root,'aff10b5One'),'Nature_detention_indirecte':texte(x,'ownershipNature/natureOfOwnership/value'),
   'Footnotes_ligne_JSON':json.dumps({k:footnotes.get(k,'REFERENCE_ABSENTE') for k in refs},ensure_ascii=False),
   'Footnotes_document_JSON':json.dumps(footnotes,ensure_ascii=False),
   'Date_originale_amendement':texte(root,'dateOfOriginalSubmission'),"Dirigeants_declares":"; ".join(n for n in noms if n),
   "Date_transaction":texte(x,"transactionDate/value"),
   "Code_transaction":code,"Acquisition_cession":texte(x,"transactionAmounts/transactionAcquiredDisposedCode/value"),
   "Titres_transaction":texte(x,"transactionAmounts/transactionShares/value"),
   "Prix_par_titre":texte(x,"transactionAmounts/transactionPricePerShare/value"),
   "Titres_apres_transaction":texte(x,"postTransactionAmounts/sharesOwnedFollowingTransaction/value"),
   "Detention_directe_indirecte":texte(x,"ownershipNature/directOrIndirectOwnership/value"),
   "Statut_interpretation":"A_VERIFIER_NATURE_FINANCEMENT_ET_PROPRIETE"})
 return rows
def lire_xml(url,agent):
 u=urlparse(url)
 if u.scheme!="https" or u.hostname!="www.sec.gov" or not u.path.startswith("/Archives/edgar/data/"):
  raise ValueError("URL SEC non autorisee")
 req=Request(url,headers={"User-Agent":agent,"Accept":"application/xml","Accept-Encoding":"identity"})
 with urlopen(req,timeout=25) as response:return response.read()
def executer():
 agent=os.environ.get("SEC_USER_AGENT","").strip()
 if "@" not in agent:raise RuntimeError("SEC_USER_AGENT avec contact requis")
 if not SRC.exists():raise RuntimeError("Index gouvernance absent")
 d=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 if "Formulaire" not in d or "Ticker" not in d:raise RuntimeError("Schema index invalide")
 rows=[];audits=[]
 for _,r in d[d["Formulaire"].isin(["4","4/A"])].iterrows():
  limite=os.getenv("MICRO_CAPS_AS_OF",datetime.now(timezone.utc).date().isoformat())
  if r.get("Date_depot",""):
   try:datetime.strptime(r["Date_depot"],"%Y-%m-%d")
   except (ValueError,TypeError):
    audits.append({"Ticker":r["Ticker"],"Accession":r.get("Accession",""),"Statut":"DATE_DEPOT_INVALIDE","Transactions":0});continue
   if r["Date_depot"]>limite:
    audits.append({"Ticker":r["Ticker"],"Accession":r.get("Accession",""),"Statut":"DEPOT_POSTERIEUR_DATE_LIMITE","Transactions":0});continue
  cik=r.get("CIK","");acc=r.get("Accession","")
  if not cik.isdigit() or not ACC.fullmatch(acc):
   audits.append({"Ticker":r["Ticker"],"Accession":acc,"Statut":"IDENTIFIANT_INVALIDE","Transactions":0});continue
  # Form 4 SEC archive: document primaire non connu, l'index seul ne suffit pas.
  # Recuperer index.json pour identifier un XML ownershipDocument sans supposer son nom.
  base="https://www.sec.gov/Archives/edgar/data/"+str(int(cik))+"/"+acc.replace("-","")+"/"
  try:
   from json import load
   req=Request(base+"index.json",headers={"User-Agent":agent,"Accept":"application/json"})
   with urlopen(req,timeout=25) as response:index=load(response)
   files=index.get("directory",{}).get("item",[])
   xmls=[f["name"] for f in files if re.fullmatch(r"[A-Za-z0-9_.-]+\.xml",f.get("name","")) and f["name"].lower()!="filingsummary.xml"]
   # Plusieurs XML peuvent coexister (pieces jointes, schemas): identifier le
   # document ownershipDocument par son contenu, sans choisir au hasard.
   documents=[]
   for nom in xmls:
    url=base+nom
    try:
     contenu=lire_xml(url,agent)
     if ET.fromstring(contenu).tag=="ownershipDocument":
      documents.append((url,contenu))
    except (ET.ParseError,ValueError):
     continue
   if len(documents)!=1:
    audits.append({"Ticker":r["Ticker"],"Accession":acc,"Statut":"OWNERSHIP_XML_AMBIGU_OU_ABSENT","Transactions":0});continue
   url,contenu=documents[0]
   emetteur_cik=texte(ET.fromstring(contenu),"issuer/issuerCik")
   if not emetteur_cik.isdigit() or int(emetteur_cik)!=int(cik):
    audits.append({"Ticker":r["Ticker"],"Accession":acc,"Statut":"CIK_EMETTEUR_FORM4_INCOHERENT","Transactions":0});continue
   transactions=analyser_xml(contenu)
   avant=len(rows)
   for t in transactions:
    date_t=t.get("Date_transaction","")
    # Une date absente reste explicitement à vérifier, jamais inventée.
    if date_t:
     try:datetime.strptime(date_t,"%Y-%m-%d")
     except (ValueError,TypeError):continue
     if date_t>limite:continue
    rows.append({"Ticker":r["Ticker"],"CIK":cik,"Accession":acc,"Source_XML":url,**t,"Note_SSI_attribuee":"NON"})
   audits.append({"Ticker":r["Ticker"],"Accession":acc,"Statut":"TRANSACTIONS_A_VERIFIER","Transactions":len(rows)-avant})
  except Exception as exc:
   audits.append({"Ticker":r["Ticker"],"Accession":acc,"Statut":"ERREUR_"+type(exc).__name__,"Transactions":0})
  time.sleep(0.15)
 cols=["Ticker","CIK","Accession","Source_XML","Dirigeants_declares","Date_transaction","Code_transaction","Acquisition_cession","Titres_transaction","Prix_par_titre","Titres_apres_transaction","Detention_directe_indirecte","Statut_interpretation","Note_SSI_attribuee"]
 pd.DataFrame(rows,columns=cols+EXTRA_COLS).to_csv(OUT,index=False)
 pd.DataFrame(audits,columns=["Ticker","Accession","Statut","Transactions"]).to_csv(AUD,index=False)
 print("Form 4:",len(rows),"transactions a verifier")
 return rows
if __name__=="__main__":executer()

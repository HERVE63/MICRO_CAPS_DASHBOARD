#!/usr/bin/env python3
"""Discover official AMF report records for four issuers whose public PDF hosts fail.
Read-only collection, exact issuer tokens, complete pagination, no missing=zero."""
import json,hashlib,urllib.request,urllib.parse
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'DONNEES';OUT=D/'REGISTRE_RAPPORTS_AMF_4_20261105.json'
TARGETS={'ALSTI.PA','ALLIX.PA','ALCUR.PA','ALSTW.PA'}
rows=[]
for issuer in json.loads((D/'DECLARATIONS_AMF_14_20261105.json').read_text()):
 if issuer['ticker'] not in TARGETS:continue
 row={k:issuer[k] for k in ('ticker','societe','isin','jeton')}
 row.update(date_collecte='2026-11-05',records=[],recherches=[],pagination_complete=False)
 try:
  offset=0;total=None
  while total is None or offset<total:
   params={'Jetons':row['jeton'],'DateDebut':'2026-01-01T00:00:00.000Z','DateFin':'2026-11-05T23:59:59.000Z','From':offset,'Size':100}
   url='https://bdif.amf-france.org/back/api/v1/informations?'+urllib.parse.urlencode(params)
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'}),timeout=35) as response:raw=response.read();http=response.status
   obj=json.loads(raw);total=obj['total'];page=obj.get('result',[])
   row['recherches'].append(dict(url=url,http=http,sha256=hashlib.sha256(raw).hexdigest(),total=total,offset=offset))
   if total>2000 or (not page and offset<total):raise ValueError('Pagination incoherente')
   for info in page:
    if not any(x.get('jeton')==row['jeton'] for x in info.get('societes',[])):raise ValueError('Emetteur divergent')
    # Keep full non-DD metadata only. Existing DD evidence is already archived.
    if 'DD' not in str(info.get('numero','')):row['records'].append(info)
   offset+=len(page)
   if not total:break
  row['pagination_complete']=True;row['statut']='REGISTRE_CONSULTE_SANS_PREJUGER_CONTENU'
 except Exception as exc:row.update(statut='RECHERCHE_NON_CLOSE',erreur=type(exc).__name__,http=getattr(exc,'code',None))
 rows.append(row)
 D.mkdir(exist_ok=True);OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'ticker':r['ticker'],'records':len(r['records']),'statut':r['statut']} for r in rows]))
if len(rows)!=4:raise RuntimeError('Quatre emetteurs requis')

# Public publisher fallback: never turn inaccessible reports into unavailable facts.
import re,html,tempfile,subprocess,shutil,unicodedata
PAGES={
 'ALSTI.PA':'https://investir.stif.fr/documentations-financieres/',
 'ALLIX.PA':'https://wallix.actusnews.com/site/documents.php?langue=FR',
 'ALCUR.PA':'https://www.actusnews.com/fr/telechargement/arcure/2026/04/22/97646-arcure_rapport_financier_annuel_2025.pdf',
 'ALSTW.PA':'https://www.streamwide.com/fr/media_center/streamwide-_-rapport-financier-annuel-2025/'
}
for row in rows:
 url=PAGES[row['ticker']];proof={'url':url,'statut':'RECHERCHE_NON_CLOSE'}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40) as response:raw=response.read();proof['http']=response.status
  proof['sha256']=hashlib.sha256(raw).hexdigest()
  if raw.startswith(b'%PDF'):
   proof['format']='PDF';proof['statut']='DOCUMENT_RECUPERE_CONTENU_A_VERIFIER'
   if shutil.which('pdftotext'):
    with tempfile.TemporaryDirectory() as folder:
     pdf=Path(folder)/'source.pdf';txt=Path(folder)/'source.txt';pdf.write_bytes(raw)
     subprocess.run(['pdftotext','-layout',str(pdf),str(txt)],check=True,capture_output=True)
     lines=txt.read_text().splitlines();selected=[];active=0
     for line in lines:
      norm=unicodedata.normalize('NFKD',line).encode('ascii','ignore').decode().lower()
      if any(marker in norm for marker in ('repartition du capital','participation au capital','detention du capital','principaux actionnaires')):active=110
      if active:
       active-=1
       if len(re.findall(r'\d[\d .,]*',line))>=3 and len(line.split())<=20 and len(line.strip())<180 and not any(x in norm for x in ('rue ','avenue','boulevard','demeurant','ne le ')):
        clean=' '.join(line.split())
        if clean not in selected:selected.append(clean)
     proof['lignes_factuelles_candidates_non_validees']=selected[:12]
  else:
   proof['format']='HTML';text=html.unescape(raw.decode('utf-8','replace')).replace('\\/','/')
   links=re.findall(r'(?:https?://[^\s"<>]+\.pdf(?:\?[^\s"<>]*)?|/[^\s"<>]+\.pdf(?:\?[^\s"<>]*)?)',text,re.I)
   proof['pdf_identifies']=sorted(set(urllib.parse.urljoin(url,x) for x in links))
   proof['statut']='LIENS_IDENTIFIES_A_EXAMINER'
 except Exception as exc:proof.update(erreur=type(exc).__name__,http=getattr(exc,'code',proof.get('http')))
 row['repli_editeur_public']=proof
OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'ticker':r['ticker'],'editeur':r['repli_editeur_public']['statut']} for r in rows]))

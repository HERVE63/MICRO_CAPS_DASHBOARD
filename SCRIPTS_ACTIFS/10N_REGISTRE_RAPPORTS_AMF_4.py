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

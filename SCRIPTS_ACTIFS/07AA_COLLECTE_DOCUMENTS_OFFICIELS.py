"""Collecte de documents d'émetteurs et dépôts officiels hors SEC.
URLs et identité doivent être sourcées dans le registre ; aucune devinette de domaine.
Collecter le document n'admet pas le dossier et n'attribue aucune note.
"""
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlparse
import hashlib, ipaddress, json, os, re, socket
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
REG=BASE/'CONFIG/DOCUMENTS_OFFICIELS_A_COLLECTER.csv'
COLS=['ID_document','Ticker','Identifiant_emetteur','Source_URL','Type_source','Date_publication',
      'Domaine_autorise','Source_habilitation_domaine','Statut_identite']
def verifier_url(url,domaines):
    u=urlparse(url)
    if u.scheme!='https' or u.username or u.password or u.port not in (None,443):raise ValueError('URL non HTTPS publique')
    if u.hostname not in domaines:raise ValueError('Domaine hors registre autorisé')
    for x in socket.getaddrinfo(u.hostname,443):
        if not ipaddress.ip_address(x[4][0]).is_global:raise ValueError('Adresse réseau non publique')
    return url
class Redirections(HTTPRedirectHandler):
    def __init__(self,domaines):self.domaines=domaines
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        verifier_url(newurl,self.domaines)
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def executer():
    d=pd.read_csv(REG,dtype=str,keep_default_na=False)
    if not set(COLS).issubset(d.columns) or d.ID_document.duplicated().any():raise RuntimeError('Registre documents invalide')
    now=datetime.now(timezone.utc)
    out=BASE/'AUDITS/SOURCES_OFFICIELLES'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for _,r in d.iterrows():
        row={c:r[c] for c in COLS};row.update({'Date_collecte_UTC':now.isoformat(),'Notes_attribuees':0})
        try:
            pub=pd.to_datetime(r.Date_publication,utc=True,errors='coerce')
            if pd.isna(pub) or pub>pd.Timestamp(now):raise ValueError('Date publication absente/future')
            if r.Type_source not in ['PUBLICATION_EMETTEUR','DEPOT_REGLEMENTAIRE']:raise ValueError('Source non primaire')
            domaines=set(r.Domaine_autorise.split('|'))
            verifier_url(r.Source_URL,domaines)
            if not r.Source_habilitation_domaine.startswith('https://'):raise ValueError('Habilitation domaine absente')
            req=Request(r.Source_URL,headers={'User-Agent':'MICRO_CAPS_DASHBOARD document research','Accept-Encoding':'identity'})
            with build_opener(Redirections(domaines)).open(req,timeout=30) as response:
                final=response.geturl();verifier_url(final,domaines)
                data=response.read(30_000_001)
                if len(data)>30_000_000 or not data:raise ValueError('Taille document invalide')
                content_type=response.headers.get('Content-Type','')
            digest=hashlib.sha256(data).hexdigest();f=out/(digest+'.bin');f.write_bytes(data)
            row.update({'Statut':'DOCUMENT_COLLECTE_A_VERIFIER','SHA256':digest,
                        'Fichier_brut':str(f.relative_to(BASE)),'URL_finale':final,'Type_contenu':content_type})
        except Exception as exc:row.update({'Statut':'BLOQUE_SOURCE','Motif':type(exc).__name__+': '+str(exc)})
        rows.append(row)
    pd.DataFrame(rows,columns=COLS+['Date_collecte_UTC','Notes_attribuees','Statut','SHA256','Fichier_brut','URL_finale','Type_contenu','Motif']).to_csv(out/'AUDIT_DOCUMENTS.csv',index=False)
    non_us=pd.read_csv(BASE/'DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv',dtype=str,keep_default_na=False)
    couverture=non_us[['Ticker','Societe','Pays']].copy()
    couverture['Document_configure']=couverture.Ticker.isin(d.Ticker).map({True:'OUI',False:'NON'})
    couverture['Statut']='SOURCES_OFFICIELLES_ET_IDENTITE_A_COMPLETER'
    couverture.to_csv(out/'COUVERTURE.csv',index=False)
    manifest={'date_utc':now.isoformat(),'documents_configures':len(d),'documents_collectes':sum(r['Statut']=='DOCUMENT_COLLECTE_A_VERIFIER' for r in rows),
              'sources_bloquees':sum(r['Statut']=='BLOQUE_SOURCE' for r in rows),'dossiers_sans_document_configure':int(couverture.Document_configure.eq('NON').sum()),
              'notes_attribuees':0,'couverture_complete':False}
    (out/'MANIFESTE.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False));return rows
if __name__=='__main__':executer()

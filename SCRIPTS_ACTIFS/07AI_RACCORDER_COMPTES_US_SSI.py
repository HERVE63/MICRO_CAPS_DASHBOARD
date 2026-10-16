"""Raccorde les archives SEC du recensement US aux moteurs 07U/07V/07W.

Hors réseau, sorties isolées par exécution. Aucune note ni validation humaine
n'est déduite de la disponibilité des comptes. Les données fournisseur restent
chiffrées ; seuls les faits provenant directement de la SEC sont extraits.
"""
from pathlib import Path
from datetime import datetime, timezone
from contextlib import redirect_stdout
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import csv, gzip, hashlib, importlib.util, io, json, os
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

def charger(nom):
    spec = importlib.util.spec_from_file_location(nom[:-3], BASE/'SCRIPTS_ACTIFS'/nom)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def verifier_fichier(source, manifeste, nom):
    if Path(nom).name != nom:
        raise RuntimeError('CHEMIN_ARCHIVE_INVALIDE')
    p = source/nom
    if manifeste.get('fichiers', {}).get(nom) != hashlib.sha256(p.read_bytes()).hexdigest():
        raise RuntimeError('EMPREINTE_SOURCE_INCOHERENTE:'+nom)
    return p

def lire_archive_sec(source, manifeste, entree, cle, dechiffrer):
    url = entree.get('route', '')
    if not url.startswith('SEC:https://data.sec.gov/api/xbrl/companyfacts/CIK'):
        raise RuntimeError('ARCHIVE_NON_COMPANYFACTS_SEC')
    p = verifier_fichier(source, manifeste, entree['archive_chiffree'])
    return json.loads(dechiffrer(json.loads(p.read_text()), cle))

def raccorder_emetteur(rows, obj, url, date_collecte, asof, dossier):
    """Réutilise les trois modules existants sans leurs chemins de production."""
    u = charger('07U_COLLECTE_COMPANYFACTS_SEC.py')
    v = charger('07V_NORMALISER_FAITS_SEC.py')
    w = charger('07W_RAPPROCHER_PREUVES_SEC_SSI.py')
    identites = pd.DataFrame([{'Ticker':r['Ticker_US'], 'CIK':r['CIK'],
        'Statut_SEC':'A_VERIFIER_IDENTITE_ET_CONTENU', 'CIK_verifie':'NON'} for r in rows])
    identites.to_csv(dossier/'IDENTITES.csv', index=False)
    pd.DataFrame([{'Ticker':r['Ticker_US'], 'Societe':r.get('Nom_SEC','')} for r in rows]).to_csv(dossier/'DOSSIERS.csv', index=False)
    u.SRC=dossier/'IDENTITES.csv'; u.OUT=dossier/'BRUTS.csv'; u.AUD=dossier/'AUDIT_BRUTS.csv'
    def lire(s, agent):
        if s != url: raise RuntimeError('URL_COMPANYFACTS_INCOHERENTE')
        return obj
    u.lire_json=lire; u.time=SimpleNamespace(sleep=lambda _:None); u.DATES_SOURCES={url:date_collecte}
    v.SRC=u.OUT; v.OUT=dossier/'COMPARABLES.csv'; v.AUD=dossier/'AUDIT_COMPARABLES.csv'
    w.DOS=dossier/'DOSSIERS.csv'; w.SEC=u.SRC; w.FACT=v.OUT
    w.OUT=dossier/'RAPPROCHEMENT.csv'; w.AUD=dossier/'AUDIT_RAPPROCHEMENT.csv'
    ancien = {k:os.environ.get(k) for k in ('SEC_USER_AGENT','MICRO_CAPS_AS_OF')}
    try:
        # 07U ne fait aucun appel réseau : lire_json est remplacé par l'archive vérifiée.
        os.environ['SEC_USER_AGENT']='Archive SEC hors reseau archives@example.invalid'
        os.environ['MICRO_CAPS_AS_OF']=asof
        with redirect_stdout(io.StringIO()):
            u.executer(); v.executer(); w.executer()
    finally:
        for k,val in ancien.items():
            if val is None: os.environ.pop(k,None)
            else: os.environ[k]=val
    return {nom:pd.read_csv(dossier/(nom+'.csv'),dtype=str,keep_default_na=False)
            for nom in ('BRUTS','COMPARABLES','RAPPROCHEMENT')}

def executer(source=None):
    eod=charger('07AH_RECENSER_MICROCAPS_US_EODHD.py')
    if source is None:
        pistes=sorted((BASE/'AUDITS/RECENSEMENT_US_EODHD').glob('*/MANIFESTE.json'))
        if not pistes: raise RuntimeError('RECENSEMENT_US_ABSENT')
        source=pistes[-1].parent
    source=Path(source); manifeste=json.loads((source/'MANIFESTE.json').read_text())
    if not manifeste.get('recensement_termine'): raise RuntimeError('DERNIER_RECENSEMENT_INCOMPLET')
    cle=os.getenv('EODHD_API_KEY','').strip()
    if not cle: raise RuntimeError('CLE_ARCHIVES_ABSENTE')
    index=json.loads(verifier_fichier(source,manifeste,'INDEX_REQUETES.json').read_text())
    archives={r['route'][4:]:r for r in index if r.get('route','').startswith('SEC:https://data.sec.gov/api/xbrl/companyfacts/CIK')}
    candidats=list(csv.DictReader(verifier_fichier(source,manifeste,'COUVERTURE_PREUVES_SEC.csv').open()))
    if len({r['Ticker_US'] for r in candidats}) != len(candidats): raise RuntimeError('DOUBLONS_TICKER_US')
    asof=min(os.getenv('MICRO_CAPS_AS_OF',manifeste['date_utc'][:10]),manifeste['date_utc'][:10])
    datetime.strptime(asof,'%Y-%m-%d')
    out=BASE/'AUDITS/QUALIFICATION_US'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True,exist_ok=False)
    groupes={}
    for r in candidats:
        if r.get('Statut_companyfacts') in ('FAITS_BRUTS_A_VERIFIER','AUCUN_FAIT_RETENU'): groupes.setdefault(r['CIK'],[]).append(r)
    couverture=[]; totaux={k:0 for k in ('BRUTS','COMPARABLES','RAPPROCHEMENT')}; premieres=set()
    for cik,rows in groupes.items():
        url='https://data.sec.gov/api/xbrl/companyfacts/CIK'+cik+'.json'
        if url not in archives: raise RuntimeError('ARCHIVE_FINANCIERE_ABSENTE:'+cik)
        entree=archives[url]; obj=lire_archive_sec(source,manifeste,entree,cle,eod.dechiffrer)
        if str(obj.get('cik','')).zfill(10)!=cik: raise RuntimeError('CIK_ARCHIVE_INCOHERENT')
        with TemporaryDirectory() as tmp:
            tables=raccorder_emetteur(rows,obj,url,entree['date_collecte_utc'],asof,Path(tmp))
        for nom,table in tables.items():
            with gzip.open(out/(nom+'.csv.gz'),'at',encoding='utf-8',newline='') as f:
                table.to_csv(f,index=False,header=nom not in premieres)
            premieres.add(nom); totaux[nom]+=len(table)
        for r in rows:
            comp=tables['COMPARABLES']; comp=comp[comp['Ticker']==r['Ticker_US']]
            rapproche=tables['RAPPROCHEMENT']; rapproche=rapproche[rapproche['Ticker']==r['Ticker_US']]
            couverture.append(dict(r,Faits_comparables=len(comp),
                Concepts_comparables=';'.join(sorted(set(comp['Concept']))),
                Blocs_avec_pistes=';'.join(sorted(set(rapproche['Bloc_SSI_cible']))),
                Dernier_depot_comparable=max(comp['Date_depot'],default=''),
                Statut_qualification='IDENTITE_CONTENU_PERIODES_ET_BLOCS_A_VERIFIER',
                SSI_evaluable_valide='NON',Note_SSI='',Admission_SSI='NON'))
        if len(couverture)%100==0: print('Raccordement SEC :',len(couverture),'cotations traitées',flush=True)
    traites={r['Ticker_US'] for r in couverture}
    couverture.extend(dict(r,Faits_comparables=0,Concepts_comparables='',Blocs_avec_pistes='',
        Dernier_depot_comparable='',Statut_qualification='DONNEES_OU_IDENTITE_A_COMPLETER',
        SSI_evaluable_valide='NON',Note_SSI='',Admission_SSI='NON') for r in candidats if r['Ticker_US'] not in traites)
    pd.DataFrame(couverture).to_csv(out/'COUVERTURE_QUALIFICATION_US.csv',index=False)
    bilan={'date_utc':datetime.now(timezone.utc).isoformat(),'date_limite_information':asof,
        'source_recensement':str(source.relative_to(BASE)),
        'SHA256_manifeste_source':hashlib.sha256((source/'MANIFESTE.json').read_bytes()).hexdigest(),
        'source_script_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'modules_SHA256':{nom:hashlib.sha256((BASE/'SCRIPTS_ACTIFS'/nom).read_bytes()).hexdigest() for nom in
            ('07U_COLLECTE_COMPANYFACTS_SEC.py','07V_NORMALISER_FAITS_SEC.py','07W_RAPPROCHER_PREUVES_SEC_SSI.py')},
        'cotations_recensees':len(candidats),'emetteurs_comptes_traites':len(groupes),
        'cotations_avec_faits_comparables':sum(int(r['Faits_comparables'])>0 for r in couverture),
        'volumes':totaux,'SSI_evaluables_valides':0,'admissions_SSI':0,'notes_SSI_attribuees':0,
        'selection_finale_autorisee':False,'appels_reseau':0,
        'statut':'RACCORDEMENT_07U_07V_07W_EXECUTE_PREUVES_NON_VALIDEES',
        'manques':'Identité à confirmer ; B4, gouvernance B5, qualité B6 et liquidité B7 restent à documenter ; B1/B2/B3 à vérifier.',
        'fichiers':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}}
    (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(bilan,ensure_ascii=False));return bilan

if __name__=='__main__': executer()

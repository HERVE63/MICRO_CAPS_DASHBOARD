"""Bilan réel du pipeline, classement et confrontation sans note imputée.
Les Top20/Top5 sont publiés uniquement après SSI et revue MCPA/IPS validés.
Ce module n'écrit jamais une opération ni les positions.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, math, subprocess
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
D=BASE/'DONNEES'
def charger(nom):
    spec=importlib.util.spec_from_file_location(nom[:-3],BASE/'SCRIPTS_ACTIFS'/nom)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def executer():
    out=BASE/'AUDITS/SELECTION'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True,exist_ok=False)
    dossiers=pd.read_csv(D/'DOSSIERS_SSI_A_QUALIFIER.csv',dtype=str,keep_default_na=False)
    ssi=charger('07R_VALIDER_NOTES_SSI.py')
    # Sorties isolées : ne pas écraser le registre d'admission opérationnel pendant un audit.
    ssi.OUT=out/'RESULTATS_SSI.csv';ssi.AUD=out/'AUDIT_SSI.csv'
    resultats=ssi.executer();admis=resultats[resultats.Statut_SSI.eq('ADMIS_SSI')]
    cohorte=pd.read_csv(D/'COHORTE_MICRO_CAPS_T0.csv')
    gele=pd.read_csv(BASE/'SAUVEGARDES/MICRO_CAPS_T0_GELE_2026-10-01.csv')
    initial=pd.read_csv(D/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv')
    t0_ok=(cohorte.equals(gele) and len(cohorte)==40 and cohorte.ID_ligne.nunique()==40
        and cohorte.Date_T0.eq('2026-10-01').all() and cohorte.Capital_T0_EUR.eq(100).all()
        and abs(cohorte.Valeur_T0_Temoin_EUR.sum()-4000)<1e-8
        and abs(cohorte.Valeur_T0_Gere_EUR.sum()-4000)<1e-8)
    initial_ok=(len(initial)==40 and initial.ID_position.nunique()==40
        and abs(initial.Capital_initial_EUR.sum()-4000)<1e-8)
    params=pd.read_csv(BASE/'CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv').set_index('Parametre')
    achat=float(params.loc['Frais_achat','Valeur'])/100;vente=float(params.loc['Frais_vente','Valeur'])/100
    frais_ok=achat==.025 and vente==.025
    journal=pd.read_csv(D/'JOURNAL_ARBITRAGES_GERE.csv',keep_default_na=False)
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'COHORTE_MICRO_CAPS_T0.csv',
        BASE/'SAUVEGARDES/MICRO_CAPS_T0_GELE_2026-10-01.csv',D/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv',D/'JOURNAL_ARBITRAGES_GERE.csv']}
    blocages=[]
    if not t0_ok:blocages.append('INTEGRITE_T0_INVALIDE')
    if not initial_ok:blocages.append('ETAT_INITIAL_INVALIDE')
    if not frais_ok:blocages.append('FRAIS_DIVERGENTS')
    if not len(admis):blocages.append('AUCUN_DOSSIER_ADMIS_SSI_SUR_PREUVES_VERIFIEES')
    revue=pd.read_csv(D/'REVUE_HEBDOMADAIRE_MCPA_IPS.csv',dtype=str,keep_default_na=False)
    classement=pd.DataFrame(columns=['Ticker','Societe','SSI','MCPA','IC','CX','Delta','WWWS','Role_IPS','Decision','Rang'])
    if revue.empty:blocages.append('REVUE_MCPA_IPS_ABSENTE_OU_VIDE')
    else:
        try:
            gate=charger('09_CONTROLE_REVUE_MCPA_IPS.py');gate.SORTIE=out/'CONTROLE_REVUE.csv';r=gate.executer()
            chasse=charger('08B_CONTROLE_CHASSE_SSI.py');chasse.OUTPUT=out/'CONTROLE_CHASSE.csv';chasse.RESULTATS=ssi.OUT;chasse.executer()
            candidates=r[r.Type.eq('CHALLENGER') & r.Ticker.isin(admis.Ticker) & pd.to_numeric(r.MCPA).ge(80)].copy()
            # Les ex aequo restent signalés ; ordre ticker seulement pour affichage stable.
            candidates=candidates.sort_values(['MCPA','Ticker'],ascending=[False,True])
            candidates['Rang']=pd.to_numeric(candidates.MCPA).rank(method='min',ascending=False).astype(int)
            classement=candidates[[c for c in classement.columns if c in candidates]]
        except Exception as exc:blocages.append('CONTROLE_COMITE_BLOQUE: '+str(exc))
    for n,k in [('CLASSEMENT_CHALLENGERS.csv',None),('TOP20.csv',20),('TOP5.csv',5)]:
        (classement if k is None else classement[classement.Rang.le(k)]).to_csv(out/n,index=False)
    rows=[]
    for _,r in cohorte.iterrows():
        rows.append({'ID_ligne':r.ID_ligne,'Ticker_titulaire':r.Ticker_cotation,
                     'Societe_titulaire':r.Societe,'Nb_challengers_valides':len(classement),
                     'Statut':'BLOQUE_ANALYSE_TITULAIRE_ET_DUEL_REQUIS' if len(classement) else 'AUCUN_CHALLENGER_VALIDE',
                     'Decision_arbitrage':'NON_PRODUITE'})
    pd.DataFrame(rows).to_csv(out/'CONFRONTATION_40_TITULAIRES.csv',index=False)
    couverture=[]
    for pays,g in dossiers.groupby('Pays'):
        couverture.append({'Pays_cotation':pays,'Dossiers':len(g),'Notes_B1_presentes':int(g.Note_B1.ne('MANQUANTE').sum())})
    pd.DataFrame(couverture).to_csv(out/'COUVERTURE_QUALIFICATION.csv',index=False)
    # Rechercher les pièces réellement exécutées (pas seulement les workflows présents).
    sec=[]
    for p in sorted((BASE/'AUDITS/SEC').glob('RUN_*/MANIFESTE.json')):
        m=json.loads(p.read_text());sec.append({'fichier':str(p.relative_to(BASE)),'statut':m['statut'],
            'secret_contact_valide':m.get('secret_contact_valide'),'etapes_executees':len(m.get('etapes',[]))})
    if not any(x['etapes_executees']==6 for x in sec):blocages.append('ENRICHISSEMENT_SEC_NON_ACHEVE')
    # Un moteur SCE indépendant ne se déduit pas d'un score SSI.
    discovery=[p.name for p in (BASE/'SCRIPTS_ACTIFS').glob('*.py') if 'DISCOVERY' in p.name.upper()]
    if not discovery:blocages.append('MOTEUR_SCE_DISCOVERY_EXECUTABLE_NON_PRESENT')
    manifest={'date_utc':datetime.now(timezone.utc).isoformat(),
       'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),
       'dossiers':len(dossiers),'admis_SSI':len(admis),'challengers_MCPA_valides':len(classement),
       'selection_finale_validee':False,'blocages':blocages,'integrite_T0':'OK' if t0_ok else 'ECHEC',
       'etat_initial':'OK' if initial_ok else 'ECHEC','frais_achat':achat,'frais_vente':vente,
       'capital_reinvesti_apres_rotation_100_EUR':100*(1-vente)/(1+achat),
       'perte_rotation_pct':100*(1-(1-vente)/(1+achat)),
       'journal_operations':len(journal),'empreintes_protegees':files,'executions_SEC':sec,
       'remarque_couverture':'Pays est la zone de cotation ; ce champ ne prouve pas le pays de l’émetteur.'}
    (out/'BILAN.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ['empreintes_protegees','executions_SEC']},ensure_ascii=False,indent=2))
    return manifest
if __name__=='__main__':executer()

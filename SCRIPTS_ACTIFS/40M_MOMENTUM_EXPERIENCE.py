#!/usr/bin/env python3
"""Momentum 1/2/3 mois depuis lectures individuelles Zonebourse.
Le moteur ne consulte pas le web. Il exige les preuves du navigateur du passage,
calcule sur les lignes historiques datées et prépare une revue, sans journaliser.
"""
import argparse,calendar,csv,hashlib,json,math,re
from pathlib import Path
from datetime import date,datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import pandas_market_calendars as mcal
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'DONNEES'
HORIZONS=('1m','2m','3m')
MIN_VALIDATED=35

def arbitrage_scope(rows):
    eligible=[r for r in rows if r.get('Statut')=='CALCULABLE_ZONEBOURSE_VERIFIE' and r.get('Controle_marche')!='SUSPENDU']
    cohort_ok=len(rows)==40 and len({r.get('Ticker') for r in rows})==40
    return eligible,cohort_ok and len(eligible)>=MIN_VALIDATED
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def numeric(v):
    n=float(re.sub(r'[\s\u202f\u00a0]','',str(v)).replace(',','.').replace('%','').replace('−','-'))
    if not math.isfinite(n):raise ValueError('Nombre non fini')
    return n
def calendar_code(t):
    return next((v for k,v in {'.PA':'XPAR','.L':'XLON','.MI':'XMIL','.ST':'XSTO','.TO':'XTSE','.V':'XTSE'}.items() if t.endswith(k)),'NYSE')
def sessions(t,start,end):return [d.date() for d in mcal.get_calendar(calendar_code(t)).valid_days(start_date=start,end_date=end)]
def latest_closed(t,asof):
    s=mcal.get_calendar(calendar_code(t)).schedule(start_date=asof.date()-timedelta(days=15),end_date=asof.date())
    done=s[s.market_close<=asof]
    if done.empty:raise ValueError('Calendrier sans séance terminée')
    return done.index[-1].date()
def reference_close(t,asof):
    # Veille de la date de contrôle à Paris ; calendrier propre à chaque place.
    day=asof.astimezone(ZoneInfo('Europe/Paris')).date()
    return sessions(t,day-timedelta(days=20),day-timedelta(days=1))[-1]
def months_before(d,n):
    y,m=divmod(d.year*12+d.month-1-n,12);m+=1
    return date(y,m,min(d.day,calendar.monthrange(y,m)[1]))
def market_block(controls,ticker,asof):
    day=asof.astimezone(ZoneInfo('Europe/Paris')).date().isoformat()
    for item in controls:
        if item['ticker']==ticker and item['statut']=='SUSPENDU' and item['debut']<=day and (not item.get('date_reprise') or day<item['date_reprise']):
            return item
    return None
def parse_history(record):
    rows={}
    for page in record.get('history',[]):
        for line in page.get('text','').splitlines():
            cols=line.split('\t')
            if len(cols)<7 or not re.fullmatch(r'\d{2}/\d{2}/\d{4}',cols[0]):continue
            d=datetime.strptime(cols[0],'%d/%m/%Y').date();p=numeric(cols[4]);v=numeric(cols[5])
            if p<=0 or v<0 or int(v)!=v:raise ValueError('Cours/volume invalide')
            row={'date':d,'close':p,'volume':int(v),'variation_publiee':numeric(cols[6])}
            if d in rows and rows[d]!=row:raise ValueError('Historique contradictoire '+str(d))
            rows[d]=row
    return rows

def signal(last,five,month):
    if None in (last,five,month):return 'DONNEES_INSUFFISANTES'
    if last<0 and five<0 and month>0:return 'ALERTE_RETOURNEMENT_BAISSIER'
    if last>0 and five>0 and month<0:return 'ALERTE_REPRISE_HAUSSIERE'
    if last<0 and five>0:return 'DECELERATION_A_SURVEILLER'
    if last>0 and five<0:return 'REBOND_A_CONFIRMER'
    return 'DIRECTION_HAUSSIERE' if last>0 else 'DIRECTION_BAISSIERE' if last<0 else 'STABLE'

def calculate(record,ticker,asof):
    if record.get('ticker')!=ticker or record.get('method')!='LECTURE_INDIVIDUELLE_NAVIGATEUR':raise ValueError('Preuve de lecture/identité absente')
    if not record.get('url','').startswith('https://www.zonebourse.com/cours/action/'):raise ValueError('Source différente de Zonebourse')
    captured=datetime.fromisoformat(record['consulted_at'].replace('Z','+00:00'))
    if captured>asof:raise ValueError('Consultation future')
    body=record['body']
    page_ticker=ticker.split('.')[0]
    if ticker=='GROW.MI':
        # Même ISIN que le dossier historique ; Zonebourse publie le symbole MAIL.
        if '\nMAIL\n' in body and '\nIT0005040354\n' in body:page_ticker='MAIL'
    if ticker=='PULS.L':
        # Zonebourse conserve ACC ; rapprochement par l'ISIN de la cohorte.
        # Ceci ne lève pas le contrôle distinct de suspension.
        if '\nACC\n' in body and '\nGB00BGQVB052\n' in body:page_ticker='ACC'
    if '\n'+page_ticker+'\n' not in body:raise ValueError('Ticker de page divergent')
    match=re.search(r'(Marché Fermé|Cours en clôture|Temps réel|Cours en différé|Temps Différé)[^\n]*?(?:(\d\d:\d\d:\d\d) )?(\d\d/\d\d/\d{4})[^\n]*\n([\d\s,\.]+) (USD|CAD|EUR|GBp|GBX|GBP|SEK)\t',body)
    if not match:raise ValueError('Date, heure et unité de cotation non identifiées')
    market_state,clock,quote_date,price,unit=match.groups();qd=datetime.strptime(quote_date,'%d/%m/%Y').date();price=numeric(price)
    if price<=0:raise ValueError('Cours non positif')
    quote_type='CLOTURE' if market_state in ('Marché Fermé','Cours en clôture') else 'INTRADAY'
    history=parse_history(record)
    if any(d>qd for d in history):raise ValueError('Ligne historique postérieure à la cotation')
    if quote_type=='CLOTURE' and qd in history and abs(history[qd]['close']-price)>max(.00001,price*.00001):raise ValueError('Clôture d’en-tête et tableau divergents')
    expected=reference_close(ticker,asof)
    # Seules des lignes historiques de clôture sont utilisées, jamais le prix en séance.
    available=[d for d in history if d<=expected]
    if not available:raise ValueError('Aucune clôture historique disponible avant la séance cible '+str(expected))
    selected=max(available)
    market=mcal.get_calendar(calendar_code(ticker))
    closed_at=market.schedule(start_date=selected,end_date=selected).iloc[0].market_close.to_pydatetime()
    if captured<closed_at:raise ValueError('Lecture antérieure à la clôture historique retenue')
    header_qd=qd;header_clock=clock;header_type=quote_type
    qd=selected;price=history[qd]['close'];quote_type='CLOTURE'
    clock=header_clock if header_qd==qd and header_type=='CLOTURE' else None
    fresh=qd==expected
    ds=sessions(ticker,qd-timedelta(days=30),qd)
    result={'Date_historique':qd.isoformat(),'Date_cloture_attendue':expected.isoformat(),'Heure_cotation_source':clock,'Heure_cloture_calendrier_UTC':closed_at.isoformat(),'Nature_cotation':quote_type,'Cours_source':price,'Unite_source':unit,'Cours_devise':price/100 if unit in ('GBp','GBX') else price,'Devise':'GBP' if unit in ('GBp','GBX') else unit,'Volume_derniere_seance':history[qd]['volume'],'Date_volume_derniere_seance':qd.isoformat(),'Date_consultation_UTC':record['consulted_at'],'Source':record['url'],'Date_cotation_entete_non_utilisee':header_qd.isoformat()}
    anchors={};missing=[]
    if not fresh:missing.append('clôture attendue '+str(expected)+' absente ; dernière disponible '+str(qd))
    for label,days in [('derniere_seance',1),('5_seances',5)]:
        baseline=ds[-1-days];r=history.get(baseline);anchors[label]=r
        result['Variation_'+label+'_pct']=100*(price/r['close']-1) if r else None
        if not r:missing.append('clôture '+str(baseline))
    for n in (1,2,3):
        target=months_before(qd,n);sd=sessions(ticker,target-timedelta(days=14),target)[-1];r=history.get(sd);anchors[str(n)+'m']=r
        result['Momentum_'+str(n)+'m_pct']=100*(price/r['close']-1) if r else None
        if not r:missing.append('ancrage '+str(sd))
    volume=re.search(r'Volume moy\. 20 séances\n([\d\s,.]+)\nRatio',body)
    result['Volume_moyen_20j']=numeric(volume[1]) if volume else None
    last=result['Variation_derniere_seance_pct'];five=result['Variation_5_seances_pct']
    result['Acceleration_derniere_seance_pct_vs_moyenne_5j']=last-five/5 if last is not None and five is not None else None
    warnings=[]
    for label,key in [('1 jour','Variation_derniere_seance_pct'),('1 semaine','Variation_5_seances_pct'),('1 mois','Momentum_1m_pct'),('3 mois','Momentum_3m_pct')]:
        m=re.search(r'(?:^|\n)'+label+r'\t\s*([+−\-\d\s,.]+)%',body)
        if header_qd==qd and header_type=='CLOTURE' and m and result.get(key) is not None and abs(numeric(m[1])-result[key])>.06:warnings.append(label+': performance synthétique différente du calcul sur dates exactes')
    result['Statut']='HISTORIQUE_PERIME' if not fresh else 'INCOMPLET_SANS_SIGNAL' if missing else 'CALCULABLE_ZONEBOURSE_VERIFIE'
    result['Signal']=signal(last,five,result['Momentum_1m_pct']) if fresh and not missing else 'DONNEES_PERIMEES_SANS_ARBITRAGE' if not fresh else 'DONNEES_INSUFFISANTES'
    prior_day=ds[-2];prior=history.get(prior_day);prior_1=history.get(ds[-3]);prior_5=history.get(ds[-7]);target=months_before(prior_day,1);prior_month=history.get(sessions(ticker,target-timedelta(days=14),target)[-1])
    previous=signal(*[100*(prior['close']/p['close']-1) for p in (prior_1,prior_5,prior_month)]) if all(p is not None for p in (prior,prior_1,prior_5,prior_month)) else 'NON_CALCULABLE'
    result['Signal_seance_precedente']=previous
    result['Changement_direction']='NON_EVALUABLE' if not fresh or missing or previous=='NON_CALCULABLE' else 'OUI' if previous!=result['Signal'] else 'NON'
    result['Ancrages']=json.dumps({k:dict(v,date=str(v['date'])) if v else None for k,v in anchors.items()},ensure_ascii=False)
    result['Limites']=' | '.join(missing+warnings+['Clôtures publiées; convention d’ajustement aux opérations sur titres non explicitée par la page.'])
    return result

def write_csv(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)

def main(root=ROOT,asof=None,source=None):
    asof=asof or datetime.now(timezone.utc);data=root/'DONNEES';day=asof.astimezone(ZoneInfo('Europe/Paris')).date().isoformat()
    explicit_source=source is not None
    source=source or data/'ZONEBOURSE_NAVIGATEUR'/day
    directories=[source] if explicit_source else sorted((data/'ZONEBOURSE_NAVIGATEUR').glob('????-??-??'),reverse=True)
    directories=[p for p in directories if p.name<=day]
    holdings=read(data/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv')
    if len(holdings)!=40 or len({r['Ticker'] for r in holdings})!=40:raise ValueError('Cohorte 40 requise')
    journal=data/'JOURNAL_ARBITRAGES_GERE.csv';journal_hash=hashlib.sha256(journal.read_bytes()).hexdigest()
    manifest=json.loads((source/'MANIFESTE.json').read_text()) if (source/'MANIFESTE.json').exists() else {}
    controls_path=root/'CONFIG/CONTROLES_MARCHE_DOCUMENTES.json'
    controls=json.loads(controls_path.read_text()) if controls_path.exists() else []
    rows=[]
    for h in holdings:
        t=h['Ticker'];p=next((folder/(t+'.json') for folder in directories if (folder/(t+'.json')).exists()),source/(t+'.json'));r={'ID_position':h['ID_position'],'Ticker':t,'Societe':h['Societe'],'Date_execution':day,'Arbitrage_autorise':'NON','Rang_momentum':''}
        if not p.exists():r.update(Statut='NON_COLLECTE',Signal='AUCUN_SIGNAL_SANS_COLLECTE',Source='',Limites=manifest.get('statuts_par_ticker',{}).get(t,'Aucune lecture navigateur de ce passage'))
        else:
            try:
                r.update(calculate(json.loads(p.read_text()),t,asof));r['SHA256_preuve']=hashlib.sha256(p.read_bytes()).hexdigest()
                if r['Devise']!=h['Devise']:raise ValueError('Devise différente de la position')
            except (ValueError,KeyError,IndexError) as e:r.update(Statut='PREUVE_INEXPLOITABLE',Signal='AUCUN_SIGNAL_SANS_PREUVE',Limites=str(e))
        blocked=market_block(controls,t,asof)
        if blocked:
            r.update(Controle_marche='SUSPENDU',Sources_controle_marche=' | '.join(blocked['sources']),Signal='MARCHE_SUSPENDU_SANS_ARBITRAGE',Changement_direction='NON_EVALUABLE')
            if r['Statut']=='CALCULABLE_ZONEBOURSE_VERIFIE':r['Statut']='COTATION_NON_NEGOCIABLE'
            r['Limites']=r.get('Limites','')+' | '+blocked['motif']
        rows.append(r)
    verified,review_allowed=arbitrage_scope(rows)
    for r in rows:r['Arbitrage_autorise']='OUI' if review_allowed and r in verified else 'NON'
    # Priorité au mouvement de la dernière cotation; 5 séances puis M1/M2/M3 départagent.
    for i,r in enumerate(sorted(verified,key=lambda r:tuple(r[k] for k in ['Variation_derniere_seance_pct','Variation_5_seances_pct','Momentum_1m_pct','Momentum_2m_pct','Momentum_3m_pct']),reverse=True),1):r['Rang_momentum']=i
    write_csv(data/'EXPERIENCE_MOMENTUM_40.csv',rows)
    report={'date_execution':day,'asof_utc':asof.isoformat(),'titulaires':40,'lectures_exploitables':len(verified),'lignes_sans_cotation_actualisee':40-len(verified),'statut':'PRET_POUR_REVUE_HEBDOMADAIRE' if review_allowed else 'SEUIL_35_NON_ATTEINT','regle_cloture':'Dernière séance strictement antérieure au jour du contrôle (Europe/Paris), calendrier de chaque marché','source_requise':'Zonebourse, consultation individuelle navigateur','source_dossier':str(source.relative_to(root)),'frais_vente_pct':2.5,'frais_achat_pct':2.5,'friction_vente_achat_pct':(1-.975/1.025)*100,'journal_sha256':journal_hash,'transactions':0,'arbitrage_automatique':'DESACTIVE','classement':'COMPLET_A_REVOIR' if len(verified)==40 else 'PERIMETRE_VALIDE_35_MINIMUM' if review_allowed else 'DIAGNOSTIC_PARTIEL','temoin':'40 positions T0 figées; aucune valorisation complète réétiquetée comme Zonebourse actuelle','blocage_collecte':manifest.get('blocage')}
    report.update(seuil_minimum_valides=MIN_VALIDATED,arbitrage_autorise=review_allowed,perimetre_arbitrable=[r['Ticker'] for r in verified] if review_allowed else [],lignes_exclues=[r['Ticker'] for r in rows if r not in verified],confrontation='COMPLETE' if len(verified)==40 else 'PARTIELLE_AUTORISEE' if review_allowed else 'BLOQUEE')
    report['suspensions_documentees']=[r['Ticker'] for r in rows if r.get('Controle_marche')=='SUSPENDU']
    (data/'ETAT_MOMENTUM_QUOTIDIEN.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    preparation=[{'Ticker':r['Ticker'],'Date_revue':day,'Signal':r['Signal'],'Statut_cotation':r['Statut'],'Preparation':'SUSPENSION_NE_PAS_ARBITRER' if r.get('Controle_marche')=='SUSPENDU' else 'ATTENDRE_PREUVES' if r not in verified else 'SEUIL_35_NON_ATTEINT' if not review_allowed else 'SURVEILLER_DECELERATION' if r['Signal']=='DECELERATION_A_SURVEILLER' else 'EXAMINER_REDUCTION' if 'BAISSIER' in r['Signal'] else 'EXAMINER_REPRISE' if 'HAUSSIER' in r['Signal'] else 'ATTENDRE_PREUVES' if r not in verified else 'CONSERVER_SOUS_REVUE','Arbitrage_autorise':r['Arbitrage_autorise'],'Confrontation_40':report['confrontation'],'Operation_virtuelle':'AUCUNE','Friction_rotation_pct':report['friction_vente_achat_pct']} for r in rows]
    write_csv(data/'PREPARATION_HEBDOMADAIRE_MOMENTUM_40.csv',preparation)
    if hashlib.sha256(journal.read_bytes()).hexdigest()!=journal_hash:raise RuntimeError('Journal modifié')
    print(json.dumps(report,ensure_ascii=False));return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--asof');ap.add_argument('--source',type=Path);args=ap.parse_args()
    main(asof=datetime.fromisoformat(args.asof.replace('Z','+00:00')) if args.asof else None,source=args.source)

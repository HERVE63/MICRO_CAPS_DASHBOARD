"""Choix du réveil UTC été/hiver, indépendant du retard de GitHub Actions."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import json, os

ETE = '30 20 * * 1-5'
HIVER = '30 21 * * 1-5'

def decider(evenement, cron='', maintenant=None, mode='QUOTIDIEN'):
    maintenant = maintenant or datetime.now(timezone.utc)
    if maintenant.tzinfo is None: raise ValueError('DATE_SANS_FUSEAU')
    paris = maintenant.astimezone(ZoneInfo('Europe/Paris'))
    if mode=='QUOTIDIEN':ete,hiver=ETE,HIVER
    elif mode=='HEBDOMADAIRE':ete,hiver='15 20 * * 2','15 21 * * 2'
    else:raise ValueError('MODE_PLANIFICATION_INCONNU')
    attendu = ete if paris.utcoffset().total_seconds()==7200 else hiver
    if evenement in ('workflow_dispatch','push'):
        autorise=True; motif='REPRISE_EXPLICITE'
    elif evenement=='schedule' and cron in (ete,hiver):
        autorise=cron==attendu
        motif='REVEIL_SAISONNIER_RETARD_ACCEPTE' if autorise else 'AUTRE_REVEIL_SAISONNIER_IGNORE'
    else: raise ValueError('DECLENCHEUR_INCONNU')
    return {'run':autorise,'motif':motif,'evenement':evenement,'cron_recu':cron,
            'mode':mode,'cron_attendu':attendu,'heure_reelle_paris':paris.isoformat()}

if __name__=='__main__':
    r=decider(os.getenv('GITHUB_EVENT_NAME',''),os.getenv('MICRO_CAPS_CRON',''),
              mode=os.getenv('MICRO_CAPS_PLANIFICATION_MODE','QUOTIDIEN'))
    print(json.dumps(r,ensure_ascii=False))
    if os.getenv('GITHUB_OUTPUT'):
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as f:f.write('run='+str(r['run']).lower()+'\n')
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a') as f:
            f.write('Décision de planification : '+r['motif']+'\n\n'+json.dumps(r,ensure_ascii=False)+'\n')

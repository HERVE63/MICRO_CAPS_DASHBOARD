"""Choix du réveil UTC été/hiver, indépendant du retard de GitHub Actions."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import json, os

ETE = '30 20 * * 1-5'
HIVER = '30 21 * * 1-5'

def decider(evenement, cron='', maintenant=None):
    maintenant = maintenant or datetime.now(timezone.utc)
    if maintenant.tzinfo is None: raise ValueError('DATE_SANS_FUSEAU')
    paris = maintenant.astimezone(ZoneInfo('Europe/Paris'))
    attendu = ETE if paris.utcoffset().total_seconds()==7200 else HIVER
    if evenement in ('workflow_dispatch','push'):
        autorise=True; motif='REPRISE_EXPLICITE'
    elif evenement=='schedule' and cron in (ETE,HIVER):
        autorise=cron==attendu
        motif='REVEIL_SAISONNIER_RETARD_ACCEPTE' if autorise else 'AUTRE_REVEIL_SAISONNIER_IGNORE'
    else: raise ValueError('DECLENCHEUR_INCONNU')
    return {'run':autorise,'motif':motif,'evenement':evenement,'cron_recu':cron,
            'cron_attendu':attendu,'heure_reelle_paris':paris.isoformat()}

if __name__=='__main__':
    r=decider(os.getenv('GITHUB_EVENT_NAME',''),os.getenv('MICRO_CAPS_CRON',''))
    print(json.dumps(r,ensure_ascii=False))
    if os.getenv('GITHUB_OUTPUT'):
        with Path(os.environ['GITHUB_OUTPUT']).open('a') as f:f.write('run='+str(r['run']).lower()+'\n')
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a') as f:
            f.write('Décision de planification : '+r['motif']+'\n\n'+json.dumps(r,ensure_ascii=False)+'\n')

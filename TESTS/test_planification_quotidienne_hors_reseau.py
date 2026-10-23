"""Régressions des retards réellement observés et du changement d'heure."""
from pathlib import Path
from datetime import datetime
import importlib.util
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def charger(nom):
    s=importlib.util.spec_from_file_location(nom,ROOT/'SCRIPTS_ACTIFS'/nom)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test():
    m=charger('00A_PLANIFICATION_QUOTIDIENNE.py')
    for date,bon,mauvais in [('2026-10-15T23:12:38+00:00',m.ETE,m.HIVER),
                              ('2026-11-03T23:40:00+00:00',m.HIVER,m.ETE),
                              ('2026-10-23T21:42:00+00:00',m.ETE,m.HIVER),
                              ('2026-10-26T23:05:00+00:00',m.HIVER,m.ETE)]:
        d=datetime.fromisoformat(date)
        assert m.decider('schedule',bon,d)['run'] is True
        assert m.decider('schedule',mauvais,d)['run'] is False
    for event in ('workflow_dispatch','push'):
        assert m.decider(event,maintenant=datetime.fromisoformat('2026-10-16T13:00:00+00:00'))['run']
    try:m.decider('schedule','inconnu')
    except ValueError:pass
    else:raise AssertionError('Un réveil inconnu ne doit pas passer silencieusement')
    # Le mardi reste le déclencheur ; un retard après minuit ne supprime pas la chasse.
    for date,bon,mauvais in [('2026-10-21T00:30:00+00:00','15 20 * * 2','15 21 * * 2'),
                             ('2026-10-28T00:30:00+00:00','15 21 * * 2','15 20 * * 2')]:
        assert m.decider('schedule',bon,datetime.fromisoformat(date),mode='HEBDOMADAIRE')['run']
        assert not m.decider('schedule',mauvais,datetime.fromisoformat(date),mode='HEBDOMADAIRE')['run']
    # Le rendez-vous mensuel tolere un retard de demarrage GitHub Actions.
    for date,bon,mauvais in [('2026-09-29T21:58:00+00:00','45 21 * * 2','45 22 * * 2'),
                             ('2026-11-24T23:11:00+00:00','45 22 * * 2','45 21 * * 2')]:
        assert m.decider('schedule',bon,datetime.fromisoformat(date),mode='MENSUEL')['run']
        assert not m.decider('schedule',mauvais,datetime.fromisoformat(date),mode='MENSUEL')['run']
    try:m.decider('schedule',m.ETE,mode='HEBDOMADAIRE')
    except ValueError:pass
    else:raise AssertionError('Un cron quotidien ne doit pas activer la chasse hebdomadaire')
    b=charger('07B_AJOUT_HISTORIQUE.py')
    with patch.object(b.gate,'controler',return_value={'statut':'EN_ATTENTE','date_candidate':'2026-10-15','raisons':['preuve manquante']}):
        try:b.executer()
        except RuntimeError as e:assert 'JOURNEE_NON_ADMISSIBLE' in str(e)
        else:raise AssertionError('Une journée bloquée ne doit pas réussir en sortie de processus')
    with patch.object(b.gate,'controler',return_value={'statut':'DEJA_PRESENTE','date_candidate':'2026-10-15','raisons':[]}):
        assert b.executer() is False
    print('Planification : retards, été/hiver, reprise manuelle et arrêt des journées non admissibles OK')

if __name__=='__main__':test()

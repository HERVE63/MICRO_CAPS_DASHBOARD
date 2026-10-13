"""Verrou GitHub Actions sur l'heure PLANIFIEE, pas l'heure effective du runner.

GitHub Actions peut demarrer avec retard. La lecture de l'horloge du runner
a la minute exacte entrainait des succes de job dont toutes les etapes etaient
ignorees. Ce module identifie le bon reveil UTC selon l'heure de Paris.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os
import sys

CIBLES = {
    "quotidien": {"heure": "22:30", "jours": {1, 2, 3, 4, 5},
                  "crons": {"30 20 * * 1-5", "30 21 * * 1-5"}},
    "chasse": {"heure": "22:15", "jours": {2},
               "crons": {"15 20 * * 2", "15 21 * * 2"}},
    "arbitrage": {"heure": "23:45", "jours": {2},
                  "crons": {"45 21 * * 2", "45 22 * * 2"}},
}

def autoriser(mode, evenement, cron="", maintenant=None):
    if mode not in CIBLES:
        raise ValueError("Mode de production inconnu")
    if evenement in ("workflow_dispatch", "push"):
        return True, "DECLENCHEMENT_EXPLICITE"
    if evenement != "schedule":
        return False, "EVENEMENT_NON_AUTORISE"
    cible = CIBLES[mode]
    if cron not in cible["crons"]:
        return False, "CRON_INATTENDU"
    minute, heure, *_ = cron.split()
    maintenant = maintenant or datetime.now(timezone.utc)
    if maintenant.tzinfo is None:
        raise ValueError("Date sans fuseau interdite")
    maintenant = maintenant.astimezone(timezone.utc)
    # Reconstituer le reveil THEORIQUE le plus recent, meme si le runner
    # GitHub est demarre des heures apres le cron.
    dates = [maintenant.date() - timedelta(days=i) for i in range(3)]
    slots = [datetime(d.year, d.month, d.day, int(heure), int(minute),
                      tzinfo=timezone.utc) for d in dates]
    precedents = [s for s in slots if s <= maintenant]
    if not precedents:
        return False, "SLOT_FUTUR"
    slot = max(precedents)
    if maintenant - slot > timedelta(hours=12):
        return False, "REVEIL_TROP_ANCIEN"
    local = slot.astimezone(ZoneInfo("Europe/Paris"))
    if local.isoweekday() not in cible["jours"]:
        return False, "JOUR_INVALIDE"
    if local.strftime("%H:%M") != cible["heure"]:
        return False, "REVEIL_UTC_HORS_SAISON"
    return True, "CRENEAU_LOCAL_VALIDE_" + local.isoformat()

def executer():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    evenement = os.environ.get("GITHUB_EVENT_NAME", "")
    cron = os.environ.get("GITHUB_EVENT_SCHEDULE", "")
    oui, motif = autoriser(mode, evenement, cron)
    ligne = "run=" + ("true" if oui else "false")
    chemin = os.environ.get("GITHUB_OUTPUT", "")
    if not chemin:
        raise RuntimeError("GITHUB_OUTPUT absent")
    with open(chemin, "a", encoding="utf-8") as f:
        f.write(ligne + "\n")
    print(ligne, motif)

if __name__ == "__main__":
    executer()

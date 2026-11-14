# -*- coding: utf-8 -*-

"""
MICRO CAPS
03A_MOTEUR_CLOTURES_V3.py

Objectif :
Ne jamais utiliser une barre journalière encore intraday comme
une clôture officielle.

Principe :
Yahoo Finance fournit les prix.
pandas_market_calendars détermine si la séance correspondante
est réellement terminée.

Version : 02/10/2026
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

# Délai de sécurité après la clôture officielle
SAFETY_DELAY_MINUTES = 30
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location("marche_public",Path(__file__).with_name("marche_public.py"))
marche=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(marche)
import pandas_market_calendars as mcal


# ============================================================
# MAPPING TICKER -> CALENDRIER
# ============================================================

def marche_du_ticker(ticker):

    t = str(ticker).upper()

    if t.endswith(".PA"):
        return "Paris", "XPAR"

    if t.endswith(".L"):
        return "Londres", "XLON"

    if t.endswith(".MI"):
        return "Milan", "XMIL"

    if t.endswith(".ST"):
        return "Stockholm", "XSTO"

    if t.endswith(".TO") or t.endswith(".V"):
        return "Canada", "XTSE"

    return "USA", "NYSE"


# ============================================================
# DERNIÈRE SESSION TERMINÉE
# ============================================================

def derniere_session_terminee(ticker, maintenant_utc=None):

    if maintenant_utc is None:
        maintenant_utc = datetime.now(ZoneInfo("UTC"))

    elif maintenant_utc.tzinfo is None:
        maintenant_utc = maintenant_utc.replace(
            tzinfo=ZoneInfo("UTC")
        )

    nom_marche, code_cal = marche_du_ticker(ticker)

    cal = mcal.get_calendar(code_cal)

    debut = (maintenant_utc - timedelta(days=15)).date()
    fin = maintenant_utc.date()

    schedule = cal.schedule(
        start_date=debut,
        end_date=fin
    )

    if schedule.empty:
        raise RuntimeError(
            f"Aucune séance trouvée pour {ticker}"
        )

    terminees = schedule[
        schedule["market_close"] + pd.Timedelta(minutes=SAFETY_DELAY_MINUTES) <= maintenant_utc
    ]

    if terminees.empty:
        raise RuntimeError(
            f"Aucune séance terminée trouvée pour {ticker}"
        )

    date_session = terminees.index[-1].date()

    fermeture = terminees.iloc[-1]["market_close"]

    return {
        "marche": nom_marche,
        "calendrier": code_cal,
        "date_session": date_session,
        "fermeture_utc": fermeture
    }


# ============================================================
# PRIX DE LA DERNIÈRE SESSION TERMINÉE
# ============================================================

def derniere_cloture_validee(ticker, maintenant_utc=None, date_reference=None):
    session=derniere_session_terminee(ticker,maintenant_utc)
    target=min(session["date_session"],pd.Timestamp(date_reference).date()) if date_reference else session["date_session"]
    suspended=marche.suspension(ticker,target)
    quote=marche.cloture(ticker,suspended["derniere_cotation"] if suspended else target)
    quoted=pd.Timestamp(quote["date"]).date()
    status="SUSPENDU_DOCUMENTE" if suspended else ("OK" if quoted==target else "ATTENTE_NOUVELLE_COTATION")
    return {**session,"date_session":target,"ticker":ticker,"date_cotation":quoted,
      "jours_sans_cotation":(target-quoted).days,"cours_cloture":quote["cours"],
      "unite_normalisee":quote["devise"],"unite_source":quote["unite_source"],"preuve":quote["preuve"],
      "statut":status,"negociable":status=="OK","source_suspension":suspended["sources"] if suspended else []}

# ============================================================
# BENCHMARKS
# ============================================================

BENCHMARKS = {
    "^GSPC": ("S&P 500", "NYSE"),
    "^NDX": ("Nasdaq-100", "NYSE"),
    "^STOXX": ("STOXX Europe 600", "XPAR")
}


def derniere_cloture_benchmark(ticker,maintenant_utc=None,date_reference=None):
    if ticker not in BENCHMARKS:raise ValueError("Benchmark inconnu")
    nom,calendrier=BENCHMARKS[ticker]
    now=maintenant_utc or datetime.now(ZoneInfo("UTC"))
    if now.tzinfo is None:now=now.replace(tzinfo=ZoneInfo("UTC"))
    schedule=mcal.get_calendar(calendrier).schedule(start_date=(now-timedelta(days=15)).date(),end_date=now.date())
    ended=schedule[schedule["market_close"]+pd.Timedelta(minutes=SAFETY_DELAY_MINUTES)<=now]
    target=ended.index[-1].date()
    if date_reference:target=min(target,pd.Timestamp(date_reference).date())
    quote=marche.cloture(ticker,target)
    if quote["date"]!=str(target):raise RuntimeError("Benchmark périmé : "+ticker+" "+quote["date"])
    return {"benchmark":nom,"ticker":ticker,"date_session":target,"cours_cloture":quote["cours"],"devise":quote["devise"],"preuve":quote["preuve"],"statut":"OK"}

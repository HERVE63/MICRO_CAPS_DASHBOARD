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
import yfinance as yf
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

def derniere_cloture_validee(ticker, maintenant_utc=None):

    session = derniere_session_terminee(
        ticker,
        maintenant_utc
    )

    date_session = session["date_session"]

    # Fenêtre explicite autour de la séance recherchée.
    start = date_session - timedelta(days=15)
    end = date_session + timedelta(days=1)

    hist = yf.download(
        ticker,
        start=str(start),
        end=str(end),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False
    )

    if hist.empty:
        raise RuntimeError(
            f"Yahoo : aucune barre pour {ticker} "
            f"le {date_session}"
        )

    # yfinance peut retourner des colonnes MultiIndex.
    if isinstance(hist.columns, pd.MultiIndex):
        close_series = hist["Close"][ticker]
    else:
        close_series = hist["Close"]

    close_series = close_series.dropna()

    if close_series.empty:
        raise RuntimeError(
            f"Close manquant pour {ticker} "
            f"le {date_session}"
        )
    date_cotation = pd.Timestamp(close_series.index[-1]).date()
    close = float(close_series.iloc[-1])
    statut_cotation = "OK" if date_cotation == date_session else "ATTENTE_NOUVELLE_COTATION"
    jours_sans_cotation = (date_session - date_cotation).days
    # Yahoo : Londres est généralement fourni en GBp.
    unite = "devise"

    if str(ticker).upper().endswith(".L"):
        close = close / 100.0
        unite = "GBP"

    return {
        **session,
        "ticker": ticker,
        "date_cotation": date_cotation,
        "jours_sans_cotation": jours_sans_cotation,
        "cours_cloture": close,
        "unite_normalisee": unite,
        "statut": statut_cotation
    }


# ============================================================
# BENCHMARKS
# ============================================================

BENCHMARKS = {
    "^GSPC": ("S&P 500", "NYSE"),
    "^NDX": ("Nasdaq-100", "NYSE"),
    "^STOXX": ("STOXX Europe 600", "XPAR")
}


def derniere_cloture_benchmark(
    ticker,
    maintenant_utc=None
):

    if ticker not in BENCHMARKS:
        raise ValueError(
            f"Benchmark non défini : {ticker}"
        )

    nom, calendrier = BENCHMARKS[ticker]

    if maintenant_utc is None:
        maintenant_utc = datetime.now(
            ZoneInfo("UTC")
        )

    elif maintenant_utc.tzinfo is None:
        maintenant_utc = maintenant_utc.replace(
            tzinfo=ZoneInfo("UTC")
        )

    cal = mcal.get_calendar(calendrier)

    debut = (
        maintenant_utc - timedelta(days=15)
    ).date()

    fin = maintenant_utc.date()

    schedule = cal.schedule(
        start_date=debut,
        end_date=fin
    )

    terminees = schedule[
        schedule["market_close"] + pd.Timedelta(minutes=SAFETY_DELAY_MINUTES) <= maintenant_utc
    ]

    if terminees.empty:
        raise RuntimeError(
            f"Aucune séance terminée pour {nom}"
        )

    date_session = terminees.index[-1].date()

    hist = yf.download(
        ticker,
        start=str(date_session),
        end=str(date_session + timedelta(days=1)),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False
    )

    if hist.empty:
        raise RuntimeError(
            f"Aucune donnée Yahoo pour {nom}"
        )

    if isinstance(hist.columns, pd.MultiIndex):
        close_series = hist["Close"][ticker]
    else:
        close_series = hist["Close"]

    close_series = close_series.dropna()

    if close_series.empty:
        raise RuntimeError(
            f"Close manquant pour {nom}"
        )

    return {
        "benchmark": nom,
        "ticker": ticker,
        "date_session": date_session,
        "cours_cloture": float(
            close_series.iloc[-1]
        ),
        "statut": "OK"
    }


# ============================================================
# FIN
# ============================================================

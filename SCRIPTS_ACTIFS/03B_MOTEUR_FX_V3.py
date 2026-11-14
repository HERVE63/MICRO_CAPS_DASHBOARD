# -*- coding: utf-8 -*-

"""
MICRO CAPS
03B_MOTEUR_FX_V3.py

Conversion quotidienne vers EUR.

Principe :
- EUR = 1
- USD/CAD/GBP/SEK obtenus via paires EURXXX=X
- inversion pour obtenir XXX -> EUR
- jamais utiliser la barre FX du jour encore en formation
- dernière journée civile FX terminée uniquement

Version : 02/10/2026
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location("marche_public",Path(__file__).with_name("marche_public.py"))
marche=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(marche)


PAIRES = {
    "USD": "EURUSD=X",
    "CAD": "EURCAD=X",
    "GBP": "EURGBP=X",
    "SEK": "EURSEK=X",
    "DKK": "EURDKK=X",
    "NOK": "EURNOK=X",
    "CHF": "EURCHF=X",
}


def _close_series(hist, ticker):

    if isinstance(hist.columns, pd.MultiIndex):
        return hist["Close"][ticker].dropna()

    return hist["Close"].dropna()


def dernier_fx_termine(devise, maintenant_utc=None, date_reference=None):

    devise = str(devise).upper()

    if devise == "EUR":
        return {
            "devise": "EUR",
            "ticker_fx": "EUR",
            "date_fx": None,
            "fx_vers_eur": 1.0,
            "statut": "OK"
        }

    if devise not in PAIRES:
        raise ValueError(
            f"Devise non gérée : {devise}"
        )

    if maintenant_utc is None:
        maintenant_utc = datetime.now(
            ZoneInfo("UTC")
        )

    elif maintenant_utc.tzinfo is None:
        maintenant_utc = maintenant_utc.replace(
            tzinfo=ZoneInfo("UTC")
        )

    ticker = PAIRES[devise]

    # On exclut systématiquement la date UTC en cours :
    # sa barre quotidienne peut encore évoluer.
    dernier_jour_autorise = (
        maintenant_utc.date() - timedelta(days=1)
    )

    if date_reference:dernier_jour_autorise=min(dernier_jour_autorise,pd.Timestamp(date_reference).date())
    raw,preuve=marche.charger(ticker,dernier_jour_autorise)
    close=marche.serie(raw);close=close[close.index<=str(dernier_jour_autorise)]
    if close.empty:raise RuntimeError("FX absent : "+ticker)
    if (dernier_jour_autorise-pd.Timestamp(close.index[-1]).date()).days>4:raise RuntimeError("FX périmé : "+ticker)
    valeur_eur_devise=float(close.iloc[-1])

    if valeur_eur_devise <= 0:
        raise RuntimeError(
            f"Taux FX invalide pour {ticker}"
        )

    # EURXXX = nombre de XXX pour 1 EUR.
    # On veut XXX -> EUR.
    fx_vers_eur = 1.0 / valeur_eur_devise

    date_fx = close.index[-1]

    if hasattr(date_fx, "date"):
        date_fx = date_fx.date()

    return {
        "devise": devise,
        "ticker_fx": ticker,
        "date_fx": str(date_fx),
        "cours_EUR_devise": valeur_eur_devise,
        "fx_vers_eur": fx_vers_eur,
        "statut": "OK"
    }


def tous_les_fx(maintenant_utc=None,date_reference=None):

    resultat = {}

    for devise in ["EUR", "USD", "CAD", "GBP", "SEK"]:
        resultat[devise] = dernier_fx_termine(
            devise,
            maintenant_utc,date_reference=date_reference
        )

    return resultat

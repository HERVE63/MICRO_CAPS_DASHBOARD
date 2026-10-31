# -*- coding: utf-8 -*-
"""Diagnostic d'acces EODHD : aucun secret ni corps de reponse journalise.

Un diagnostic en erreur ne bloque pas la collecte 09D des 40 titulaires.
Il ne certifie ni la disponibilite des 40 titres ni la qualite des donnees.
"""
import os
import requests


def verifier():
    token = os.environ.get("EODHD_API_TOKEN") or os.environ.get("EODHD_API_KEY")
    if not token:
        print("DIAGNOSTIC EODHD API_TOKEN_ABSENT")
        return 2
    tests = (
        ("compte", "user"),
        ("cours_AAPL", "eod/AAPL.US"),
        ("fondamentaux_AAPL", "fundamentals/AAPL.US"),
    )
    echecs = 0
    for nom, endpoint in tests:
        try:
            response = requests.get(
                "https://eodhd.com/api/" + endpoint,
                params={"api_token": token, "fmt": "json"},
                timeout=20,
            )
            statut = response.status_code
            print("DIAGNOSTIC", nom, "HTTP", statut)
            if statut != 200:
                echecs += 1
        except requests.RequestException as exc:
            # Ne jamais imprimer str(exc) : une URL peut contenir le secret.
            print("DIAGNOSTIC", nom, "ERREUR", type(exc).__name__)
            echecs += 1
    print("DIAGNOSTIC_EODHD_ECHECS", echecs, "SUR", len(tests))
    return 1 if echecs else 0


if __name__ == "__main__":
    raise SystemExit(verifier())

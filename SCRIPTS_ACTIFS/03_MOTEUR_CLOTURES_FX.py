# -*- coding: utf-8 -*-

"""
MICRO CAPS — MOTEUR QUOTIDIEN V3

Chaîne :
T0 gelé
→ dernière séance réellement terminée
→ dernier FX quotidien terminé
→ conversion EUR
→ valorisation des 40 lignes
→ contrôles bloquants

IMPORTANT :
Ce script ne modifie jamais le T0.

Version : 02/10/2026
"""

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import importlib.util
import pandas as pd


BASE = Path(__file__).resolve().parent.parent

SRC = BASE / "SCRIPTS_ACTIFS"

T0_FILE = (
    BASE / "SAUVEGARDES" /
    "MICRO_CAPS_T0_GELE_2026-10-01.csv"
)

TEST_OUTPUT = (
    BASE / "DONNEES" /
    "TEST_MOTEUR_V3.csv"
)


def charger_module(nom, chemin):

    spec = importlib.util.spec_from_file_location(
        nom, chemin
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


clotures = charger_module(
    "mc_clotures",
    SRC / "03A_MOTEUR_CLOTURES_V3.py"
)

fxmod = charger_module(
    "mc_fx",
    SRC / "03B_MOTEUR_FX_V3.py"
)


def executer():

    t0 = pd.read_csv(T0_FILE)

    maintenant = datetime.now(
        ZoneInfo("UTC")
    )

    fx = fxmod.tous_les_fx(
        maintenant
    )

    resultats = []

    for _, r in t0.iterrows():

        ticker = str(
            r["Ticker_cotation"]
        )

        devise = str(
            r["Devise"]
        ).upper()

        try:

            px = (
                clotures
                .derniere_cloture_validee(
                    ticker,
                    maintenant
                )
            )

            taux = float(
                fx[devise]["fx_vers_eur"]
            )

            cours_eur = (
                float(px["cours_cloture"])
                * taux
            )

            quantite = float(
                r["Quantite_T0"]
            )

            valeur = (
                quantite * cours_eur
            )

            capital_t0 = float(
                r["Capital_T0_EUR"]
            )

            perf = (
                valeur / capital_t0 - 1
            ) * 100

            contribution = (
                valeur - capital_t0
            )

            resultats.append({
                "ID_ligne":
                    int(r["ID_ligne"]),

                "Societe":
                    r["Societe"],

                "Ticker_cotation":
                    ticker,

                "Pays":
                    r["Pays"],

                "Devise":
                    devise,

                "Marche":
                    px["marche"],

                "Date_cloture":
                    str(px["date_session"]),

                "Cours_cloture_devise":
                    float(px["cours_cloture"]),

                "Date_FX":
                    (
                        "FIXE"
                        if devise == "EUR"
                        else fx[devise]["date_fx"]
                    ),

                "FX_vers_EUR":
                    taux,

                "Cours_EUR":
                    cours_eur,

                "Quantite_T0":
                    quantite,

                "Capital_T0_EUR":
                    capital_t0,

                "Valeur_EUR":
                    valeur,

                "Performance_pct":
                    perf,

                "Contribution_EUR":
                    contribution,

                "Statut":
                    "OK"
            })

        except Exception as e:

            resultats.append({
                "ID_ligne":
                    int(r["ID_ligne"]),

                "Societe":
                    r["Societe"],

                "Ticker_cotation":
                    ticker,

                "Statut":
                    "ERREUR",

                "Erreur":
                    str(e)
            })

    df = pd.DataFrame(
        resultats
    )

    # ========================================================
    # CONTRÔLES BLOQUANTS
    # ========================================================

    if len(df) != 40:
        raise RuntimeError(
            f"Nombre de lignes invalide : {len(df)}"
        )

    if df["ID_ligne"].nunique() != 40:
        raise RuntimeError(
            "IDs non uniques"
        )

    erreurs = df[
        df["Statut"] != "OK"
    ]

    if len(erreurs) > 0:

        print(
            erreurs[
                [
                    "ID_ligne",
                    "Societe",
                    "Ticker_cotation",
                    "Erreur"
                ]
            ].to_string(index=False)
        )

        raise RuntimeError(
            "MOTEUR BLOQUÉ : "
            "au moins une ligne est en erreur."
        )

    # --------------------------------------------------------
    # ÉCRITURE TEST UNIQUEMENT
    # --------------------------------------------------------

    df.to_csv(
        TEST_OUTPUT,
        index=False
    )

    total = df[
        "Valeur_EUR"
    ].sum()

    perf_total = (
        total / 4000.0 - 1
    ) * 100

    print("=" * 80)
    print("MICRO CAPS — MOTEUR QUOTIDIEN V3")
    print("=" * 80)

    print(
        "Heure UTC :",
        maintenant.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print(
        f"40 lignes : OK"
    )

    print(
        f"Valeur totale : "
        f"{total:.2f} €"
    )

    print(
        f"Performance : "
        f"{perf_total:+.4f}%"
    )

    print()

    print("Séances utilisées :")

    print(
        df.groupby(
            ["Marche", "Date_cloture"]
        )
        .size()
        .reset_index(name="Nb")
        .to_string(index=False)
    )

    print()
    print(
        "Fichier TEST :",
        TEST_OUTPUT
    )

    print()
    print(
        "🔒 T0 non modifié."
    )

    print(
        "🔒 DERNIER_ETAT_MICRO_CAPS.csv "
        "non modifié."
    )

    return df


if __name__ == "__main__":
    executer()

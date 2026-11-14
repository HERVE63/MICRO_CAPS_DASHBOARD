# -*- coding: utf-8 -*-

"""
MICRO CAPS — BENCHMARKS V3

Benchmarks :
- S&P 500
- Nasdaq-100
- STOXX Europe 600

Règle :
aucune barre intraday.
Base 100 à la clôture du 01/10/2026.

Version : 02/10/2026
"""

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import importlib.util
import pandas as pd


BASE = Path(__file__).resolve().parent.parent

SRC = BASE / "SCRIPTS_ACTIFS"

T0_BENCH = (
    BASE / "DONNEES" /
    "BENCHMARKS_MICRO_CAPS.csv"
)

OUTPUT = (
    BASE / "DONNEES" /
    "TEST_BENCHMARKS_V3.csv"
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


def executer():

    ref = pd.read_csv(T0_BENCH)

    maintenant = datetime.now(
        ZoneInfo("UTC")
    )

    mapping = {
        "S&P 500": "^GSPC",
        "Nasdaq-100": "^NDX",
        "STOXX Europe 600": "^STOXX"
    }

    prix=pd.read_csv(BASE/"DONNEES/TEST_MOTEUR_V3.csv")
    frozen=pd.read_csv(BASE/"SAUVEGARDES/MICRO_CAPS_T0_GELE_2026-10-01.csv")
    dates=prix["Date_cloture"].astype(str).unique()
    if len(dates)!=1:raise RuntimeError("Dates portefeuille non synchronisées")
    reference=dates[0]
    resultats = []

    for nom, ticker in mapping.items():

        ligne = ref[
            ref["Benchmark"] == nom
        ]

        if ligne.empty:
            raise RuntimeError(
                f"T0 benchmark absent : {nom}"
            )

        r = ligne.iloc[0]

        # Accepte plusieurs noms de colonne
        # possibles dans le fichier historique.
        candidats = [
            "Cours_T0",
            "Cours_T0_devise",
            "Close_T0",
            "Valeur_T0"
        ]

        col_t0 = next(
            (
                c for c in candidats
                if c in ref.columns
            ),
            None
        )

        if col_t0 is None:
            raise RuntimeError(
                "Impossible d'identifier "
                "la colonne de cours T0. "
                f"Colonnes présentes : {list(ref.columns)}"
            )

        cours_t0 = float(
            r[col_t0]
        )

        px = (
            clotures
            .derniere_cloture_benchmark(
                ticker,
                maintenant,date_reference=reference
            )
        )

        cours = float(
            px["cours_cloture"]
        )

        currency="USD" if ticker in {"^GSPC","^NDX"} else "EUR"
        if px["devise"]!=currency:raise RuntimeError("Devise benchmark divergente")
        fx0s=frozen.loc[frozen["Devise"]==currency,"FX_T0_vers_EUR"].unique()
        fxs=prix.loc[prix["Devise"]==currency,"FX_vers_EUR"].unique()
        if len(fx0s)!=1 or len(fxs)!=1:raise RuntimeError("FX benchmark non unique")
        fx0,fx=float(fx0s[0]),float(fxs[0])
        base100_local=cours/cours_t0*100
        base100=base100_local*fx/fx0;perf=base100-100

        resultats.append({
            "Benchmark":
                nom,

            "Ticker":
                ticker,

            "Date_T0":
                "2026-10-01",

            "Cours_T0":
                cours_t0,

            "Date_cloture":
                str(px["date_session"]),

            "Cours_cloture":
                cours,

            "Base_100":
                base100,

            "Performance_pct":
                perf,

            "Devise_indice":currency,"Devise_performance":"EUR",
            "FX_T0_vers_EUR":fx0,"FX_vers_EUR":fx,
            "Base_100_devise_locale":base100_local,"Performance_locale_pct":base100_local-100,
            "Convention":"Indice de prix, change inclus, dividendes non réinvestis",
            "Statut":"OK"
        })

    df = pd.DataFrame(
        resultats
    )

    if len(df) != 3:
        raise RuntimeError(
            "Le moteur doit produire "
            "exactement 3 benchmarks."
        )

    df.to_csv(
        OUTPUT,
        index=False
    )

    print("=" * 86)
    print(
        "📊 MICRO CAPS — "
        "BENCHMARKS V3"
    )
    print("=" * 86)

    print(
        df[
            [
                "Benchmark",
                "Date_cloture",
                "Cours_T0",
                "Cours_cloture",
                "Base_100",
                "Performance_pct"
            ]
        ].to_string(
            index=False,
            formatters={
                "Cours_T0":
                    lambda x: f"{x:.6f}",

                "Cours_cloture":
                    lambda x: f"{x:.6f}",

                "Base_100":
                    lambda x: f"{x:.4f}",

                "Performance_pct":
                    lambda x: f"{x:+.4f}%"
            }
        )
    )

    print()
    print(
        "Fichier TEST :",
        OUTPUT
    )

    print()
    print(
        "🔒 Aucune barre intraday admise."
    )

    return df


if __name__ == "__main__":
    executer()

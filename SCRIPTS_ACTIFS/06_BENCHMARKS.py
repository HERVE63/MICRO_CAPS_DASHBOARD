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
                maintenant
            )
        )

        cours = float(
            px["cours_cloture"]
        )

        base100 = (
            cours / cours_t0
        ) * 100

        perf = (
            base100 - 100
        )

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

            "Statut":
                "OK"
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

# -*- coding: utf-8 -*-

"""
MICRO CAPS — CONTROLE QUALITE V3.4

Sépare strictement :
1. performance depuis T0
2. variation entre les deux dernières clôtures admissibles

Une variation journalière >25 % déclenche une investigation.
Elle n'est jamais neutralisée automatiquement.

Version : 02/10/2026
"""

from pathlib import Path
from datetime import timedelta
import pandas as pd
import numpy as np
import yfinance as yf


BASE = Path(__file__).resolve().parent.parent

REGISTRE_ANOMALIES = (
    BASE / "DONNEES/VALIDATIONS_ANOMALIES.csv"
)

MOTEUR_FILE = (
    BASE / "DONNEES" /
    "TEST_MOTEUR_V3.csv"
)

OUTPUT = (
    BASE / "DONNEES" /
    "TEST_CONTROLE_QUALITE_V3.csv"
)

T0_GELE = (
    BASE / "SAUVEGARDES" /
    "MICRO_CAPS_T0_GELE_2026-10-01.csv"
)


def close_series(hist, ticker):
    """
    Extrait robustement la série Close depuis yfinance,
    avec ou sans MultiIndex.
    """

    if hist.empty:
        raise RuntimeError(
            "Historique Yahoo vide"
        )

    if isinstance(hist.columns, pd.MultiIndex):

        # Cas normal yfinance :
        # niveau 0 = Price
        # niveau 1 = Ticker
        if "Close" not in hist.columns.get_level_values(0):
            raise RuntimeError(
                "Colonne Close absente du MultiIndex Yahoo"
            )

        bloc = hist.xs(
            "Close",
            axis=1,
            level=0
        )

        # DataFrame à une ou plusieurs colonnes
        if isinstance(bloc, pd.DataFrame):

            if ticker in bloc.columns:
                serie = bloc[ticker]

            elif bloc.shape[1] == 1:
                serie = bloc.iloc[:, 0]

            else:
                raise RuntimeError(
                    "Ticker introuvable dans Close Yahoo"
                )

        else:
            serie = bloc

    else:

        if "Close" not in hist.columns:
            raise RuntimeError(
                "Colonne Close absente de Yahoo"
            )

        serie = hist["Close"]

    serie = pd.to_numeric(
        serie,
        errors="coerce"
    ).dropna()

    if serie.empty:
        raise RuntimeError(
            "Série Close Yahoo vide"
        )

    return serie

def cloture_t0_gelee(ticker, date_actuelle):
    """
    Fallback strict sur le T0 officiel gelé.

    Utilise les colonnes réelles du fichier T0 :
    Ticker_cotation
    Date_T0
    Cours_T0_devise

    Le fallback n'est utilisé qu'après échec
    de la récupération Yahoo normale.
    """

    if not T0_GELE.exists():
        raise RuntimeError(
            "T0 gelé introuvable"
        )

    t0 = pd.read_csv(T0_GELE)

    colonnes_requises = {
        "Ticker_cotation",
        "Date_T0",
        "Cours_T0_devise"
    }

    manquantes = (
        colonnes_requises
        - set(t0.columns)
    )

    if manquantes:
        raise RuntimeError(
            "Colonnes T0 manquantes : "
            + ", ".join(sorted(manquantes))
        )

    ligne = t0[
        t0["Ticker_cotation"]
        .astype(str)
        .eq(str(ticker))
    ]

    if len(ligne) != 1:
        raise RuntimeError(
            "Ticker absent ou dupliqué "
            "dans le T0 gelé"
        )

    ligne = ligne.iloc[0]

    date_t0 = pd.Timestamp(
        ligne["Date_T0"]
    ).date()

    date_actuelle = pd.Timestamp(
        date_actuelle
    ).date()

    if date_t0 >= date_actuelle:
        raise RuntimeError(
            "T0 non antérieur à la date contrôlée"
        )

    cours_t0 = float(
        ligne["Cours_T0_devise"]
    )

    if (
        not pd.notna(cours_t0)
        or cours_t0 <= 0
    ):
        raise RuntimeError(
            "Cours T0 invalide"
        )

    return str(date_t0), cours_t0

def cloture_precedente(ticker, date_actuelle):

    date_actuelle = pd.Timestamp(
        date_actuelle
    ).date()

    debut = date_actuelle - timedelta(days=10)

    hist = yf.download(
        ticker,
        start=str(debut),
        end=str(date_actuelle),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False
    )

    if hist.empty:
        raise RuntimeError(
            "Historique précédent indisponible"
        )

    close = close_series(
        hist,
        ticker
    )

    if close.empty:
        raise RuntimeError(
            "Clôture précédente indisponible"
        )

    cours = float(close.iloc[-1])

    # Londres : GBp -> GBP
    if str(ticker).upper().endswith(".L"):
        cours /= 100.0

    date_prec = close.index[-1]

    if hasattr(date_prec, "date"):
        date_prec = date_prec.date()

    return str(date_prec), cours


def enregistrer_anomalie(
    registre,
    ligne,
    variation_jj
):
    """
    Ajoute une anomalie uniquement si elle n'existe pas déjà.

    Clé métier :
    Date_cloture + ID_position + Type_anomalie
    """

    date_cloture = str(ligne["Date_cloture"])
    id_position = str(int(ligne["ID_ligne"]))
    type_anomalie = "MOUVEMENT_EXTREME"

    if len(registre) > 0:

        masque = (
            registre["Date_cloture"].astype(str).eq(date_cloture)
            & registre["ID_position"].astype(str).eq(id_position)
            & registre["Type_anomalie"].astype(str).eq(type_anomalie)
        )

        if masque.any():
            return registre

    numero = len(registre) + 1

    nouvelle = {
        "ID_anomalie":
            f"ANO_{date_cloture}_{id_position}_{numero:04d}",

        "Date_cloture":
            date_cloture,

        "ID_position":
            id_position,

        "Societe":
            ligne["Societe"],

        "Ticker":
            ligne["Ticker_cotation"],

        "Type_anomalie":
            type_anomalie,

        "Variation_JJ_pct":
            variation_jj,

        "Cours_initial":
            ligne["Cours_cloture_devise"],

        "Devise":
            ligne["Devise"],

        "Statut_validation":
            "EN_ATTENTE",

        "Cours_retenu":
            pd.NA,

        "Source_1":
            pd.NA,

        "Source_2":
            pd.NA,

        "Type_operation_sur_titre":
            pd.NA,

        "Facteur_ajustement":
            pd.NA,

        "Commentaire":
            "Variation J/J >25 % détectée automatiquement.",

        "Date_detection":
            pd.Timestamp.now(tz="Europe/Paris").isoformat(),

        "Date_resolution":
            pd.NA,

        "Impact_historique":
            "BLOQUEE",

        "Version_regle":
            "QC_V3.4.1"
    }

    return pd.concat(
        [
            registre,
            pd.DataFrame(
                [nouvelle],
                columns=registre.columns
            )
        ],
        ignore_index=True
    )


def executer():

    cur = pd.read_csv(
        MOTEUR_FILE
    )

    controles = []

    if not REGISTRE_ANOMALIES.exists():
        raise RuntimeError(
            "Registre des anomalies introuvable."
        )

    registre = pd.read_csv(
        REGISTRE_ANOMALIES
    )

    for _, r in cur.iterrows():

        ticker = str(
            r["Ticker_cotation"]
        )

        statut = "OK"
        raison = "RAS"
        impact = "COMPTEE"

        try:

            cours_actuel = float(
                r["Cours_cloture_devise"]
            )

            if (
                not np.isfinite(cours_actuel)
                or cours_actuel <= 0
            ):
                raise ValueError(
                    "Cours actuel invalide"
                )

            date_prec, cours_prec = (
                cloture_precedente(
                    ticker,
                    r["Date_cloture"]
                )
            )

            variation_jj = (
                cours_actuel / cours_prec - 1
            ) * 100

            if abs(variation_jj) > 25:

                statut = "ALERTE_A_VERIFIER"
                impact = "BLOQUEE_EN_ATTENTE_VALIDATION"

                raison = (
                    "Variation J/J > 25 % : "
                    "validation obligatoire avant "
                    "historisation officielle."
                )

                registre = enregistrer_anomalie(
                    registre,
                    r,
                    variation_jj
                )

        except Exception as e_yahoo:

            try:

                date_prec, cours_prec = (
                    cloture_t0_gelee(
                        ticker,
                        r["Date_cloture"]
                    )
                )

                cours_actuel = float(
                    r["Cours_cloture_devise"]
                )

                variation_jj = (
                    cours_actuel / cours_prec - 1
                ) * 100

                statut = "OK"
                raison = (
                    "Clôture précédente issue du "
                    "T0 officiel gelé après échec Yahoo."
                )
                impact = "AUCUN"

                if abs(variation_jj) > 25:

                    statut = "ALERTE_A_VERIFIER"
                    impact = (
                        "BLOQUEE_EN_ATTENTE_VALIDATION"
                    )

                    raison = (
                        "Variation J/J > 25 % calculée "
                        "depuis le T0 officiel gelé : "
                        "validation obligatoire avant "
                        "historisation officielle."
                    )

                    registre = enregistrer_anomalie(
                        registre,
                        r,
                        variation_jj
                    )

            except Exception as e_t0:

                date_prec = None
                cours_prec = np.nan
                variation_jj = np.nan

                statut = "ERREUR_DONNEE"
                raison = (
                    "Yahoo : "
                    + str(e_yahoo)
                    + " | Fallback T0 : "
                    + str(e_t0)
                )
                impact = "BLOQUEE"

        controles.append({

            "ID_ligne":
                int(r["ID_ligne"]),

            "Societe":
                r["Societe"],

            "Ticker":
                ticker,

            "Date_precedente":
                date_prec,

            "Cours_precedent":
                cours_prec,

            "Date_cloture":
                r["Date_cloture"],

            "Cours_cloture":
                r["Cours_cloture_devise"],

            "Variation_JJ_pct":
                variation_jj,

            "Performance_depuis_T0_pct":
                r["Performance_pct"],

            "Statut_qualite":
                statut,

            "Raison":
                raison,

            "Impact_performance":
                impact
        })

    qc = pd.DataFrame(
        controles
    )

    # Ecriture atomique du registre
    temp_registre = REGISTRE_ANOMALIES.with_suffix(".tmp")

    registre.to_csv(
        temp_registre,
        index=False
    )

    temp_registre.replace(
        REGISTRE_ANOMALIES
    )

    qc.to_csv(
        OUTPUT,
        index=False
    )

    print("=" * 100)
    print(
        "🛡️ MICRO CAPS — "
        "CONTROLE QUALITE V3.4"
    )
    print("=" * 100)

    print(
        qc[
            [
                "ID_ligne",
                "Societe",
                "Date_precedente",
                "Date_cloture",
                "Variation_JJ_pct",
                "Performance_depuis_T0_pct",
                "Statut_qualite"
            ]
        ].to_string(
            index=False,
            formatters={
                "Variation_JJ_pct":
                    lambda x: f"{x:+.2f}%",

                "Performance_depuis_T0_pct":
                    lambda x: f"{x:+.2f}%"
            }
        )
    )

    print()
    print("Synthèse :")

    print(
        qc["Statut_qualite"]
        .value_counts()
        .to_string()
    )

    print()

    print(
        "Alertes à vérifier :",
        (
            qc["Statut_qualite"]
            == "ALERTE_A_VERIFIER"
        ).sum()
    )

    print(
        "Erreurs bloquantes :",
        (
            qc["Statut_qualite"]
            == "ERREUR_DONNEE"
        ).sum()
    )

    print()
    print(
        "🔒 Une ALERTE >25 % conserve le cours observé, "
        "mais bloque l'historisation officielle "
        "tant qu'elle est EN_ATTENTE."
    )

    print(
        "🔒 Une perte réelle CONFIRMEE sera comptée "
        "intégralement."
    )

    return qc


if __name__ == "__main__":
    executer()

# -*- coding: utf-8 -*-

"""
MICRO CAPS — GARDE-BARRIERE JOURNEE OFFICIELLE V3.1

Une date n'est admissible dans l'historique que si :

1. exactement 40 valeurs sont présentes ;
2. exactement 3 benchmarks sont présents ;
3. toutes les valeurs utilisent la même date de clôture ;
4. tous les benchmarks utilisent cette même date ;
5. aucune erreur bloquante ni anomalie >25 % non résolue n'existe ;
6. les IDs des 40 valeurs sont uniques ;
7. les 3 benchmarks sont uniques ;
8. la date n'est pas antérieure au T0.

Ce module NE MODIFIE PAS l'historique.
"""

from pathlib import Path
import pandas as pd


BASE = Path(__file__).resolve().parent.parent

PRIX = (
    BASE / "DONNEES" /
    "TEST_MOTEUR_V3.csv"
)

RESOLU = (
    BASE / "DONNEES" /
    "TEST_MOTEUR_RESOLU_V3.csv"
)

QC = (
    BASE / "DONNEES" /
    "TEST_CONTROLE_QUALITE_V3.csv"
)

BENCH = (
    BASE / "DONNEES" /
    "TEST_BENCHMARKS_V3.csv"
)

HIST = (
    BASE / "HISTORIQUE" /
    "HISTORIQUE_PERFORMANCE_V3.csv"
)

REGISTRE = (
    BASE / "DONNEES" /
    "VALIDATIONS_ANOMALIES.csv"
)

T0 = "2026-10-01"


def controler():

    prix = pd.read_csv(PRIX)

    if not RESOLU.exists():
        raise RuntimeError(
            "TEST_MOTEUR_RESOLU_V3.csv introuvable."
        )

    resolu = pd.read_csv(RESOLU)

    qc = pd.read_csv(QC)
    bench = pd.read_csv(BENCH)
    hist = pd.read_csv(HIST)

    if not REGISTRE.exists():
        raise RuntimeError(
            "Registre VALIDATIONS_ANOMALIES.csv introuvable."
        )

    registre = pd.read_csv(REGISTRE)

    raisons = []

    # --------------------------------------------------------
    # Complétude valeurs
    # --------------------------------------------------------

    if len(prix) != 40:
        raisons.append(
            f"Nombre de valeurs incorrect : {len(prix)}"
        )

    if (
        "ID_ligne" not in prix.columns
        or prix["ID_ligne"].nunique() != 40
    ):
        raisons.append(
            "Les 40 ID_ligne ne sont pas uniques."
        )

    # --------------------------------------------------------
    # Complétude benchmarks
    # --------------------------------------------------------

    if len(bench) != 3:
        raisons.append(
            f"Nombre de benchmarks incorrect : {len(bench)}"
        )

    if (
        "Benchmark" not in bench.columns
        or bench["Benchmark"].nunique() != 3
    ):
        raisons.append(
            "Les 3 benchmarks ne sont pas uniques."
        )

    # --------------------------------------------------------
    # Contrôle qualité
    # --------------------------------------------------------

    if len(qc) != 40:
        raisons.append(
            f"Contrôle qualité incomplet : {len(qc)} lignes."
        )

    nb_bloquantes = 0

    if "Statut_qualite" not in qc.columns:
        raisons.append(
            "Colonne Statut_qualite absente."
        )
    else:
        nb_bloquantes = int(
            (
                qc["Statut_qualite"]
                == "ERREUR_DONNEE"
            ).sum()
        )

        if nb_bloquantes > 0:
            raisons.append(
                f"{nb_bloquantes} erreur(s) "
                "qualité bloquante(s)."
            )

        # ----------------------------------------------------
        # Alertes >25 % : résolution obligatoire
        # ----------------------------------------------------

        alertes = qc[
            qc["Statut_qualite"]
            == "ALERTE_A_VERIFIER"
        ].copy()

        for _, alerte in alertes.iterrows():

            date_a = str(alerte["Date_cloture"])
            id_a = str(int(alerte["ID_ligne"]))

            if len(registre) == 0:
                correspondances = registre
            else:
                ids_registre = (
                    pd.to_numeric(
                        registre["ID_position"],
                        errors="coerce"
                    )
                    .astype("Int64")
                    .astype(str)
                )

                correspondances = registre[
                    registre["Date_cloture"]
                    .astype(str)
                    .eq(date_a)
                    &
                    ids_registre.eq(id_a)
                    &
                    registre["Type_anomalie"]
                    .astype(str)
                    .eq("MOUVEMENT_EXTREME")
                ]

            if len(correspondances) == 0:

                raisons.append(
                    f"Anomalie {date_a} / ID {id_a} "
                    "sans validation enregistrée."
                )

                continue

            if len(correspondances) > 1:

                raisons.append(
                    f"Anomalie {date_a} / ID {id_a} "
                    "présente plusieurs fois dans le registre."
                )

                continue

            validation = correspondances.iloc[0]

            statut_validation = str(
                validation["Statut_validation"]
            )

            impact = str(
                validation["Impact_historique"]
            )

            if (
                statut_validation == "CONFIRMEE"
                and impact == "DEBLOQUEE"
            ):
                # Le cours observé est le vrai cours :
                # la perte/gain reste intégralement compté.
                pass

            elif statut_validation == "EN_ATTENTE":

                raisons.append(
                    f"Anomalie {date_a} / ID {id_a} "
                    "encore EN_ATTENTE."
                )

            elif statut_validation == "REJETEE":

                raisons.append(
                    f"Anomalie {date_a} / ID {id_a} : "
                    "cours rejeté ; correction économique "
                    "pas encore appliquée au moteur."
                )

            elif (
                statut_validation
                == "OPERATION_SUR_TITRE"
            ):

                raisons.append(
                    f"Anomalie {date_a} / ID {id_a} : "
                    "opération sur titre validée mais "
                    "ajustement économique pas encore "
                    "appliqué au moteur."
                )

            else:

                raisons.append(
                    f"Anomalie {date_a} / ID {id_a} : "
                    f"statut non admissible "
                    f"({statut_validation})."
                )

    # --------------------------------------------------------
    # --------------------------------------------------------
    # Garde-barrière économique 04B
    # --------------------------------------------------------

    if len(resolu) != 40:
        raisons.append(
            f"04B : {len(resolu)} lignes au lieu de 40."
        )

    if "ID_ligne" not in resolu.columns:
        raisons.append(
            "04B : colonne ID_ligne absente."
        )
    elif resolu["ID_ligne"].nunique() != 40:
        raisons.append(
            "04B : IDs non uniques ou incomplets."
        )

    if "Date_cloture" not in resolu.columns:
        raisons.append(
            "04B : colonne Date_cloture absente."
        )
    else:
        dates_resolues = set(
            resolu["Date_cloture"]
            .astype(str)
        )

        dates_brutes = set(
            prix["Date_cloture"]
            .astype(str)
        )

        if dates_resolues != dates_brutes:
            raisons.append(
                "04B : dates résolues différentes "
                "des dates brutes."
            )

    if "Resolution_anomalie" not in resolu.columns:
        raisons.append(
            "04B : colonne Resolution_anomalie absente."
        )
    else:
        resolutions_autorisees = {
            "AUCUNE",
            "MOUVEMENT_REEL_CONFIRME",
            "FAUX_PRIX_CORRIGE"
        }

        resolutions_presentes = set(
            resolu["Resolution_anomalie"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        inconnues = (
            resolutions_presentes
            - resolutions_autorisees
        )

        if inconnues:
            raisons.append(
                "04B : résolution économique inconnue : "
                + ", ".join(sorted(inconnues))
            )

    if "Valeur_EUR_resolue" not in resolu.columns:
        raisons.append(
            "04B : Valeur_EUR_resolue absente."
        )
    else:
        valeurs_resolues = pd.to_numeric(
            resolu["Valeur_EUR_resolue"],
            errors="coerce"
        )

        if valeurs_resolues.isna().any():
            raisons.append(
                "04B : valeur économique manquante."
            )

        elif (valeurs_resolues <= 0).any():
            raisons.append(
                "04B : valeur économique non positive."
            )

    # Synchronisation
    # --------------------------------------------------------

    dates_actions = set(
        prix["Date_cloture"]
        .astype(str)
    )

    dates_bench = set(
        bench["Date_cloture"]
        .astype(str)
    )

    dates_globales = (
        dates_actions | dates_bench
    )

    date_candidate = None

    if len(dates_actions) != 1:
        raisons.append(
            "Les 40 valeurs ne sont pas "
            "synchronisées sur une seule date."
        )

    if len(dates_bench) != 1:
        raisons.append(
            "Les benchmarks ne sont pas "
            "synchronisés sur une seule date."
        )

    if len(dates_globales) != 1:
        raisons.append(
            "Valeurs et benchmarks n'utilisent "
            "pas la même date."
        )
    else:
        date_candidate = list(
            dates_globales
        )[0]

        if date_candidate < T0:
            raisons.append(
                "Date candidate antérieure au T0."
            )

    # --------------------------------------------------------
    # Décision
    # --------------------------------------------------------

    if raisons:

        statut = "EN_ATTENTE"

    else:

        deja_presente = (
            date_candidate
            in hist["Date_reference"]
            .astype(str)
            .values
        )

        if deja_presente:
            statut = "DEJA_PRESENTE"
        else:
            statut = "PRETE_A_AJOUTER"

    return {
        "statut": statut,
        "date_candidate": date_candidate,
        "raisons": raisons,
        "nb_bloquantes": nb_bloquantes
    }


if __name__ == "__main__":

    r = controler()

    print("=" * 92)
    print(
        "🚦 MICRO CAPS — "
        "GARDE-BARRIÈRE JOURNÉE OFFICIELLE"
    )
    print("=" * 92)

    print(
        "Date candidate :",
        r["date_candidate"]
    )

    print(
        "Statut :",
        r["statut"]
    )

    print(
        "Erreurs qualité bloquantes :",
        r["nb_bloquantes"]
    )

    if r["raisons"]:

        print()
        print("Motifs :")

        for raison in r["raisons"]:
            print(" -", raison)

    print()
    print(
        "🔒 Historique non modifié."
    )

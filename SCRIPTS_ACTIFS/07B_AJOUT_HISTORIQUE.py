# -*- coding: utf-8 -*-

"""
MICRO CAPS — AJOUT HISTORIQUE V3

Append-only strict.

Une ligne n'est ajoutée que si le garde-barrière 07A
renvoie PRETE_A_AJOUTER.

Aucune date existante n'est écrasée.
"""

from pathlib import Path
import importlib.util
import pandas as pd
import numpy as np


BASE = Path(__file__).resolve().parent.parent

SRC = BASE / "SCRIPTS_ACTIFS"

PORTEFEUILLES = (
    BASE / "DONNEES" /
    "TEST_PORTEFEUILLES_V3.csv"
)

BENCH = (
    BASE / "DONNEES" /
    "TEST_BENCHMARKS_V3.csv"
)

QC = (
    BASE / "DONNEES" /
    "TEST_CONTROLE_QUALITE_V3.csv"
)

HIST = (
    BASE / "HISTORIQUE" /
    "HISTORIQUE_PERFORMANCE_V3.csv"
)


def charger_module(nom, chemin):

    spec = importlib.util.spec_from_file_location(
        nom, chemin
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


gate = charger_module(
    "gate",
    SRC / "07A_GARDE_BARRIERE_JOURNEE.py"
)


def executer():

    # --------------------------------------------------------
    # 1. GARDE-BARRIÈRE
    # --------------------------------------------------------

    controle = gate.controler()

    statut = controle["statut"]
    date_candidate = controle["date_candidate"]

    print("=" * 94)
    print("📚 MICRO CAPS — AJOUT HISTORIQUE V3")
    print("=" * 94)

    print("Date candidate :", date_candidate)
    print("Garde-barrière :", statut)

    if statut != "PRETE_A_AJOUTER":

        print()
        print("⛔ AUCUNE ÉCRITURE.")

        if statut == "DEJA_PRESENTE":
            print(
                "Motif : cette date existe déjà "
                "dans l'historique."
            )
        else:
            print(
                "Motif : journée non admissible."
            )

            for raison in controle["raisons"]:
                print(" -", raison)

        return False

    # --------------------------------------------------------
    # 2. CHARGEMENT DES DONNÉES VALIDÉES
    # --------------------------------------------------------

    pf = pd.read_csv(PORTEFEUILLES)
    bench = pd.read_csv(BENCH)
    qc = pd.read_csv(QC)
    hist = pd.read_csv(HIST)

    if len(pf) != 40:
        raise RuntimeError(
            "Portefeuilles incomplets."
        )

    if len(bench) != 3:
        raise RuntimeError(
            "Benchmarks incomplets."
        )

    # --------------------------------------------------------
    # 3. PORTEFEUILLES
    # --------------------------------------------------------

    # --------------------------------------------------------
    # Les valorisations officielles viennent exclusivement
    # du moteur portefeuille 05.
    #
    # IMPORTANT :
    # Total_Gere_EUR inclut le cash retourné par 05C.
    # 07B ne recalcule jamais ce cash.
    # --------------------------------------------------------

    colonnes_totaux = [
        "Total_Temoin_EUR",
        "Total_Gere_EUR",
        "Total_Gere_Titres_EUR",
        "Cash_Gere_EUR"
    ]

    manquantes = [
        c for c in colonnes_totaux
        if c not in pf.columns
    ]

    if manquantes:
        raise RuntimeError(
            "Colonnes portefeuille 05 absentes : "
            + ", ".join(manquantes)
        )

    # Les métadonnées sont répétées sur les lignes par 05.
    # Elles doivent donc contenir une valeur unique.
    for c in colonnes_totaux:

        valeurs = pd.to_numeric(
            pf[c],
            errors="coerce"
        )

        if valeurs.isna().any():
            raise RuntimeError(
                f"Valeur invalide dans {c}."
            )

        uniques = valeurs.unique()

        if len(uniques) != 1:
            raise RuntimeError(
                f"{c} n'est pas unique dans la sortie 05."
            )

    valeur_temoin = float(
        pd.to_numeric(
            pf["Total_Temoin_EUR"],
            errors="raise"
        ).iloc[0]
    )

    valeur_gere_titres = float(
        pd.to_numeric(
            pf["Total_Gere_Titres_EUR"],
            errors="raise"
        ).iloc[0]
    )

    cash_gere = float(
        pd.to_numeric(
            pf["Cash_Gere_EUR"],
            errors="raise"
        ).iloc[0]
    )

    valeur_gere = float(
        pd.to_numeric(
            pf["Total_Gere_EUR"],
            errors="raise"
        ).iloc[0]
    )

    # Cohérence comptable obligatoire
    if not np.isclose(
        valeur_gere,
        valeur_gere_titres + cash_gere,
        rtol=0,
        atol=0.01
    ):
        raise RuntimeError(
            "Incohérence 05 : "
            "Total_Gere_EUR != titres + cash."
        )

    # Cohérence témoin avec les lignes
    temoin_lignes = float(
        pd.to_numeric(
            pf["Valeur_Temoin_EUR"],
            errors="raise"
        ).sum()
    )

    if not np.isclose(
        valeur_temoin,
        temoin_lignes,
        rtol=0,
        atol=0.01
    ):
        raise RuntimeError(
            "Incohérence 05 : "
            "Total_Temoin_EUR != somme des lignes témoin."
        )

    base_temoin = (
        valeur_temoin / 4000.0
    ) * 100

    base_gere = (
        valeur_gere / 4000.0
    ) * 100

    perf_temoin = base_temoin - 100
    perf_gere = base_gere - 100

    alpha = (
        perf_gere - perf_temoin
    )

    # --------------------------------------------------------
    # 4. BENCHMARKS
    # --------------------------------------------------------

    def base100(nom):

        ligne = bench[
            bench["Benchmark"] == nom
        ]

        if len(ligne) != 1:
            raise RuntimeError(
                f"Benchmark invalide : {nom}"
            )

        return float(
            ligne.iloc[0]["Base_100"]
        )

    b_sp = base100("S&P 500")
    b_ndx = base100("Nasdaq-100")
    b_stoxx = base100("STOXX Europe 600")

    # --------------------------------------------------------
    # 4B. COUCHE ÉCONOMIQUE RÉSOLUE
    # --------------------------------------------------------

    # --- CHARGEMENT EXPLICITE 04B ---
    chemin_resolu = (
        BASE
        / "DONNEES"
        / "TEST_MOTEUR_RESOLU_V3.csv"
    )

    if not chemin_resolu.exists():
        raise RuntimeError(
            "Couche économique 04B absente. "
            "Aucune écriture officielle."
        )

    resolu = pd.read_csv(chemin_resolu)

    if len(resolu) != 40:
        raise RuntimeError(
            f"Couche 04B invalide : {len(resolu)} lignes."
        )

    # --------------------------------------------------------
    # 5. QUALITÉ
    # --------------------------------------------------------

    nb_alertes = int(
        (
            qc["Statut_qualite"]
            == "ALERTE_A_VERIFIER"
        ).sum()
    )

    nb_erreurs = int(
        (
            qc["Statut_qualite"]
            == "ERREUR_DONNEE"
        ).sum()
    )

    if nb_erreurs != 0:
        raise RuntimeError(
            "Erreur qualité apparue après "
            "le garde-barrière."
        )

    # Une alerte qualité ne peut être historisée que si
    # elle a été explicitement résolue dans la couche économique.
    #
    # IMPORTANT :
    # - on ne transforme PAS l'alerte QC en OK ;
    # - on conserve donc sa trace dans Nb_alertes_qualite ;
    # - seules les alertes résolues par 04B sont admissibles.

    if nb_alertes > 0:

        alertes_qc = qc[
            qc["Statut_qualite"]
            == "ALERTE_A_VERIFIER"
        ].copy()

        # Colonnes nécessaires pour faire le raccord
        # position/date avec la couche économique résolue.
        for col in [
            "ID_ligne",
            "Date_cloture"
        ]:
            if col not in alertes_qc.columns:
                raise RuntimeError(
                    f"Colonne QC manquante : {col}"
                )

        for col in [
            "ID_ligne",
            "Date_cloture",
            "Resolution_anomalie"
        ]:
            if col not in resolu.columns:
                raise RuntimeError(
                    f"Colonne 04B manquante : {col}"
                )

        resolutions_admises = {
            "MOUVEMENT_REEL_CONFIRME",
            "FAUX_PRIX_CORRIGE"
        }

        non_resolues = []

        for _, alerte in alertes_qc.iterrows():

            id_ligne = int(alerte["ID_ligne"])
            date_alerte = str(alerte["Date_cloture"])

            correspondance = resolu[
                (
                    pd.to_numeric(
                        resolu["ID_ligne"],
                        errors="coerce"
                    )
                    == id_ligne
                )
                &
                (
                    resolu["Date_cloture"]
                    .astype(str)
                    == date_alerte
                )
            ]

            if len(correspondance) != 1:
                non_resolues.append(
                    f"ID {id_ligne} / {date_alerte} "
                    f"(correspondances 04B={len(correspondance)})"
                )
                continue

            resolution = str(
                correspondance.iloc[0][
                    "Resolution_anomalie"
                ]
            )

            if resolution not in resolutions_admises:
                non_resolues.append(
                    f"ID {id_ligne} / {date_alerte} "
                    f"({resolution})"
                )

        if non_resolues:
            raise RuntimeError(
                "Alerte(s) qualité non résolue(s) : "
                + " ; ".join(non_resolues)
                + ". Aucune écriture officielle."
            )

        print(
            f"Alertes qualité résolues : "
            f"{nb_alertes}/{nb_alertes}"
        )

    # --------------------------------------------------------
    # 6. CONSTRUCTION DE LA LIGNE
    # --------------------------------------------------------

    nouvelle = pd.DataFrame([{

        "Date_reference":
            date_candidate,

        "Valeur_Temoin_EUR":
            valeur_temoin,

        "Valeur_Gere_EUR":
            valeur_gere,

        "Base100_Temoin":
            base_temoin,

        "Base100_Gere":
            base_gere,

        "Base100_SP500":
            b_sp,

        "Base100_Nasdaq100":
            b_ndx,

        "Base100_STOXX600":
            b_stoxx,

        "Perf_Temoin_pct":
            perf_temoin,

        "Perf_Gere_pct":
            perf_gere,

        "Perf_SP500_pct":
            b_sp - 100,

        "Perf_Nasdaq100_pct":
            b_ndx - 100,

        "Perf_STOXX600_pct":
            b_stoxx - 100,

        "Alpha_Gere_vs_Temoin_pts":
            alpha,

        "Nb_alertes_qualite":
            nb_alertes,

        "Nb_erreurs_bloquantes":
            nb_erreurs,

        "Statut":
            "VALIDE"
    }])

    # --------------------------------------------------------
    # 7. CONTRÔLES APPEND-ONLY
    # --------------------------------------------------------

    if (
        date_candidate
        in hist["Date_reference"]
        .astype(str)
        .values
    ):
        raise RuntimeError(
            "Protection doublon déclenchée."
        )

    if list(nouvelle.columns) != list(hist.columns):
        raise RuntimeError(
            "Schéma historique incompatible."
        )

    derniere_date = str(
        hist["Date_reference"].max()
    )

    if date_candidate <= derniere_date:
        raise RuntimeError(
            "Date candidate non postérieure "
            "à la dernière date historique."
        )

    # --------------------------------------------------------
    # 8. ÉCRITURE ATOMIQUE
    # --------------------------------------------------------

    complet = pd.concat(
        [hist, nouvelle],
        ignore_index=True
    )

    temporaire = HIST.with_suffix(
        ".tmp"
    )

    complet.to_csv(
        temporaire,
        index=False
    )

    # Vérification avant remplacement
    controle_fichier = pd.read_csv(
        temporaire
    )

    if len(controle_fichier) != len(hist) + 1:
        temporaire.unlink(missing_ok=True)
        raise RuntimeError(
            "Contrôle fichier temporaire échoué."
        )

    temporaire.replace(HIST)

    print()
    print("✅ JOURNÉE AJOUTÉE")
    print("Date :", date_candidate)

    print(
        f"Témoin : {valeur_temoin:.2f} € "
        f"| {perf_temoin:+.4f}%"
    )

    print(
        f"Géré   : {valeur_gere:.2f} € "
        f"| {perf_gere:+.4f}%"
    )

    print(
        f"Alpha  : {alpha:+.4f} point"
    )

    print()
    print(
        "Nombre de dates officielles :",
        len(complet)
    )

    return True


if __name__ == "__main__":
    executer()

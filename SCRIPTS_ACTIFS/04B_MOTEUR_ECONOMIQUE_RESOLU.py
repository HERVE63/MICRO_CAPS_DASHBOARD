
from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parent.parent

PRIX = BASE / "DONNEES/TEST_MOTEUR_V3.csv"
QC = BASE / "DONNEES/TEST_CONTROLE_QUALITE_V3.csv"
REGISTRE = BASE / "DONNEES/VALIDATIONS_ANOMALIES.csv"

OUTPUT = BASE / "DONNEES/TEST_MOTEUR_RESOLU_V3.csv"


def id_normalise(x):
    try:
        return str(int(float(x)))
    except Exception:
        return str(x).strip()


def executer():

    prix = pd.read_csv(PRIX)
    qc = pd.read_csv(QC)
    registre = pd.read_csv(REGISTRE)

    if len(prix) != 40:
        raise RuntimeError(
            f"Prix : 40 lignes attendues, {len(prix)} obtenues."
        )

    if len(qc) != 40:
        raise RuntimeError(
            f"QC : 40 lignes attendues, {len(qc)} obtenues."
        )

    if prix["ID_ligne"].nunique() != 40:
        raise RuntimeError("IDs prix non uniques.")

    if qc["ID_ligne"].nunique() != 40:
        raise RuntimeError("IDs QC non uniques.")

    df = prix.merge(
        qc[
            [
                "ID_ligne",
                "Variation_JJ_pct",
                "Statut_qualite",
                "Impact_performance"
            ]
        ],
        on="ID_ligne",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Colonnes de traçabilité
    # --------------------------------------------------------

    df["Cours_brut_devise"] = pd.to_numeric(
        df["Cours_cloture_devise"],
        errors="coerce"
    )

    df["Cours_retenu_devise"] = df["Cours_brut_devise"]

    df["Resolution_anomalie"] = "AUCUNE"
    df["ID_anomalie"] = pd.NA

    # --------------------------------------------------------
    # Erreurs de données classiques
    # --------------------------------------------------------

    erreurs = df[
        df["Statut_qualite"].astype(str)
        == "ERREUR_DONNEE"
    ]

    if len(erreurs) > 0:
        raise RuntimeError(
            "ERREUR_DONNEE présente : "
            "moteur économique bloqué."
        )

    # --------------------------------------------------------
    # Traitement des alertes >25 %
    # --------------------------------------------------------

    alertes = df[
        df["Statut_qualite"].astype(str)
        == "ALERTE_A_VERIFIER"
    ]

    for idx, ligne in alertes.iterrows():

        date_cloture = str(ligne["Date_cloture"])[:10]
        id_pos = id_normalise(ligne["ID_ligne"])

        if len(registre) == 0:
            raise RuntimeError(
                f"Alerte {id_pos} du {date_cloture} "
                "sans registre de validation."
            )

        ids_reg = registre["ID_position"].map(id_normalise)

        masque = (
            registre["Date_cloture"].astype(str).str[:10]
            .eq(date_cloture)
            &
            ids_reg.eq(id_pos)
            &
            registre["Type_anomalie"].astype(str)
            .eq("MOUVEMENT_EXTREME")
        )

        matches = registre[masque]

        if len(matches) != 1:
            raise RuntimeError(
                f"Anomalie {id_pos} / {date_cloture} : "
                f"{len(matches)} validation(s), attendu 1."
            )

        r = matches.iloc[0]

        statut = str(
            r["Statut_validation"]
        ).strip().upper()

        impact = str(
            r["Impact_historique"]
        ).strip().upper()

        df.at[idx, "ID_anomalie"] = r["ID_anomalie"]

        # ----------------------------------------------------
        # Mouvement réel confirmé
        # ----------------------------------------------------

        if statut == "CONFIRMEE":

            if impact != "DEBLOQUEE":
                raise RuntimeError(
                    f"Anomalie {r['ID_anomalie']} confirmée "
                    "mais historique non débloqué."
                )

            df.at[
                idx, "Resolution_anomalie"
            ] = "MOUVEMENT_REEL_CONFIRME"

            # cours brut conservé

        # ----------------------------------------------------
        # Faux prix : cours corrigé documenté
        # ----------------------------------------------------

        elif statut == "REJETEE":

            if impact != "DEBLOQUEE":
                raise RuntimeError(
                    f"Anomalie {r['ID_anomalie']} rejetée "
                    "mais historique non débloqué."
                )

            cours_retenu = pd.to_numeric(
                pd.Series([r["Cours_retenu"]]),
                errors="coerce"
            ).iloc[0]

            if pd.isna(cours_retenu) or cours_retenu <= 0:
                raise RuntimeError(
                    f"Cours_retenu invalide pour "
                    f"{r['ID_anomalie']}."
                )

            source1 = str(
                r.get("Source_1", "")
            ).strip()

            source2 = str(
                r.get("Source_2", "")
            ).strip()

            if (
                source1 == ""
                or source1.lower() == "nan"
                or source2 == ""
                or source2.lower() == "nan"
            ):
                raise RuntimeError(
                    f"Deux sources requises pour corriger "
                    f"{r['ID_anomalie']}."
                )

            df.at[
                idx, "Cours_retenu_devise"
            ] = float(cours_retenu)

            df.at[
                idx, "Resolution_anomalie"
            ] = "FAUX_PRIX_CORRIGE"

        # ----------------------------------------------------
        # Corporate action :
        # NE PAS bricoler une correction ici
        # ----------------------------------------------------

        elif statut == "OPERATION_SUR_TITRE":

            raise RuntimeError(
                f"Opération sur titre détectée : "
                f"{r['ID_anomalie']}. "
                "Ajustement économique non encore implémenté."
            )

        elif statut == "EN_ATTENTE":

            raise RuntimeError(
                f"Anomalie {r['ID_anomalie']} "
                "encore EN_ATTENTE."
            )

        else:

            raise RuntimeError(
                f"Statut de validation inconnu : {statut}"
            )

    # --------------------------------------------------------
    # Recalcul économique
    # --------------------------------------------------------

    for c in [
        "FX_vers_EUR",
        "Quantite_T0",
        "Capital_T0_EUR"
    ]:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

    if (
        df[
            [
                "Cours_retenu_devise",
                "FX_vers_EUR",
                "Quantite_T0",
                "Capital_T0_EUR"
            ]
        ].isna().any().any()
    ):
        raise RuntimeError(
            "Valeur numérique manquante après résolution."
        )

    if (
        (df["Cours_retenu_devise"] <= 0).any()
        or (df["FX_vers_EUR"] <= 0).any()
        or (df["Quantite_T0"] <= 0).any()
    ):
        raise RuntimeError(
            "Cours / FX / quantité non positif."
        )

    df["Cours_EUR_resolu"] = (
        df["Cours_retenu_devise"]
        * df["FX_vers_EUR"]
    )

    df["Valeur_EUR_resolue"] = (
        df["Quantite_T0"]
        * df["Cours_EUR_resolu"]
    )

    df["Performance_resolue_pct"] = (
        df["Valeur_EUR_resolue"]
        / df["Capital_T0_EUR"]
        - 1
    ) * 100

    df["Contribution_resolue_EUR"] = (
        df["Valeur_EUR_resolue"]
        - df["Capital_T0_EUR"]
    )

    # --------------------------------------------------------
    # Écriture atomique
    # --------------------------------------------------------

    tmp = OUTPUT.with_suffix(".tmp")

    df.to_csv(
        tmp,
        index=False
    )

    tmp.replace(OUTPUT)

    print("=" * 92)
    print("🧠 MICRO CAPS — MOTEUR ÉCONOMIQUE RÉSOLU")
    print("=" * 92)

    print("Lignes :", len(df))

    print(
        "Sans anomalie :",
        (df["Resolution_anomalie"] == "AUCUNE").sum()
    )

    print(
        "Mouvements réels confirmés :",
        (
            df["Resolution_anomalie"]
            == "MOUVEMENT_REEL_CONFIRME"
        ).sum()
    )

    print(
        "Faux prix corrigés :",
        (
            df["Resolution_anomalie"]
            == "FAUX_PRIX_CORRIGE"
        ).sum()
    )

    print(
        "Valeur témoin résolue :",
        f"{df['Valeur_EUR_resolue'].sum():.4f} €"
    )

    print()
    print("Fichier TEST :", OUTPUT)
    print()
    print("🔒 Aucun historique modifié")
    print("🔒 T0 non modifié")

    return df


if __name__ == "__main__":
    executer()

# -*- coding: utf-8 -*-

"""
MICRO CAPS — 05C REPLAY PORTEFEUILLE GERE V2

Source :
    ETAT_INITIAL_PORTEFEUILLE_GERE.csv
    +
    JOURNAL_ARBITRAGES_GERE.csv

Principes :
- replay déterministe ;
- journal append-only ;
- ordre Date_execution puis ID_operation ;
- aucune correction silencieuse ;
- cash jamais négatif ;
- sortie conservée dans l'historique ;
- une nouvelle entrée ne repart jamais artificiellement à 100 EUR ;
- aucune modification du T0 ou de l'état initial.
"""

from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent

INITIAL = BASE / "DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv"
JOURNAL = BASE / "DONNEES/JOURNAL_ARBITRAGES_GERE.csv"
PARAMS_ARBITRAGE = BASE / "CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv"

OUTPUT = BASE / "DONNEES/TEST_ETAT_GERE_RECONSTRUIT.csv"


def nombre(x, nom):
    try:
        v = float(x)
    except Exception:
        raise RuntimeError(f"{nom} invalide : {x}")

    if pd.isna(v):
        raise RuntimeError(f"{nom} manquant.")

    return v


def _taux_frais():
    p = pd.read_csv(PARAMS_ARBITRAGE)
    q = p.set_index("Parametre")
    achat = float(q.loc["Frais_achat","Valeur"]) / 100.0
    vente = float(q.loc["Frais_vente","Valeur"]) / 100.0
    if achat < 0 or vente < 0:
        raise RuntimeError("Taux de frais invalide.")
    return achat, vente


def executer():

    taux_achat, taux_vente = _taux_frais()

    initial = pd.read_csv(INITIAL)
    journal = pd.read_csv(JOURNAL)

    # ========================================================
    # 1. ETAT INITIAL
    # ========================================================

    if len(initial) != 40:
        raise RuntimeError(
            f"Etat initial invalide : {len(initial)} positions."
        )

    if initial["ID_position"].nunique() != 40:
        raise RuntimeError("ID_position initiaux non uniques.")

    if abs(
        initial["Capital_initial_EUR"].astype(float).sum()
        - 4000.0
    ) > 0.01:
        raise RuntimeError("Capital initial différent de 4 000 EUR.")

    positions = initial.copy()

    positions["Capital_realise_EUR"] = 0.0
    positions["Date_sortie"] = pd.NA
    positions["ID_operation_sortie"] = pd.NA

    cash = 0.0

    # ========================================================
    # 2. JOURNAL
    # ========================================================

    if len(journal) > 0:

        if journal["ID_operation"].duplicated().any():
            raise RuntimeError(
                "ID_operation dupliqué dans le journal."
            )

        journal["Date_execution"] = pd.to_datetime(
            journal["Date_execution"],
            errors="raise"
        )

        # Ordre comptable explicite et déterministe.
        # Plusieurs opérations peuvent avoir la même date.
        if "Sequence_execution" not in journal.columns:
            raise RuntimeError(
                "Sequence_execution absente du journal."
            )

        journal["Sequence_execution"] = pd.to_numeric(
            journal["Sequence_execution"],
            errors="raise"
        )

        if journal["Sequence_execution"].isna().any():
            raise RuntimeError(
                "Sequence_execution manquante."
            )

        # Une séquence doit être unique à l'intérieur
        # d'une même date d'exécution.
        if journal.duplicated(
            subset=["Date_execution", "Sequence_execution"]
        ).any():
            raise RuntimeError(
                "Sequence_execution dupliquée pour une même date."
            )

        journal = journal.sort_values(
            [
                "Date_execution",
                "Sequence_execution",
                "ID_operation"
            ]
        ).reset_index(drop=True)

    # ========================================================
    # Fonctions internes
    # ========================================================

    def normaliser_id(valeur):
        """
        Canonise les identifiants lus depuis CSV.

        1       -> "1"
        1.0     -> "1"
        "1.0"   -> "1"
        "1"     -> "1"
        "NEW_X" -> "NEW_X"
        """

        if pd.isna(valeur):
            return ""

        s = str(valeur).strip()

        try:
            f = float(s)

            if f.is_integer():
                return str(int(f))

        except (ValueError, TypeError, OverflowError):
            pass

        return s


    def active_par_id(id_position):

        id_recherche = normaliser_id(id_position)

        masque = (
            (
                positions["ID_position"]
                .apply(normaliser_id)
                == id_recherche
            )
            & (positions["Statut"] == "ACTIF")
        )

        if masque.sum() != 1:
            raise RuntimeError(
                f"Position active introuvable/non unique : "
                f"{id_position}"
            )

        return positions.index[masque][0]


    def vendre(
        id_position,
        quantite,
        cours,
        fx,
        frais,
        date_execution,
        id_operation
    ):

        nonlocal cash, positions

        idx = active_par_id(id_position)

        q_dispo = nombre(
            positions.loc[idx, "Quantite"],
            "Quantite disponible"
        )

        if quantite <= 0:
            raise RuntimeError("Quantité vendue <= 0.")

        if quantite > q_dispo + 1e-10:
            raise RuntimeError(
                "Vente supérieure à la quantité détenue."
            )

        produit = (
            quantite * cours * fx - frais
        )

        if produit <= 0:
            raise RuntimeError(
                "Produit net de vente non positif."
            )

        positions.loc[idx, "Quantite"] = (
            q_dispo - quantite
        )

        positions.loc[
            idx, "Capital_realise_EUR"
        ] += produit

        cash += produit

        if abs(
            float(positions.loc[idx, "Quantite"])
        ) < 1e-10:

            positions.loc[idx, "Quantite"] = 0.0
            positions.loc[idx, "Statut"] = "SORTI"
            positions.loc[idx, "Date_sortie"] = str(
                date_execution.date()
            )
            positions.loc[
                idx, "ID_operation_sortie"
            ] = id_operation

        return produit


    def renforcer(
        id_position,
        montant,
        cours,
        fx,
        frais
    ):

        nonlocal cash, positions

        idx = active_par_id(id_position)

        if montant <= frais:
            raise RuntimeError(
                "Montant de renforcement insuffisant."
            )

        # Tolérance technique d'un centime :
        # Montant_EUR représente le débit TOTAL du cash,
        # frais d'entrée compris.
        if montant > cash + 0.01:
            raise RuntimeError(
                "Cash insuffisant pour le renforcement."
            )

        # Si l'écart ne provient que des arrondis numériques,
        # on utilise exactement le cash disponible.
        if montant > cash:
            montant = cash

        net = montant - frais
        quantite = net / (cours * fx)

        positions.loc[idx, "Quantite"] = (
            nombre(
                positions.loc[idx, "Quantite"],
                "Quantite"
            )
            + quantite
        )

        cash -= montant

        return quantite


    def nouvelle_entree(
        operation,
        montant,
        cours,
        fx,
        frais
    ):

        nonlocal cash, positions

        if montant <= frais:
            raise RuntimeError(
                "Montant d'entrée insuffisant."
            )

        # Tolérance technique d'un centime :
        # Montant_EUR représente le débit TOTAL du cash,
        # frais d'entrée compris.
        if montant > cash + 0.01:
            raise RuntimeError(
                "Cash insuffisant pour l'entrée."
            )

        # Neutralisation d'un éventuel écart flottant
        # inférieur ou égal à un centime.
        if montant > cash:
            montant = cash

        net = montant - frais
        quantite = net / (cours * fx)

        # ID permanent distinct des 40 IDs T0
        id_position = (
            "NEW_" + str(operation["ID_operation"])
        )

        if (
            positions["ID_position"].astype(str)
            == id_position
        ).any():
            raise RuntimeError(
                f"ID nouvelle position déjà utilisé : "
                f"{id_position}"
            )

        nouvelle = pd.DataFrame([{
            "ID_position": id_position,
            "ID_origine_T0": pd.NA,
            "Societe": operation["Societe_entrante"],
            "Ticker": operation["Ticker_entrant"],
            "Devise": operation.get(
                "Devise_entrante", pd.NA
            ),
            "Date_entree": str(
                operation["Date_execution"].date()
            ),
            "Quantite": quantite,
            "Capital_initial_EUR": net,
            "Statut": "ACTIF",
            "Capital_realise_EUR": 0.0,
            "Date_sortie": pd.NA,
            "ID_operation_sortie": pd.NA
        }])

        positions = pd.concat(
            [positions, nouvelle],
            ignore_index=True
        )

        cash -= montant

        return quantite

    # ========================================================
    # 3. REPLAY CHRONOLOGIQUE
    # ========================================================

    for _, op in journal.iterrows():

        statut_op = str(
            op.get("Statut_operation", "")
        ).strip().upper()

        # seules les opérations réellement exécutées
        # doivent modifier le portefeuille
        if statut_op not in {
            "EXECUTEE",
            "EXÉCUTÉE",
            "EXECUTE",
            "EXÉCUTÉ"
        }:
            continue

        typ = str(
            op["Type_operation"]
        ).strip().upper()

        id_op = op["ID_operation"]
        date_op = op["Date_execution"]

        # ----------------------------------------------------
        # SORTIE
        # ----------------------------------------------------

        if typ == "SORTIE":

            id_sortie = op["ID_ligne_sortante"]

            idx = active_par_id(id_sortie)

            quantite = nombre(
                positions.loc[idx, "Quantite"],
                "Quantite sortie"
            )

            cours = nombre(
                op["Cours_execution_sortie"],
                "Cours sortie"
            )

            fx = nombre(
                op["FX_sortie_vers_EUR"],
                "FX sortie vers EUR"
            )

            frais = nombre(
                op["Frais_sortie_EUR"]
                if not pd.isna(op["Frais_sortie_EUR"])
                else 0.0,
                "Frais sortie EUR"
            )

            if frais < 0:
                raise RuntimeError(
                    f"Frais sortie négatifs — opération {id_op}"
                )
            frais_attendus = quantite * cours * fx * taux_vente
            if abs(frais - frais_attendus) > 0.01:
                raise RuntimeError(
                    f"Frais vente non conformes à {taux_vente*100:.2f}% — opération {id_op}"
                )

            vendre(
                id_sortie,
                quantite,
                cours,
                fx,
                frais,
                date_op,
                id_op
            )

        # ----------------------------------------------------
        # ALLEGEMENT
        # ----------------------------------------------------

        elif typ in {"ALLEGEMENT", "ALLÉGEMENT"}:

            id_sortie = op["ID_ligne_sortante"]

            quantite = nombre(
                op["Quantite_vendue"],
                "Quantite vendue"
            )

            cours = nombre(
                op["Cours_execution_sortie"],
                "Cours sortie"
            )

            fx = nombre(
                op["FX_sortie_vers_EUR"],
                "FX sortie vers EUR"
            )

            frais = nombre(
                op["Frais_sortie_EUR"]
                if not pd.isna(op["Frais_sortie_EUR"])
                else 0.0,
                "Frais sortie EUR"
            )

            if frais < 0:
                raise RuntimeError(
                    f"Frais sortie négatifs — opération {id_op}"
                )
            frais_attendus = quantite * cours * fx * taux_vente
            if abs(frais - frais_attendus) > 0.01:
                raise RuntimeError(
                    f"Frais vente non conformes à {taux_vente*100:.2f}% — opération {id_op}"
                )

            vendre(
                id_sortie,
                quantite,
                cours,
                fx,
                frais,
                date_op,
                id_op
            )

        # ----------------------------------------------------
        # RENFORCEMENT
        # ----------------------------------------------------

        elif typ == "RENFORCEMENT":

            id_entree = op["ID_ligne_entrante"]

            montant = nombre(
                op["Montant_EUR"],
                "Montant renforcement"
            )

            cours = nombre(
                op["Cours_execution_entree"],
                "Cours entrée"
            )

            fx = nombre(
                op["FX_entree_vers_EUR"],
                "FX entrée vers EUR"
            )

            frais = nombre(
                op["Frais_entree_EUR"]
                if not pd.isna(op["Frais_entree_EUR"])
                else 0.0,
                "Frais entrée EUR"
            )

            if frais < 0:
                raise RuntimeError(
                    f"Frais entrée négatifs — opération {id_op}"
                )
            frais_attendus = montant * taux_achat / (1.0 + taux_achat)
            if abs(frais - frais_attendus) > 0.01:
                raise RuntimeError(
                    f"Frais achat non conformes à {taux_achat*100:.2f}% — opération {id_op}"
                )

            renforcer(
                id_entree,
                montant,
                cours,
                fx,
                frais
            )

        # ----------------------------------------------------
        # ENTREE
        # ----------------------------------------------------

        elif typ in {"ENTREE", "ENTRÉE"}:

            montant = nombre(
                op["Montant_EUR"],
                "Montant entrée"
            )

            cours = nombre(
                op["Cours_execution_entree"],
                "Cours entrée"
            )

            fx = nombre(
                op["FX_entree_vers_EUR"],
                "FX entrée vers EUR"
            )

            frais = nombre(
                op["Frais_entree_EUR"]
                if not pd.isna(op["Frais_entree_EUR"])
                else 0.0,
                "Frais entrée EUR"
            )

            if frais < 0:
                raise RuntimeError(
                    f"Frais entrée négatifs — opération {id_op}"
                )
            frais_attendus = montant * taux_achat / (1.0 + taux_achat)
            if abs(frais - frais_attendus) > 0.01:
                raise RuntimeError(
                    f"Frais achat non conformes à {taux_achat*100:.2f}% — opération {id_op}"
                )

            nouvelle_entree(
                op,
                montant,
                cours,
                fx,
                frais
            )

        else:
            raise RuntimeError(
                f"Type_operation inconnu : "
                f"{typ} — opération {id_op}"
            )

        if cash < -1e-8:
            raise RuntimeError(
                f"Cash négatif après opération {id_op}"
            )

    # ========================================================
    # 4. NORMALISATION
    # ========================================================

    if abs(cash) < 1e-10:
        cash = 0.0

    nb_actives = int(
        (positions["Statut"] == "ACTIF").sum()
    )

    nb_sorties = int(
        (positions["Statut"] == "SORTI").sum()
    )

    if (
        positions.loc[
            positions["Statut"] == "ACTIF",
            "Quantite"
        ].astype(float) < 0
    ).any():
        raise RuntimeError(
            "Quantité active négative détectée."
        )

    # ========================================================
    # 5. SAUVEGARDE DU REPLAY
    # ========================================================

    positions.to_csv(
        OUTPUT,
        index=False
    )

    print("=" * 92)
    print("🔁 MICRO CAPS — REPLAY PORTEFEUILLE GÉRÉ V2")
    print("=" * 92)

    print(
        "Opérations journalisées :",
        len(journal)
    )

    print(
        "Positions actives :",
        nb_actives
    )

    print(
        "Positions sorties archivées :",
        nb_sorties
    )

    print(
        f"Cash disponible : {cash:.4f} €"
    )

    if len(journal) == 0:

        # invariant spécial T0
        compare_cols = [
            "ID_position",
            "ID_origine_T0",
            "Societe",
            "Ticker",
            "Devise",
            "Date_entree",
            "Quantite",
            "Capital_initial_EUR",
            "Statut"
        ]

        a = initial[compare_cols].reset_index(drop=True)
        b = positions[compare_cols].reset_index(drop=True)

        if not a.equals(b):
            raise RuntimeError(
                "Replay vide différent de l'état initial."
            )

        print()
        print(
            "Comparaison état initial / replay : IDENTIQUE"
        )

    print()
    print("Fichier TEST :")
    print(OUTPUT)

    print()
    print("🔒 Journal non modifié")
    print("🔒 Etat initial non modifié")
    print("🔒 T0 non modifié")

    return {
        "positions": positions,
        "cash": cash,
        "nb_actives": nb_actives,
        "nb_sorties": nb_sorties
    }


if __name__ == "__main__":
    executer()

# réception frais proportionnels

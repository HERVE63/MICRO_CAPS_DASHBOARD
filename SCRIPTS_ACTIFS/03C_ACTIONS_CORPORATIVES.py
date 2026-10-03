
from pathlib import Path
import pandas as pd
import yfinance as yf

BASE = Path(__file__).resolve().parent.parent

COHORTE = BASE / "DONNEES/COHORTE_MICRO_CAPS_T0.csv"

OUTPUT = (
    BASE /
    "DONNEES/TEST_ACTIONS_CORPORATIVES_V3.csv"
)

T0 = pd.Timestamp("2026-10-01")


def executer():

    cohorte = pd.read_csv(COHORTE)

    if len(cohorte) != 40:
        raise RuntimeError(
            f"40 titres attendus, {len(cohorte)} obtenus."
        )

    evenements = []

    for _, ligne in cohorte.iterrows():

        ticker = str(
            ligne["Ticker_cotation"]
        ).strip()

        id_ligne = ligne["ID_ligne"]
        societe = ligne["Societe"]
        devise = ligne["Devise"]

        try:

            h = yf.Ticker(ticker).history(
                start="2026-10-01",
                auto_adjust=False,
                actions=True
            )

            if len(h) == 0:
                continue

            # ------------------------------------------------
            # Normaliser les dates sans dépendre du fuseau
            # ------------------------------------------------

            dates = pd.to_datetime(h.index)

            if getattr(dates, "tz", None) is not None:
                dates = dates.tz_localize(None)

            h = h.copy()
            h["DATE_EVENT"] = dates

            # ------------------------------------------------
            # DIVIDENDES
            # ------------------------------------------------

            if "Dividends" in h.columns:

                div = pd.to_numeric(
                    h["Dividends"],
                    errors="coerce"
                ).fillna(0)

                for pos in range(len(h)):

                    montant = float(div.iloc[pos])
                    date_evt = pd.Timestamp(
                        h["DATE_EVENT"].iloc[pos]
                    ).normalize()

                    if (
                        montant != 0
                        and date_evt >= T0
                    ):

                        evenements.append({
                            "ID_ligne": id_ligne,
                            "Societe": societe,
                            "Ticker": ticker,
                            "Devise": devise,
                            "Date_evenement": str(
                                date_evt.date()
                            ),
                            "Type_evenement": "DIVIDENDE",
                            "Valeur_evenement": montant,
                            "Statut_traitement":
                                "DETECTE_NON_APPLIQUE",
                            "Source": "YAHOO_YFINANCE"
                        })

            # ------------------------------------------------
            # SPLITS
            # ------------------------------------------------

            if "Stock Splits" in h.columns:

                splits = pd.to_numeric(
                    h["Stock Splits"],
                    errors="coerce"
                ).fillna(0)

                for pos in range(len(h)):

                    facteur = float(
                        splits.iloc[pos]
                    )

                    date_evt = pd.Timestamp(
                        h["DATE_EVENT"].iloc[pos]
                    ).normalize()

                    if (
                        facteur != 0
                        and date_evt >= T0
                    ):

                        evenements.append({
                            "ID_ligne": id_ligne,
                            "Societe": societe,
                            "Ticker": ticker,
                            "Devise": devise,
                            "Date_evenement": str(
                                date_evt.date()
                            ),
                            "Type_evenement": "SPLIT",
                            "Valeur_evenement": facteur,
                            "Statut_traitement":
                                "DETECTE_NON_APPLIQUE",
                            "Source": "YAHOO_YFINANCE"
                        })

        except Exception as e:

            raise RuntimeError(
                f"Erreur actions corporatives "
                f"{ticker} : {e}"
            )

    colonnes = [
        "ID_ligne",
        "Societe",
        "Ticker",
        "Devise",
        "Date_evenement",
        "Type_evenement",
        "Valeur_evenement",
        "Statut_traitement",
        "Source"
    ]

    resultat = pd.DataFrame(
        evenements,
        columns=colonnes
    )

    if len(resultat):

        resultat = resultat.sort_values(
            [
                "Date_evenement",
                "ID_ligne",
                "Type_evenement"
            ]
        ).reset_index(drop=True)

        doublons = resultat.duplicated(
            subset=[
                "ID_ligne",
                "Date_evenement",
                "Type_evenement",
                "Valeur_evenement"
            ]
        )

        if doublons.any():
            raise RuntimeError(
                "Événement corporate dupliqué."
            )

    # écriture atomique
    tmp = OUTPUT.with_suffix(".tmp")

    resultat.to_csv(
        tmp,
        index=False
    )

    tmp.replace(OUTPUT)

    print("=" * 92)
    print("🏢 MICRO CAPS — ACTIONS CORPORATIVES POST-T0")
    print("=" * 92)

    print("Événements détectés :", len(resultat))

    if len(resultat):

        print(
            "Dividendes :",
            (
                resultat["Type_evenement"]
                == "DIVIDENDE"
            ).sum()
        )

        print(
            "Splits     :",
            (
                resultat["Type_evenement"]
                == "SPLIT"
            ).sum()
        )

        print()
        print(
            resultat.to_string(
                index=False
            )
        )

    else:

        print(
            "Aucun dividende ou split post-T0 "
            "détecté à ce stade."
        )

    print()
    print("Fichier TEST :", OUTPUT)
    print()
    print("⚠️ Événements détectés mais NON appliqués.")
    print("🔒 Aucun cash crédité")
    print("🔒 Aucune quantité modifiée")
    print("🔒 T0 inchangé")

    return resultat


if __name__ == "__main__":
    executer()


# ============================================================
# RÈGLE ÉCONOMIQUE ACTIONS CORPORATIVES — V2
# FIGÉE OCTOBRE 2026
# ============================================================
#
# Principe général :
# simplicité maximale compatible avec une mesure pertinente.
#
# DIVIDENDE
# ----------
# Tout dividende postérieur au T0 détecté sur une position
# détenue est automatiquement réinvesti à 100 % dans le même
# titre.
#
# Les fractions de titre sont autorisées.
#
# Formule :
#
# dividende_recu_devise =
#     quantite_detenue * dividende_par_action
#
# quantite_supplementaire =
#     dividende_recu_devise / cours_reinvestissement_devise
#
# Aucun cash dividende dormant.
# Aucun arbitrage provoqué par le dividende.
#
# La règle est identique pour :
# - le portefeuille témoin
# - le portefeuille géré
#
# Une valeur sortie du portefeuille géré ne bénéficie plus des
# dividendes futurs dans le portefeuille géré.
#
# Le témoin conserve ses positions et continue donc naturellement
# à bénéficier de leurs dividendes.
#
#
# SPLIT
# -----
# quantite_economique_apres =
#     quantite_economique_avant * facteur_split
#
# Aucun changement artificiel de valeur économique.
#
#
# T0
# --
# Le fichier T0 gelé reste strictement immuable.
# Les ajustements sont portés uniquement par des quantités
# économiques dérivées.
#
#
# BIAIS ACCEPTÉ
# -------------
# La convention simplifiée de réinvestissement peut introduire
# un écart marginal par rapport à une comptabilité exacte des
# dates de détachement/paiement.
#
# Ce biais est accepté car :
# - les dividendes sont secondaires dans cet univers de croissance
# - la règle est symétrique témoin/géré
# - elle évite une complexité disproportionnée
# - elle reste stable et reproductible
#
# ============================================================

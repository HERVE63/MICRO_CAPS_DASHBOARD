
from pathlib import Path
import pandas as pd
import numpy as np
import importlib.util

BASE = Path(__file__).resolve().parent.parent

SRC = BASE / "SCRIPTS_ACTIFS"

RESOLU = BASE / "DONNEES/TEST_MOTEUR_RESOLU_V3.csv"

SCRIPT_05C = SRC / "05C_REPLAY_PORTEFEUILLE_GERE.py"

OUTPUT = BASE / "DONNEES/TEST_PORTEFEUILLES_V3.csv"


def norm_id(x):
    if pd.isna(x):
        return None
    try:
        return str(int(float(x)))
    except Exception:
        return str(x).strip()


def charger_05c():

    spec = importlib.util.spec_from_file_location(
        "replay_gere_05",
        SCRIPT_05C
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    resultat = module.executer()

    if not isinstance(resultat, dict):
        raise RuntimeError(
            "05C n'a pas retourné un dictionnaire."
        )

    for cle in [
        "positions",
        "cash",
        "nb_actives",
        "nb_sorties"
    ]:
        if cle not in resultat:
            raise RuntimeError(
                f"Clé absente du résultat 05C : {cle}"
            )

    return resultat


def executer():

    # ========================================================
    # 1. PRIX ÉCONOMIQUES DU TÉMOIN
    # ========================================================

    prix = pd.read_csv(RESOLU)

    if len(prix) != 40:
        raise RuntimeError(
            f"04B : 40 lignes attendues, {len(prix)} obtenues."
        )

    if prix["ID_ligne"].nunique() != 40:
        raise RuntimeError(
            "IDs 04B non uniques."
        )

    prix["CLE_T0"] = prix["ID_ligne"].map(norm_id)

    if prix["CLE_T0"].duplicated().any():
        raise RuntimeError(
            "Clés T0 normalisées dupliquées."
        )

    # ========================================================
    # 2. TÉMOIN
    # ========================================================

    prix["Valeur_Temoin_EUR"] = pd.to_numeric(
        prix["Valeur_EUR_resolue"],
        errors="coerce"
    )

    if prix["Valeur_Temoin_EUR"].isna().any():
        raise RuntimeError(
            "Valeur témoin manquante."
        )

    total_temoin = float(
        prix["Valeur_Temoin_EUR"].sum()
    )

    # ========================================================
    # 3. COMPTABILITÉ DU GÉRÉ VIA 05C
    # ========================================================

    resultat_05c = charger_05c()

    positions = resultat_05c["positions"].copy()
    cash = float(resultat_05c["cash"])

    if cash < -1e-8:
        raise RuntimeError(
            "Cash 05C négatif."
        )

    actifs = positions[
        positions["Statut"].astype(str).str.upper()
        == "ACTIF"
    ].copy()

    # ========================================================
    # 4. V2 FAIL-CLOSED SUR LES NOUVELLES POSITIONS
    # ========================================================

    nouvelles = actifs[
        actifs["ID_position"]
        .astype(str)
        .str.startswith("NEW_")
    ]

    if len(nouvelles) > 0:
        raise RuntimeError(
            "Position(s) NEW_ détectée(s). "
            "Le moteur prix des challengers n'est pas encore "
            "branché : valorisation officielle bloquée."
        )

    if actifs["ID_origine_T0"].isna().any():
        raise RuntimeError(
            "Position active sans ID_origine_T0. "
            "Valorisation bloquée."
        )

    actifs["CLE_T0"] = (
        actifs["ID_origine_T0"].map(norm_id)
    )

    if actifs["CLE_T0"].duplicated().any():
        raise RuntimeError(
            "Plusieurs positions actives utilisent "
            "le même ID_origine_T0."
        )

    # ========================================================
    # 5. RACCORDEMENT POSITIONS ↔ PRIX
    # ========================================================

    gere = actifs.merge(
        prix[
            [
                "CLE_T0",
                "ID_ligne",
                "Ticker_cotation",
                "Date_cloture",
                "Cours_retenu_devise",
                "FX_vers_EUR",
                "Cours_EUR_resolu",
                "Resolution_anomalie"
            ]
        ],
        on="CLE_T0",
        how="left",
        validate="one_to_one"
    )

    if gere["Cours_EUR_resolu"].isna().any():
        ids = gere.loc[
            gere["Cours_EUR_resolu"].isna(),
            "ID_position"
        ].astype(str).tolist()

        raise RuntimeError(
            f"Prix absent pour position(s) active(s) : {ids}"
        )

    ticker_ok = (
        gere["Ticker"].astype(str).str.strip().str.upper()
        ==
        gere["Ticker_cotation"]
        .astype(str).str.strip().str.upper()
    )

    if not ticker_ok.all():
        raise RuntimeError(
            "Discordance ticker entre 05C et 04B."
        )

    gere["Quantite"] = pd.to_numeric(
        gere["Quantite"],
        errors="coerce"
    )

    gere["Cours_EUR_resolu"] = pd.to_numeric(
        gere["Cours_EUR_resolu"],
        errors="coerce"
    )

    if (
        gere["Quantite"].isna().any()
        or gere["Cours_EUR_resolu"].isna().any()
    ):
        raise RuntimeError(
            "Quantité ou cours EUR invalide."
        )

    if (gere["Quantite"] < 0).any():
        raise RuntimeError(
            "Quantité active négative."
        )

    # ========================================================
    # 6. VALORISATION GÉRÉE
    # ========================================================

    gere["Valeur_Gere_EUR"] = (
        gere["Quantite"]
        * gere["Cours_EUR_resolu"]
    )

    total_gere_titres = float(
        gere["Valeur_Gere_EUR"].sum()
    )

    total_gere = (
        total_gere_titres + cash
    )

    # ========================================================
    # 7. PERFORMANCE PORTEFEUILLES
    # ========================================================

    capital_depart = 4000.0

    perf_temoin = (
        total_temoin / capital_depart - 1
    ) * 100

    perf_gere = (
        total_gere / capital_depart - 1
    ) * 100

    alpha_gestion = (
        perf_gere - perf_temoin
    )

    # ========================================================
    # 8. TABLEAU DE SORTIE
    #
    # Une ligne par titre T0 :
    # témoin toujours présent ;
    # géré = valeur active ou 0 si sorti.
    # ========================================================

    sortie = prix.copy()

    map_valeur_gere = dict(
        zip(
            gere["CLE_T0"],
            gere["Valeur_Gere_EUR"]
        )
    )

    map_statut_gere = dict(
        zip(
            gere["CLE_T0"],
            gere["Statut"]
        )
    )

    sortie["Valeur_Gere_EUR"] = (
        sortie["CLE_T0"]
        .map(map_valeur_gere)
        .fillna(0.0)
    )

    sortie["Statut_Temoin"] = "ACTIF"

    sortie["Statut_Gere"] = (
        sortie["CLE_T0"]
        .map(map_statut_gere)
        .fillna("SORTI")
    )

    sortie["Perf_Temoin_pct"] = (
        sortie["Valeur_Temoin_EUR"]
        / sortie["Capital_T0_EUR"]
        - 1
    ) * 100

    # Performance ligne gérée :
    # informative uniquement tant qu'il n'y a pas de flux.
    # La performance officielle du géré est celle du portefeuille.
    sortie["Perf_Gere_pct"] = np.nan

    # Métadonnées portefeuille répétées pour compatibilité
    sortie["Cash_Gere_EUR"] = cash
    sortie["Total_Gere_Titres_EUR"] = total_gere_titres
    sortie["Total_Gere_EUR"] = total_gere
    sortie["Total_Temoin_EUR"] = total_temoin
    sortie["Perf_Gere_Portefeuille_pct"] = perf_gere
    sortie["Perf_Temoin_Portefeuille_pct"] = perf_temoin
    sortie["Alpha_Gestion_points"] = alpha_gestion

    # ========================================================
    # 9. ÉCRITURE ATOMIQUE
    # ========================================================

    tmp = OUTPUT.with_suffix(".tmp")

    sortie.to_csv(
        tmp,
        index=False
    )

    tmp.replace(OUTPUT)

    # ========================================================
    # 10. AFFICHAGE
    # ========================================================

    print("=" * 92)
    print("📊 MICRO CAPS — PORTEFEUILLES V2")
    print("=" * 92)

    print(
        f"Témoin       : {total_temoin:.6f} € "
        f"| {perf_temoin:+.6f}%"
    )

    print(
        f"Géré titres  : {total_gere_titres:.6f} €"
    )

    print(
        f"Cash géré    : {cash:.6f} €"
    )

    print(
        f"Géré total   : {total_gere:.6f} € "
        f"| {perf_gere:+.6f}%"
    )

    print(
        f"Alpha gestion: {alpha_gestion:+.10f} point"
    )

    print(
        "Positions gérées actives :",
        len(gere)
    )

    print(
        "Positions archivées :",
        int(resultat_05c["nb_sorties"])
    )

    print()
    print("Fichier TEST :", OUTPUT)

    return {
        "tableau": sortie,
        "positions_gerees": gere,
        "cash": cash,
        "total_temoin": total_temoin,
        "total_gere_titres": total_gere_titres,
        "total_gere": total_gere,
        "perf_temoin": perf_temoin,
        "perf_gere": perf_gere,
        "alpha_gestion": alpha_gestion
    }


if __name__ == "__main__":
    executer()

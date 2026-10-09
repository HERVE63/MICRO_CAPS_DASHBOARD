
# -*- coding: utf-8 -*-

"""
MICRO CAPS — EXECUTION QUOTIDIENNE V3

Orchestrateur strict.

Aucune logique métier n'est dupliquée ici.

Une étape en erreur arrête immédiatement toute la chaîne.
"""

from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent.parent

SRC = BASE / "SCRIPTS_ACTIFS"

ETAPES = [
    ("T0", "Intégrité des références figées", SRC / "07AC_CONTROLER_T0.py"),

    (
        "03",
        "Clôtures + FX",
        SRC / "03_MOTEUR_CLOTURES_FX.py"
    ),

    (
        "03C",
        "Actions corporatives",
        SRC / "03C_ACTIONS_CORPORATIVES.py"
    ),

    (
        "04",
        "Contrôle qualité",
        SRC / "04_CONTROLE_QUALITE.py"
    ),

    (
        "04B",
        "Résolution économique",
        SRC / "04B_MOTEUR_ECONOMIQUE_RESOLU.py"
    ),

    (
        "05",
        "Portefeuilles",
        SRC / "05_MOTEUR_PORTEFEUILLES.py"
    ),

    (
        "06",
        "Benchmarks",
        SRC / "06_BENCHMARKS.py"
    ),

    (
        "07B",
        "Historique officiel",
        SRC / "07B_AJOUT_HISTORIQUE.py"
    ),
]


def executer_script(code_etape, libelle, chemin):

    print()
    print("=" * 96)
    print(
        f"▶ ÉTAPE {code_etape} — {libelle}"
    )
    print("=" * 96)

    if not chemin.exists():
        raise RuntimeError(
            f"Script absent : {chemin}"
        )

    r = subprocess.run(
        [sys.executable, str(chemin)],
        capture_output=True,
        text=True
    )

    if r.stdout:
        print(r.stdout)

    if r.stderr:
        print("STDERR :")
        print(r.stderr)

    if r.returncode != 0:

        print()
        print(
            f"⛔ CHAÎNE ARRÊTÉE À L'ÉTAPE "
            f"{code_etape}"
        )

        raise RuntimeError(
            f"Échec {code_etape} — {libelle}"
        )

    print(
        f"✅ ÉTAPE {code_etape} TERMINÉE"
    )


def executer():

    debut = datetime.now(timezone.utc)

    print("=" * 96)
    print("🚀 MICRO CAPS — EXÉCUTION QUOTIDIENNE V3")
    print("=" * 96)

    print(
        "Début UTC :",
        debut.isoformat()
    )

    print(
        "Nombre d'étapes :",
        len(ETAPES)
    )

    # --------------------------------------------------------
    # Précontrôle : tous les scripts doivent exister
    # AVANT de lancer la première étape.
    # --------------------------------------------------------

    absents = [
        str(path)
        for _, _, path in ETAPES
        if not path.exists()
    ]

    if absents:
        raise RuntimeError(
            "Scripts absents avant démarrage :\n"
            + "\n".join(absents)
        )

    # --------------------------------------------------------
    # Exécution séquentielle stricte
    # --------------------------------------------------------

    for code_etape, libelle, chemin in ETAPES:

        executer_script(
            code_etape,
            libelle,
            chemin
        )

    fin = datetime.now(timezone.utc)

    duree = (
        fin - debut
    ).total_seconds()

    print()
    print("=" * 96)
    print("🏁 CHAÎNE QUOTIDIENNE TERMINÉE")
    print("=" * 96)

    print(
        "Fin UTC   :",
        fin.isoformat()
    )

    print(
        f"Durée      : {duree:.2f} secondes"
    )

    print()
    print("🔒 T0 jamais modifié par l'orchestrateur")
    print("🔒 CPI / ETF hors périmètre")

    return True


if __name__ == "__main__":
    executer()

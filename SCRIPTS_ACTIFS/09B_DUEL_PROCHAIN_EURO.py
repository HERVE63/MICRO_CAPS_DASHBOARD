# -*- coding: utf-8 -*-
"""
MICRO CAPS — 09B DUEL DU PROCHAIN EURO

Règles validées :
- aucune rotation sur égalité avec la valeur détenue ;
- une destination doit avoir une note MCPA strictement supérieure à la source ;
- seules les sorties VENDRE libèrent automatiquement du capital ;\n- destinations admissibles : titulaire RENFORCER ou challenger SONDE/INCUBATION ;
- si plusieurs meilleures destinations ont la même note, partage équipondéré ;
- aucune écriture dans le journal : 09B décide l'allocation, l'exécution reste
  séparée afin que prix, FX, frais et quantités soient documentés.
"""
from pathlib import Path
import importlib.util
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SCRIPT = BASE / "SCRIPTS_ACTIFS" / "09_CONTROLE_REVUE_MCPA_IPS.py"
OUTPUT = BASE / "DONNEES" / "DUELS_PROCHAIN_EURO.csv"

DEST_TITULAIRE = {"RENFORCER"}
DEST_CHALLENGER = {"SONDE", "INCUBATION"}
SORTIES = {"VENDRE"}

def _s(v):
    return str(v).strip().upper()

def calculer_duels(df):
    if df.empty:
        raise RuntimeError("Revue vide.")

    d = df.copy()
    d["Type_N"] = d["Type"].map(_s)
    d["Decision_N"] = d["Decision"].map(_s)
    d["MCPA_N"] = pd.to_numeric(d["MCPA"], errors="raise")

    titulaires = d[d["Type_N"] == "TITULAIRE"]
    challengers = d[d["Type_N"] == "CHALLENGER"]
    if titulaires.empty:
        raise RuntimeError("Aucune titulaire dans la revue.")

    sources = titulaires[titulaires["Decision_N"].isin(SORTIES)]
    destinations = d[
        ((d["Type_N"] == "TITULAIRE") & d["Decision_N"].isin(DEST_TITULAIRE))
        | ((d["Type_N"] == "CHALLENGER") & d["Decision_N"].isin(DEST_CHALLENGER))
    ].copy()

    rows = []
    for _, src in sources.iterrows():
        note_source = float(src["MCPA_N"])
        comparaison = str(src["Challengers_compares"]).strip()
        if not comparaison:
            raise RuntimeError(f"Comparaison manquante pour {src['Societe']}.")

        if destinations.empty:
            rows.append({
                "ID_position_source": src["ID_position"],
                "Societe_source": src["Societe"],
                "Decision_source": src["Decision"],
                "MCPA_source": note_source,
                "ID_position_destination": "CASH",
                "Societe_destination": "CASH",
                "Type_destination": "CASH",
                "MCPA_destination": pd.NA,
                "Part_allocation": 1.0,
                "Regle_decision": "AUCUNE_DESTINATION_ADMISSIBLE",
                "Statut_duel": "CASH"
            })
            continue

        meilleure = float(destinations["MCPA_N"].max())

        # Règle utilisateur : égalité (ou absence de supériorité) => statu quo.
        if meilleure <= note_source:
            rows.append({
                "ID_position_source": src["ID_position"],
                "Societe_source": src["Societe"],
                "Decision_source": src["Decision"],
                "MCPA_source": note_source,
                "ID_position_destination": src["ID_position"],
                "Societe_destination": src["Societe"],
                "Type_destination": "STATU_QUO",
                "MCPA_destination": note_source,
                "Part_allocation": 1.0,
                "Regle_decision": "EGALITE_OU_NOTE_INFERIEURE_STAUT_QUO",
                "Statut_duel": "CONSERVER"
            })
            continue

        champions = destinations[destinations["MCPA_N"] == meilleure].copy()
        part = 1.0 / len(champions)
        for _, dst in champions.iterrows():
            rows.append({
                "ID_position_source": src["ID_position"],
                "Societe_source": src["Societe"],
                "Decision_source": src["Decision"],
                "MCPA_source": note_source,
                "ID_position_destination": dst["ID_position"],
                "Societe_destination": dst["Societe"],
                "Type_destination": dst["Type_N"],
                "MCPA_destination": meilleure,
                "Part_allocation": part,
                "Regle_decision": (
                    "MEILLEUR_STRICT_UNIQUE" if len(champions) == 1
                    else "MEILLEURS_EX_AEQUO_PARTAGE_EQUIPONDERE"
                ),
                "Statut_duel": "ALLOCATION_DETERMINEE"
            })

    cols = [
        "ID_position_source","Societe_source","Decision_source","MCPA_source",
        "ID_position_destination","Societe_destination","Type_destination",
        "MCPA_destination","Part_allocation","Regle_decision","Statut_duel"
    ]
    return pd.DataFrame(rows, columns=cols)

def executer():
    spec = importlib.util.spec_from_file_location("controle_revue", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    df = module.executer().copy()
    guard_path=BASE/"SCRIPTS_ACTIFS/08B_CONTROLE_CHASSE_SSI.py"
    gs=importlib.util.spec_from_file_location("controle_ssi_duel",guard_path)
    gm=importlib.util.module_from_spec(gs);gs.loader.exec_module(gm);gm.executer()
    out = calculer_duels(df)
    out.to_csv(OUTPUT, index=False)
    print("Duels calcules :", len(out))
    print("Regles d'egalite et partage ex-aequo appliquees.")
    return out

if __name__ == "__main__":
    executer()

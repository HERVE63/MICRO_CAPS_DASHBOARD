# -*- coding: utf-8 -*-
"""Collecte incrémentale de fondamentaux observables (NON preuves SSI).

Ne fabrique ni note ni admission. Chaque passage choisit les tickers absents
puis les plus anciens, conserve les dernières valeurs datées en cas d'échec
réseau, et écrit un audit de toutes les tentatives. Exécution réentrante.
"""
from datetime import datetime, timezone
from pathlib import Path
import os
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
COLS = ["Date_scan", "Ticker", "CA_TTM", "Croissance_CA", "Marge_brute",
        "EBITDA", "FCF", "Cash", "Dette_totale", "Dette_nette", "Actions",
        "Insiders_pct", "Source_fondamentaux", "Statut_fondamentaux",
        "Date_derniere_tentative_UTC", "Statut_derniere_tentative"]
CORRESPONDANCE = {
    "CA_TTM": ("totalRevenue",),
    "Croissance_CA": ("revenueGrowth",),
    "Marge_brute": ("grossMargins",),
    "EBITDA": ("ebitda",),
    "FCF": ("freeCashflow",),
    "Cash": ("totalCash",),
    "Dette_totale": ("totalDebt",),
    "Dette_nette": ("netDebt",),
    "Actions": ("sharesOutstanding",),
    "Insiders_pct": ("heldPercentInsiders",),
}
INDISPENSABLES = ("CA_TTM", "Cash", "Dette_totale", "Actions", "Insiders_pct")


def _lire(path, colonnes=None):
    if not path.exists():
        return pd.DataFrame(columns=colonnes or [])
    return pd.read_csv(path, dtype={"Ticker": str}, keep_default_na=False)


def _atomique(df, path):
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        df.to_csv(tmp, index=False)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def executer(base=None, fetcher=None, taille_lot=None, instant=None):
    base = Path(base) if base is not None else BASE
    d = base / "DONNEES"
    u = _lire(d / "UNIVERS_PRET_FILTRES_OBJECTIFS.csv")
    if not {"Ticker", "Admissible_filtre_marche"}.issubset(u.columns):
        raise RuntimeError("Univers préfiltré absent ou schéma invalide")
    if u.empty or u.Ticker.duplicated().any():
        raise RuntimeError("Univers vide ou tickers dupliqués")
    anciens = _lire(d / "FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv", COLS)
    if "Ticker" not in anciens or anciens.Ticker.duplicated().any():
        raise RuntimeError("Registre fondamentaux dupliqué ou invalide")
    for col in COLS:
        if col not in anciens:
            anciens[col] = ""
    anciens = anciens[COLS].copy()
    eligibles = sorted(set(u.loc[u.Admissible_filtre_marche.eq("OUI"), "Ticker"]
                           .astype(str).str.strip()) - {""})
    if not eligibles:
        raise RuntimeError("Aucun ticker admissible au préfiltrage")
    if taille_lot is None:
        taille_lot = int(os.environ.get("MICRO_CAPS_FONDAMENTAUX_BATCH_SIZE", "100"))
    if not 1 <= taille_lot <= 500:
        raise ValueError("Lot fondamentaux hors intervalle 1..500")
    instant = instant or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("Horodatage UTC requis")
    date = instant.date().isoformat()
    iso = instant.astimezone(timezone.utc).isoformat()
    # pandas 3.x infere StringDtype sur les colonnes historiques mixtes ;
    # utiliser object permet de conserver les nombres verifies sans erreur de typage.
    index = anciens.set_index("Ticker", drop=False).astype(object)
    # Les tentatives du jour ne sont pas répétées : on évite une boucle infinie
    # sur des sources indisponibles et l'épuisement du fournisseur.
    attente = []
    for t in eligibles:
        if t not in index.index:
            attente.append((0, "", t))
            continue
        r = index.loc[t]
        tentative = str(r.get("Date_derniere_tentative_UTC", "")).strip()
        if tentative.startswith(date):
            continue
        dernier = str(r.get("Date_scan", "")).strip()
        attente.append((1, dernier, t))
    attente.sort()
    selection = [t for _, _, t in attente[:taille_lot]]
    if fetcher is None:
        import yfinance as yf
        fetcher = lambda ticker: yf.Ticker(ticker).get_info()
    audit = []
    for t in selection:
        ancien = index.loc[t].to_dict() if t in index.index else {c: "" for c in COLS}
        nouveau = dict(ancien)
        nouveau["Ticker"] = t
        nouveau["Date_derniere_tentative_UTC"] = iso
        statut = "ERREUR_SOURCE"
        motif = ""
        try:
            info = fetcher(t)
            if not isinstance(info, dict) or not info:
                raise RuntimeError("Réponse fournisseur absente")
            valeurs = {}
            for champ, clefs in CORRESPONDANCE.items():
                valeur = next((info[k] for k in clefs if info.get(k) is not None), None)
                if valeur is None:
                    valeurs[champ] = ""
                else:
                    valeur = float(valeur)
                    if not pd.notna(valeur) or not float("-inf") < valeur < float("inf"):
                        raise ValueError("Valeur numérique non finie: " + champ)
                    valeurs[champ] = valeur
            if not any(valeurs[c] != "" for c in CORRESPONDANCE):
                raise RuntimeError("Aucune variable financière utilisable")
            nouveau.update(valeurs)
            nouveau["Date_scan"] = date
            nouveau["Source_fondamentaux"] = "Yahoo Finance / yfinance get_info"
            complet = all(valeurs[c] != "" for c in INDISPENSABLES)
            statut = "OK" if complet else "PARTIELLE"
            nouveau["Statut_fondamentaux"] = statut
        except Exception as exc:
            motif = type(exc).__name__ + ": " + str(exc)[:240]
            # En cas d'échec, ne jamais transformer l'ancien relevé en
            # nouvelle observation ; sa date et ses valeurs restent intactes.
            if t not in index.index:
                nouveau["Statut_fondamentaux"] = "MANQUANTE"
        nouveau["Statut_derniere_tentative"] = statut
        index.loc[t, COLS] = [nouveau.get(c, "") for c in COLS]
        audit.append({"Date_tentative_UTC": iso, "Ticker": t,
                      "Statut": statut, "Motif": motif,
                      "Date_derniere_observation": nouveau.get("Date_scan", "")})
    out = index.reset_index(drop=True)
    if out.Ticker.duplicated().any():
        raise RuntimeError("Doublon créé par la collecte")
    _atomique(out[COLS], d / "FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv")
    _atomique(pd.DataFrame(audit, columns=[
        "Date_tentative_UTC", "Ticker", "Statut", "Motif",
        "Date_derniere_observation"]), d / "AUDIT_TENTATIVES_FONDAMENTAUX.csv")
    synthese = pd.DataFrame([{
        "Date_UTC": iso, "Univers_eligible": len(eligibles),
        "Lot_tente": len(selection),
        "Observations_completes": sum(x["Statut"] == "OK" for x in audit),
        "Observations_partielles": sum(x["Statut"] == "PARTIELLE" for x in audit),
        "Erreurs_source": sum(x["Statut"] == "ERREUR_SOURCE" for x in audit),
        "En_attente_apres_lot": len(attente) - len(selection),
        "SSI_calcule": "NON", "Notes_attribuees": 0,
    }])
    _atomique(synthese, d / "AUDIT_FONDAMENTAUX_INCREMENTAL.csv")
    print(synthese.to_json(orient="records", force_ascii=False))
    return synthese


if __name__ == "__main__":
    executer()

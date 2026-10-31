"""Contrôle de conservation du registre historique, sans réseau ni écriture."""
from pathlib import Path
import hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "DONNEES"


def executer():
    p = D / "CHASSE_CANDIDATS.csv"
    s = D / "SORTIE_SCREENER_CANDIDATS.csv"
    c = D / "CONTROLE_IMPORT_SCREENER.csv"
    assert p.stat().st_size > 5_000_000, "Registre historique tronque"
    a = pd.read_csv(p, dtype=str, keep_default_na=False)
    b = pd.read_csv(s, dtype=str, keep_default_na=False)
    audit = pd.read_csv(c)
    champs = {"Date_detection", "Societe", "Ticker", "Devise", "Pays",
              "Source_detection", "Date_source", "These_initiale", "Statut_chasse"}
    assert champs.issubset(a.columns) and champs.issubset(b.columns)
    assert len(a) == 31352, f"Historique incomplet: {len(a)} au lieu de 31352"
    assert len(b) == 5737, f"Sortie screener inattendue: {len(b)}"
    ak = set(zip(a.Ticker, a.Date_detection))
    bk = set(zip(b.Ticker, b.Date_detection))
    assert len(ak) == len(a), "Doublons ticker/date dans le registre"
    assert bk.issubset(ak), "Détections actuelles absentes de l'historique"
    assert a[list(champs)].astype(str).apply(lambda x: x.str.strip().ne("")).all().all()
    assert int(audit.Nb_entree.iloc[0]) == len(b)
    assert int(audit.Nb_registre_apres_import.iloc[0]) == len(a)
    assert audit.Statut.iloc[0] == "OK"
    print("REGISTRE HISTORIQUE OK :",
          len(a), "détections, dont", len(b), "du screener actuel.",
          "SHA256:", hashlib.sha256(p.read_bytes()).hexdigest())


if __name__ == "__main__":
    executer()

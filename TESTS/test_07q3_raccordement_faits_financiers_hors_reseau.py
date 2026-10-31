"""Tests adverses hors réseau du raccordement 07Q3, sur copie temporaire."""
from pathlib import Path
import csv
import hashlib
import importlib.util
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "SCRIPTS_ACTIFS/07Q3_RACCORDER_FAITS_FINANCIERS_NON_CERTIFIES.py"
CAPTURES = ("20261031T103236976336Z", "20261031T120058499540Z")


def lire(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ecrire(path, lignes):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)


def test():
    spec = importlib.util.spec_from_file_location("raccordement_financier_isole", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    with tempfile.TemporaryDirectory() as t:
        b = Path(t)
        (b / "DONNEES").mkdir()
        (b / "AUDITS/REPARATION").mkdir(parents=True)
        (b / "AUDITS/SOURCES_OFFICIELLES").mkdir(parents=True)
        with (b / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=("Ticker", "Identifiant_emetteur_verifie"))
            w.writeheader()
            w.writerows([
                {"Ticker": "Z8J.F", "Identifiant_emetteur_verifie": "ISIN:FR001400A3Q3"},
                {"Ticker": "1F6.F", "Identifiant_emetteur_verifie": "MANQUANTE"},
            ])
        for nom in m.NOMS:
            shutil.copy2(ROOT / "AUDITS/REPARATION" / nom, b / "AUDITS/REPARATION" / nom)
        for dossier in CAPTURES:
            shutil.copytree(ROOT / "AUDITS/SOURCES_OFFICIELLES" / dossier,
                            b / "AUDITS/SOURCES_OFFICIELLES" / dossier)
        originals = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (ROOT / "AUDITS/REPARATION").glob("FAITS_FINANCIERS_*_NON_CERTIFIES.csv")}
        resultat = m.executer(b)
        assert len(resultat) == 18
        assert sum(r["Statut_raccordement"] == "PISTE_FINANCIERE_SHA256_OK_NON_CERTIFIEE" for r in resultat) == 9
        assert sum(r["Statut_raccordement"] == "EN_ATTENTE_DATA_IDENTITE" for r in resultat) == 9
        assert all(r["Note_SSI"] == r["Note_MCPA"] == "MANQUANTE" for r in resultat)
        audit = lire(b / "DONNEES/AUDIT_RACCORDEMENT_FAITS_SSI.csv")
        assert len(audit) == 1 and audit[0]["Scores_attribues"] == "0"
        # Une source corrompue ne bloque pas les autres : refus local des 9 faits ICAPE.
        brut = b / "AUDITS/SOURCES_OFFICIELLES" / CAPTURES[0] / (
            "05605e38d3a3e9778d3d8468b613752fe54ef2bbe529bd109b5c622824b0669c.bin")
        brut.write_bytes(brut.read_bytes() + b"CORRUPTION_TEST")
        resultat = m.executer(b)
        assert sum(r["Statut_raccordement"] == "EN_ATTENTE_DATA_SOURCE" for r in resultat) == 9
        assert sum(r["Statut_raccordement"] == "EN_ATTENTE_DATA_IDENTITE" for r in resultat) == 9
        # Une note injectée dans le registre factuel est refusée.
        chemin = b / "AUDITS/REPARATION" / m.NOMS[1]
        faits = lire(chemin)
        faits[0]["Note_SSI"] = "80"
        ecrire(chemin, faits)
        resultat = m.executer(b)
        assert sum(r["Statut_raccordement"] == "REJET_NOTE_OU_QUALIFICATION" for r in resultat) == 1
        assert all(r["Note_SSI"] == r["Note_MCPA"] == "MANQUANTE" for r in resultat)
        assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in originals.items())
    print("07Q3: 18 faits réutilisés, 9 pistes SHA256, 9 identités en attente; corruption et note injectée rejetées")


if __name__ == "__main__":
    test()

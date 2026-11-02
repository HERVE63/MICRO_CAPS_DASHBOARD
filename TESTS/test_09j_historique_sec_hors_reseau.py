"""09J : tests adverses hors reseau des quatre accessions SEC a revoir."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def module(nom, chemin):
    spec = importlib.util.spec_from_file_location(nom, ROOT / chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fixture_i = module("fixture_09i", "TESTS/test_09i_audit_accessions_sec_hors_reseau.py")
j = module("module_09j", "SCRIPTS_ACTIFS/09J_REVOIR_HISTORIQUE_SEC.py")


def lire(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def preparer(base):
    d = fixture_i.fixture(base)
    manifest_path = d / "MANIFESTE.json"
    mf = json.loads(manifest_path.read_text())
    sub = next(s for s in mf["Sources"] if "/submissions/" in s["URL"] and s["URL"].endswith("CIK0000001001.json"))
    ancien = d / sub["Fichier_brut"]
    obj = json.loads(ancien.read_bytes())
    obj["filings"]["files"] = [{
        "name": "CIK0000001001-submissions-001.json",
        "filingFrom": "2010-01-01", "filingTo": "2030-01-01",
    }]
    brut = json.dumps(obj, sort_keys=True).encode()
    digest = hashlib.sha256(brut).hexdigest()
    nouveau = d / "BRUTS" / (digest + ".json")
    nouveau.write_bytes(brut)
    ancien.unlink()
    mf["Fichiers_SHA256"].pop(sub["Fichier_brut"])
    mf["Fichiers_SHA256"][str(nouveau.relative_to(d))] = digest
    sub["Fichier_brut"] = str(nouveau.relative_to(d))
    sub["SHA256"] = digest
    manifest_path.write_text(json.dumps(mf))
    fixture_i.i.executer(d)
    return d


def test_replay_historique_sha256_et_zero_score():
    with TemporaryDirectory() as tmp:
        d = preparer(tmp)
        source = lire(d / "AUDIT_ACCESSIONS_09I/REVUE_ACCESSIONS_SEC_09I.csv")
        old = {r["Accession"]: r for r in source
               if r["CIK"] == "0000001001"
               and r["Statut_accession_09I"] == "EN_ATTENTE_DATA_ACCESSION_HORS_INDEX_RECENT"}
        assert old, "Fixture sans accession historique"
        appels = []
        def fetcher(url, agent):
            assert url == "https://data.sec.gov/submissions/CIK0000001001-submissions-001.json"
            appels.append(url)
            obj = {"accessionNumber": list(old),
                   "filingDate": [r["Date_depot_fait"] for r in old.values()],
                   "form": [r["Formulaire"] for r in old.values()]}
            brut = json.dumps(obj, sort_keys=True).encode()
            return obj, brut
        bilan = j.executer(d, fetcher=fetcher, agent="Test@local.invalid", pause=lambda _: None)
        assert len(appels) == 1, "Index historique a reutiliser une seule fois"
        assert bilan["Captures"] and len(bilan["Captures"]) == 1
        assert bilan["Notes_SSI"] == bilan["Notes_MCPA"] == bilan["Arbitrages"] == 0
        rows = lire(d / "AUDIT_HISTORIQUE_09J/REVUE_HISTORIQUE_SEC_09J.csv")
        assert {r["Accession"] for r in rows} >= set(old)
        for r in rows:
            assert r["Statut_preuve"] == "A_VERIFIER_IDENTITE_ET_PERIODE"
            if r["Accession"] in old:
                assert r["Statut_09J"] == "DEPOT_HISTORIQUE_RECOUPE_NON_CERTIFIANT"
                assert len(r["SHA256_source_historique"]) == 64
        for rel, digest in bilan["Fichiers_SHA256"].items():
            assert hashlib.sha256((d / "AUDIT_HISTORIQUE_09J" / rel).read_bytes()).hexdigest() == digest
        try:
            j.executer(d, fetcher=fetcher, agent="Test@local.invalid")
        except FileExistsError:
            pass
        else:
            raise AssertionError("Ecrasement de preuves interdit")


def test_echec_sec_non_bloquant():
    with TemporaryDirectory() as tmp:
        d = preparer(tmp)
        def panne(url, agent):
            raise ConnectionError("test offline")
        bilan = j.executer(d, fetcher=panne, agent="Test@local.invalid")
        assert bilan["Notes_SSI"] == bilan["Notes_MCPA"] == bilan["Arbitrages"] == 0
        assert bilan["Statuts"].get("EN_ATTENTE_DATA_SEC_ConnectionError", 0) >= 1
        assert not bilan["Captures"]


def test_empreinte_09i_invalide_refusee():
    with TemporaryDirectory() as tmp:
        d = preparer(tmp)
        p = d / "AUDIT_ACCESSIONS_09I/REVUE_ACCESSIONS_SEC_09I.csv"
        p.write_bytes(p.read_bytes() + b"\n")
        try:
            j.executer(d, fetcher=lambda *_: None, agent="Test@local.invalid")
        except ValueError as e:
            assert "SHA256" in str(e)
        else:
            raise AssertionError("09I modifie ne doit pas etre admis")
        assert not (d / "AUDIT_HISTORIQUE_09J").exists()


def test_amendement_ne_vaut_pas_validation():
    r = {"CIK": "0000001001", "Accession": "0000001001-26-000001",
         "Ticker": "IDN", "Date_depot_fait": "2026-01-01",
         "Formulaire": "10-Q", "Formulaire_submissions": "10-Q/A",
         "Statut_accession_09I": "EN_ATTENTE_DATA_FORMULAIRE_DIVERGENT"}
    lignes = j.extraire_cibles([r, dict(r, Horizon="COURANT")])
    assert len(lignes) == 1
    assert lignes[0]["Formulaire_companyfacts"] == "10-Q"
    assert lignes[0]["Formulaire_submissions"] == "10-Q/A"
    assert lignes[0]["Statut_preuve"] == "A_VERIFIER_IDENTITE_ET_PERIODE"




def test_index_historique_identite_et_dates_en_quarantaine():
    # Les metadonnees des archives sont des donnees externes non fiables.
    # Une archive d'un autre CIK ne doit jamais etre consultee.
    with TemporaryDirectory() as tmp:
        d = preparer(tmp)
        mf = json.loads((d / "MANIFESTE.json").read_text())
        sub = next(s for s in mf["Sources"] if s["URL"].endswith("/CIK0000001001.json"))
        p = d / sub["Fichier_brut"]
        obj = json.loads(p.read_bytes())
        valide = {"name": "CIK0000001001-submissions-001.json",
                  "filingFrom": "2010-01-01", "filingTo": "2030-01-01"}
        etranger = dict(valide, name="CIK0000009999-submissions-001.json")
        date_malformee = dict(valide, filingFrom="2026-99-99")
        bornes_inversees = dict(valide, filingFrom="2030-01-01", filingTo="2010-01-01")
        obj["filings"]["files"] = [etranger, date_malformee, bornes_inversees]
        brut = json.dumps(obj).encode()
        p.write_bytes(brut)
        sub["SHA256"] = hashlib.sha256(brut).hexdigest()
        urls, statut = j.extraire_fichiers_historiques(d, mf, "0000001001", "2026-01-01")
        assert urls == [] and statut == "EN_ATTENTE_DATA_INDEX_HISTORIQUE_MALFORME"
        urls, statut = j.extraire_fichiers_historiques(d, mf, "0000001001", "date-invalide")
        assert urls == [] and statut == "EN_ATTENTE_DATA_DATE_DEPOT_INVALIDE"
        obj["filings"]["files"].append(valide)
        brut = json.dumps(obj).encode()
        p.write_bytes(brut)
        sub["SHA256"] = hashlib.sha256(brut).hexdigest()
        urls, statut = j.extraire_fichiers_historiques(d, mf, "0000001001", "2026-01-01")
        assert urls == ["https://data.sec.gov/submissions/CIK0000001001-submissions-001.json"]
        assert statut == ""

if __name__ == "__main__":
    test_replay_historique_sha256_et_zero_score()
    test_echec_sec_non_bloquant()
    test_empreinte_09i_invalide_refusee()
    test_amendement_ne_vaut_pas_validation()
    test_index_historique_identite_et_dates_en_quarantaine()
    print("TEST 09J OK : archives SEC, SHA256, amendements, quarantaine, zero score")

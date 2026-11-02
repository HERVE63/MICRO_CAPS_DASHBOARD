"""09I : recoupement primaire SEC sur captures 09F/09G/09H, hors réseau."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def charger(nom, path):
    spec = importlib.util.spec_from_file_location(nom, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


h_test = charger("test_09h_fixtures", "TESTS/test_09h_audit_periodes_sec_hors_reseau.py")
i = charger("audit_09i", "SCRIPTS_ACTIFS/09I_AUDITER_ACCESSIONS_SEC.py")
ACCS = {
    "a": "0000001001-26-000001",
    "rev": "0000001001-26-000002",
    "alias": "0000001001-26-000003",
    "b": "0000001003-26-000002",
    "c": "0000001003-26-000003",
}


def ajouter_source(d, manifest, url, obj):
    raw = json.dumps(obj, sort_keys=True).encode()
    digest = hashlib.sha256(raw).hexdigest()
    rel = "BRUTS/" + digest + ".json"
    (d / rel).write_bytes(raw)
    manifest["Fichiers_SHA256"][rel] = digest
    manifest["Sources"].append({
        "URL": url, "SHA256": digest, "Fichier_brut": rel,
        "Date_collecte_UTC": manifest["Date_collecte_UTC"],
    })


def fixture(base, ambigu=False):
    d = h_test.fixture_adverse(base)
    mp = d / "MANIFESTE.json"
    manifest = json.loads(mp.read_text())
    for source in manifest["Sources"]:
        if "/companyfacts/" not in source["URL"]:
            continue
        old = d / source["Fichier_brut"]
        obj = json.loads(old.read_bytes())
        cik = str(obj["cik"]).zfill(10)
        for taxonomy in obj["facts"].values():
            for tag in taxonomy.values():
                for facts in tag["units"].values():
                    for fact in facts:
                        accn = fact.get("accn", "")
                        if accn in ACCS:
                            fact["accn"] = ACCS[accn] if cik == "0000001001" else (
                                "0000001003-26-000001" if accn == "a" else ACCS[accn])
        raw = json.dumps(obj, sort_keys=True).encode()
        digest = hashlib.sha256(raw).hexdigest()
        new = d / "BRUTS" / (digest + ".json")
        new.write_bytes(raw)
        old.unlink()
        manifest["Fichiers_SHA256"].pop(source["Fichier_brut"])
        manifest["Fichiers_SHA256"][str(new.relative_to(d))] = digest
        source["Fichier_brut"] = str(new.relative_to(d))
        source["SHA256"] = digest
    accessions = [ACCS["a"], ACCS["rev"]]
    dates = ["2026-02-20", "2026-03-14"]  # Révision : date discordante.
    forms = ["10-K", "10-K"]
    docs = ["idn10k.htm", "idn10ka.htm"]
    if ambigu:
        accessions.append(ACCS["a"])
        dates.append("2026-02-21")
        forms.append("10-Q")
        docs.append("idn10q.htm")
    ajouter_source(d, manifest,
                   "https://data.sec.gov/submissions/CIK0000001001.json",
                   {"cik": 1001, "filings": {"recent": {
                       "accessionNumber": accessions,
                       "filingDate": dates,
                       "form": forms,
                       "primaryDocument": docs,
                   }}})
    mp.write_text(json.dumps(manifest))
    h_test.g.mod.executer(d)
    h_test.h.executer(d)
    return d


def lire(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_recoupement_conservateur():
    with TemporaryDirectory() as tmp:
        d = fixture(tmp)
        m = i.executer(d)
        assert m["Statut"] == "RECOUPEMENT_DEPOTS_SEC_NON_CERTIFIANT"
        assert (m["Notes_SSI"], m["Notes_MCPA"], m["Arbitrages"]) == (0, 0, 0)
        lignes = lire(d / "AUDIT_ACCESSIONS_09I/REVUE_ACCESSIONS_SEC_09I.csv")
        assert len(lignes) == sum(x["Observations"] for x in m["Audits"].values())
        assert any(x["Statut_accession_09I"] == "DEPOT_SEC_CONCORDE_NON_CERTIFIANT"
                   and x["URL_depot_indicative_non_consultee"].startswith(
                       "https://www.sec.gov/Archives/edgar/data/1001/")
                   for x in lignes)
        assert any(x["Statut_accession_09I"] == "EN_ATTENTE_DATA_DATE_DEPOT_DIVERGENTE"
                   for x in lignes)
        assert any(x["Statut_accession_09I"] == "EN_ATTENTE_DATA_ACCESSION_HORS_INDEX_RECENT"
                   for x in lignes)
        assert all(x["Statut_preuve"] == "A_VERIFIER_IDENTITE_ET_PERIODE" for x in lignes)
        assert all(x["Date_depot_fait"] <= ("2026-10-01" if x["Horizon"] == "T0"
                                         else "2026-11-02") for x in lignes)
        for rel, digest in m["Fichiers_SHA256"].items():
            assert hashlib.sha256((d / "AUDIT_ACCESSIONS_09I" / rel).read_bytes()).hexdigest() == digest
        assert not (Path(tmp) / "DONNEES").exists()
        try:
            i.executer(d)
        except FileExistsError:
            pass
        else:
            raise AssertionError("Une revue existante ne doit pas être écrasée")


def test_accession_ambigue_isolee():
    with TemporaryDirectory() as tmp:
        d = fixture(tmp, ambigu=True)
        m = i.executer(d)
        assert m["Audits"]["T0"]["Statuts"].get("EN_ATTENTE_DATA_ACCESSION_AMBIGUE", 0) >= 1
        assert m["Notes_SSI"] == m["Notes_MCPA"] == m["Arbitrages"] == 0


def test_sources_corrompues_refusees():
    with TemporaryDirectory() as tmp:
        d = fixture(tmp)
        manifest = json.loads((d / "MANIFESTE.json").read_text())
        s = next(x for x in manifest["Sources"] if "/submissions/" in x["URL"])
        p = d / s["Fichier_brut"]
        p.write_bytes(p.read_bytes() + b"\n")
        try:
            i.executer(d)
        except ValueError as e:
            assert "SHA256" in str(e)
        else:
            raise AssertionError("Une capture SEC corrompue doit être rejetée")
        assert not (d / "AUDIT_ACCESSIONS_09I").exists()


if __name__ == "__main__":
    test_recoupement_conservateur()
    test_accession_ambigue_isolee()
    test_sources_corrompues_refusees()
    print("TEST 09I OK : accessions, dates, SHA256, PIT, quarantaine, zéro score")

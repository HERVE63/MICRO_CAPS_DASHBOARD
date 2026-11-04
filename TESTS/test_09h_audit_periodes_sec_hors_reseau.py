"""09H : adversaires SEC (révisions, alias, cumuls, SHA256), hors réseau."""
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


g = module("test_09g_fixture", "TESTS/test_09g_replay_sec_archive_hors_reseau.py")
h = module("audit_09h", "SCRIPTS_ACTIFS/09H_AUDITER_PERIODES_SEC.py")


def fixture_adverse(tmp):
    d = g.fixture(tmp)
    mpath = d / "MANIFESTE.json"
    m = json.loads(mpath.read_text())
    s = next(x for x in m["Sources"] if "0000001001" in x["URL"])
    ancien = d / s["Fichier_brut"]
    obj = json.loads(ancien.read_bytes())
    table = obj["facts"]["us-gaap"]
    facts = table["RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"]
    facts.extend([
        {"val": 105, "start": "2025-01-01", "end": "2025-12-31",
         "filed": "2026-03-15", "form": "10-K", "accn": "rev"},
        {"val": 70, "start": "2026-01-01", "end": "2026-06-30",
         "filed": "2026-08-10", "form": "10-Q", "accn": "ytd"}
    ])
    table["Revenues"] = {"units": {"USD": [{
        "val": 110, "start": "2025-01-01", "end": "2025-12-31",
        "filed": "2026-03-20", "form": "10-K", "accn": "alias"
    }]}}
    raw = json.dumps(obj, sort_keys=True).encode()
    digest = hashlib.sha256(raw).hexdigest()
    nouveau = d / "BRUTS" / (digest + ".json")
    nouveau.write_bytes(raw)
    ancien.unlink()
    m["Fichiers_SHA256"].pop(s["Fichier_brut"])
    m["Fichiers_SHA256"][str(nouveau.relative_to(d))] = digest
    s["Fichier_brut"], s["SHA256"] = str(nouveau.relative_to(d)), digest
    mpath.write_text(json.dumps(m))
    return d


def lire(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_revisions_alias_cumuls_et_replay():
    with TemporaryDirectory() as tmp:
        d = fixture_adverse(tmp)
        g.mod.executer(d)
        m = h.executer(d)
        assert m["Statut"] == "AUDIT_PERIODES_NON_CERTIFIANT"
        assert (m["Notes_SSI"], m["Notes_MCPA"], m["Arbitrages"]) == (0, 0, 0)
        lignes = lire(d / "AUDIT_PERIODES_09H/PERIODES_SEC_09H.csv")
        details = lire(d / "AUDIT_PERIODES_09H/DETAIL_CONFLITS_REVISIONS_09H.csv")
        assert details, "Les révisions doivent rester inspectables au niveau des dépôts SEC"
        assert len(details) == sum(
            x["Observations_a_revoir"] for x in m["Audits"].values())
        assert all(x["Statut_groupe"] in (
            "EN_ATTENTE_DATA_CONFLIT_ALIAS", "EN_ATTENTE_DATA_REVISION")
            and x["Statut_preuve"] == "A_VERIFIER_IDENTITE_ET_PERIODE"
            and x["SHA256_brut_SEC"] == (
                json.loads((d / "NORMALISATION_07U_07V/MANIFESTE_REPLAY.json")
                           .read_text())["Sources_reutilisees"][x["Ticker"]]["SHA256"])
            for x in details)
        assert all(x["Date_depot"] <= ("2026-10-01" if x["Horizon"] == "T0"
                                     else m["Date_collecte"]) for x in details)
        revision = [x for x in details if x["Ticker"] == "IDN"
                    and x["Fin_periode"] == "2025-12-31"
                    and x["Horizon"] == "T0"]
        assert {"100", "105", "110"}.issubset({x["Valeur"] for x in revision})
        assert {"a", "rev", "alias"}.issubset({x["Accession"] for x in revision})
        assert all(x["Ticker"] != "OSS" for x in details)
        conflit = [r for r in lignes if r["Ticker"] == "IDN"
                   and r["Fin_periode"] == "2025-12-31"
                   and r["Concept"] == "Revenues"]
        assert len(conflit) == 2
        assert all(r["Statut"] == "EN_ATTENTE_DATA_CONFLIT_ALIAS" for r in conflit)
        assert all(int(r["Nb_revisions_meme_tag"]) >= 1 for r in conflit)
        assert all(int(r["Nb_valeurs_distinctes"]) == 2 for r in conflit)
        assert any(r["Ticker"] == "OSS" and r["Statut"].startswith("PISTE_") for r in lignes)
        assert m["Audits"]["T0"]["Cumuls_intermediaires_bruts_non_convertis"] >= 1
        assert all(r["Statut"] != "CERTIFIE" for r in lignes)
        assert all(r["Date_depot_max"] <= ("2026-10-01" if r["Horizon"] == "T0"
                                           else m["Date_collecte"]) for r in lignes)
        assert set(m["Audits"]["T0"]["Titres_sans_periode"]) >= {"INFU", "CXDO", "LWAY"}
        for relatif, digest in m["Fichiers_SHA256"].items():
            p = d / "AUDIT_PERIODES_09H" / relatif
            assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
        assert not (Path(tmp) / "DONNEES").exists()
        try:
            h.executer(d)
        except FileExistsError:
            pass
        else:
            raise AssertionError("Un audit existant ne doit jamais être écrasé")


def test_tamper_refuse_avant_ecriture():
    with TemporaryDirectory() as tmp:
        d = g.fixture(tmp)
        g.mod.executer(d)
        cible = d / "NORMALISATION_07U_07V/T0/FAITS_SEC_COMPARABLES_SSI.csv"
        cible.write_bytes(cible.read_bytes() + b"\n")
        try:
            h.executer(d)
        except ValueError as e:
            assert "SHA256" in str(e)
        else:
            raise AssertionError("Le fichier SEC modifié doit être refusé")
        assert not (d / "AUDIT_PERIODES_09H").exists()


if __name__ == "__main__":
    test_revisions_alias_cumuls_et_replay()
    test_tamper_refuse_avant_ecriture()
    print("TEST 09H OK : conflits, révisions, cumuls, SHA256, PIT, zéro note")

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
    # Les montants et dates sont des faits, pas des estimations à normaliser.
    for valeur in ("113,342", "(3,904)", "-4,270", "310", "0", "1,234,567.89"):
        assert m.verifier_montant(valeur), valeur
    for valeur in ("1,2,3", "123,4", "1,000,0", "01,000", "(-12)", "NaN", "1e6", "(3,904", "3,904)"):
        assert not m.verifier_montant(valeur), valeur
    # Provenance stricte, cohérente avec 07Q2 et 07R : les fuseaux
    # non UTC, les heures absentes et les formats ambigus sont refusés.
    for date in (
        "2026-10-01T05:45:00", "2026-10-01",
        "2026-10-01T06:45:00+01:00",
        "2026-09-30T23:45:00-06:00",
        "2026-10-01T05:45:00+0000",
        "2026-10-01T05:45:00z",
        "2026-10-01T05:45Z",
        "2026-13-01T05:45:00Z",
    ):
        try:
            m.date_utc(date)
        except ValueError:
            pass
        else:
            raise AssertionError("Date de provenance ambiguë acceptée : " + date)
    assert m.date_utc("2026-10-01T05:45:00Z").isoformat() == "2026-10-01T05:45:00+00:00"
    assert m.date_utc("2026-10-01T05:45:00.123456+00:00").isoformat() == "2026-10-01T05:45:00.123456+00:00"
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
        # Couverture indicative B1/B2/B3 : 18 pistes déjà archivées,
        # mais aucune transcription vérifiée, identité SCE ou note inventée.
        couverture = lire(b / "DONNEES/COUVERTURE_OBSERVATIONS_SSI_NON_CERTIFIEES.csv")
        assert len(couverture) == 14  # deux émetteurs x sept blocs
        compte = {(x["Ticker"], x["Bloc_SSI"]): int(x["Nombre_observations_pistes"])
                  for x in couverture}
        assert [compte["Z8J.F", "B" + str(i)] for i in range(1, 8)] == [3, 5, 1, 0, 0, 0, 0]
        assert [compte["1F6.F", "B" + str(i)] for i in range(1, 8)] == [4, 3, 2, 0, 0, 0, 0]
        assert all(x["Note_SSI"] == x["Note_MCPA"] == "MANQUANTE" for x in couverture)
        assert all(x["Identite_SCE_certifiee"] == "NON"
                   and x["Transcription_chiffres_verifiee"] == "NON" for x in couverture)
        assert all(x["Nombre_documents_SHA256_distincts"] == "1"
                   for x in couverture if int(x["Nombre_observations_pistes"]) > 0)
        # Une répétition exacte du même fait ne double pas les pistes B3.
        chemin_icape = b / "AUDITS/REPARATION" / m.NOMS[0]
        faits_icape = lire(chemin_icape)
        ecrire(chemin_icape, faits_icape + [dict(faits_icape[0])])
        doublons = m.executer(b)
        assert len(doublons) == 19
        couverture = lire(b / "DONNEES/COUVERTURE_OBSERVATIONS_SSI_NON_CERTIFIEES.csv")
        assert next(x for x in couverture if x["Ticker"] == "Z8J.F" and x["Bloc_SSI"] == "B3")["Nombre_observations_pistes"] == "1"
        # Même document/tableau/ligne/période, deux montants : quarantaine
        # de toutes les variantes, sans empêcher les 16 autres faits.
        conflit = dict(faits_icape[0])
        conflit["Valeur_source"] = "999,999"
        ecrire(chemin_icape, faits_icape + [conflit])
        contradictoires = m.executer(b)
        assert len(contradictoires) == 19
        assert sum(x["Statut_raccordement"] == "EN_ATTENTE_DATA_CONFLIT_FACTUEL"
                   for x in contradictoires) == 2
        couverture = lire(b / "DONNEES/COUVERTURE_OBSERVATIONS_SSI_NON_CERTIFIEES.csv")
        assert next(x for x in couverture if x["Ticker"] == "Z8J.F" and x["Bloc_SSI"] == "B3")["Nombre_observations_pistes"] == "0"
        assert next(x for x in couverture if x["Ticker"] == "1F6.F" and x["Bloc_SSI"] == "B3")["Nombre_observations_pistes"] == "2"
        assert all(x["Note_SSI"] == x["Note_MCPA"] == "MANQUANTE" for x in contradictoires)
        ecrire(chemin_icape, faits_icape)
        # Ligne source absente : impossible de classer un fait financier.
        sans_ligne = dict(faits_icape[0])
        sans_ligne["Ligne_IFRS"] = ""
        ecrire(chemin_icape, faits_icape[1:] + [sans_ligne])
        incomplet = m.executer(b)
        assert sum(x["Statut_raccordement"] == "EN_ATTENTE_DATA_SCHEMA" for x in incomplet) == 1
        ecrire(chemin_icape, faits_icape)
        # Collision de ticker dans les dossiers SSI : aucune ligne ne doit
        # hériter silencieusement de la dernière identité rencontrée.
        dossiers_path = b / "DONNEES/DOSSIERS_SSI_A_QUALIFIER.csv"
        dossiers_originaux = lire(dossiers_path)
        ecrire(dossiers_path, dossiers_originaux + [{
            "Ticker": "Z8J.F", "Identifiant_emetteur_verifie": "ISIN:FR0011271600"
        }])
        resultat = m.executer(b)
        assert sum(r["Statut_raccordement"] == "EN_ATTENTE_DATA_IDENTITE_AMBIGUE" for r in resultat) == 9
        assert sum(r["Statut_raccordement"] == "EN_ATTENTE_DATA_IDENTITE" for r in resultat) == 9
        assert all(r["Note_SSI"] == r["Note_MCPA"] == "MANQUANTE" for r in resultat)
        # Une identité dupliquée même identique reste en quarantaine.
        ecrire(dossiers_path, dossiers_originaux + [dict(dossiers_originaux[0])])
        resultat = m.executer(b)
        assert sum(r["Statut_raccordement"] == "EN_ATTENTE_DATA_IDENTITE_AMBIGUE" for r in resultat) == 9
        ecrire(dossiers_path, dossiers_originaux)
        # Un seul fait à horodatage non UTC reste EN_ATTENTE_DATA_DATES,
        # sans bloquer les 17 autres faits ni publier de note.
        dates_non_utc = [dict(x) for x in faits_icape]
        dates_non_utc[0]["Date_collecte_UTC"] = "2026-10-31T11:32:36.976336+01:00"
        ecrire(chemin_icape, dates_non_utc)
        controle_dates = m.executer(b)
        assert len(controle_dates) == 18
        assert sum(x["Statut_raccordement"] == "EN_ATTENTE_DATA_DATES"
                   for x in controle_dates) == 1
        assert sum(x["Statut_raccordement"] == "PISTE_FINANCIERE_SHA256_OK_NON_CERTIFIEE"
                   for x in controle_dates) == 8
        assert all(x["Note_SSI"] == x["Note_MCPA"] == "MANQUANTE"
                   for x in controle_dates)
        # Une période comptable ne peut pas contenir une heure ni un fuseau.
        periode_non_civile = [dict(x) for x in faits_icape]
        periode_non_civile[0]["Periode_cloture"] = "2026-06-30T00:00:00+00:00"
        ecrire(chemin_icape, periode_non_civile)
        controle_periode = m.executer(b)
        assert sum(x["Statut_raccordement"] == "EN_ATTENTE_DATA_DATES"
                   for x in controle_periode) == 1
        ecrire(chemin_icape, faits_icape)
        # URL primaire adversariale : aucun score, même avec SHA256 présent.
        for mauvaise_url in (
            "https://user:secret@www.icape-group.com/report.pdf",
            "https://www.icape-group.com/report.pdf#session",
            "https://www.icape-group.com:bad/report.pdf",
            "http://www.icape-group.com/report.pdf",
        ):
            ligne = dict(faits_icape[0])
            ligne["Source_URL"] = mauvaise_url
            statut, _, _ = m.controler_ligne(
                ligne,
                {x["Ticker"]: x for x in dossiers_originaux},
                m.indexer_archives(b), b, m.datetime.now(m.timezone.utc))
            assert statut == "EN_ATTENTE_DATA_PROVENANCE", (mauvaise_url, statut)
        ecrire(chemin_icape, faits_icape)
        # Une source corrompue ne bloque pas les autres : refus local des 9 faits ICAPE.
        brut = b / "AUDITS/SOURCES_OFFICIELLES" / CAPTURES[0] / (
            "05605e38d3a3e9778d3d8468b613752fe54ef2bbe529bd109b5c622824b0669c.bin")
        brut.write_bytes(brut.read_bytes() + b"CORRUPTION_TEST")
        resultat = m.executer(b)
        assert sum(r["Statut_raccordement"] == "EN_ATTENTE_DATA_SOURCE" for r in resultat) == 9
        assert sum(r["Statut_raccordement"] == "EN_ATTENTE_DATA_IDENTITE" for r in resultat) == 9
        couverture = lire(b / "DONNEES/COUVERTURE_OBSERVATIONS_SSI_NON_CERTIFIEES.csv")
        assert sum(int(x["Nombre_observations_pistes"]) for x in couverture
                   if x["Ticker"] == "Z8J.F") == 0  # source corrompue isolée
        assert sum(int(x["Nombre_observations_pistes"]) for x in couverture
                   if x["Ticker"] == "1F6.F") == 9
        # Une note injectée dans le registre factuel est refusée.
        chemin = b / "AUDITS/REPARATION" / m.NOMS[1]
        faits = lire(chemin)
        faits[0]["Note_SSI"] = "80"
        ecrire(chemin, faits)
        resultat = m.executer(b)
        assert sum(r["Statut_raccordement"] == "REJET_NOTE_OU_QUALIFICATION" for r in resultat) == 1
        assert all(r["Note_SSI"] == r["Note_MCPA"] == "MANQUANTE" for r in resultat)
        # Reprise sur incident 07Q3 : une erreur pendant l'ecriture de
        # l'audit ne doit jamais tronquer le dernier audit publie.
        audit_path = b / "DONNEES/AUDIT_RACCORDEMENT_FAITS_SSI.csv"
        audit_precedent = audit_path.read_bytes()
        dictwriter_initial = csv.DictWriter
        class EchecEcritureAudit(dictwriter_initial):
            def writerow(self, rowdict):
                if ("Observations" in self.fieldnames
                        and rowdict.get("Observations") != "Observations"):
                    self.writer.writerow(["AUDIT_PARTIEL_INJECTE"])
                    raise OSError("Panne simulee pendant l'ecriture de l'audit 07Q3")
                return super().writerow(rowdict)
        csv.DictWriter = EchecEcritureAudit
        try:
            try:
                m.executer(b)
            except OSError as exc:
                assert "Panne simulee" in str(exc)
            else:
                raise AssertionError("Injection de panne audit 07Q3 non declenchee")
        finally:
            csv.DictWriter = dictwriter_initial
        assert audit_path.read_bytes() == audit_precedent, (
            "Panne 07Q3 : le dernier audit valide a ete ecrase ou tronque")
        assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in originals.items())
    print("07Q3: 18 faits réutilisés, 9 pistes SHA256, 9 identités en attente; corruption et note injectée rejetées")


if __name__ == "__main__":
    test()

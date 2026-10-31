"""Index documentaire 07AA -> plan 07Q2 : pistes seulement, jamais preuves certifiées."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv
import hashlib
import importlib.util
import json
import shutil
import tempfile
import sys

ROOT=Path(__file__).resolve().parents[1]

def csv_ecrire(path,colonnes,lignes):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=colonnes)
        w.writeheader()
        w.writerows(lignes)

def tester():
    with tempfile.TemporaryDirectory() as d:
        base=Path(d)
        (base/"SCRIPTS_ACTIFS").mkdir()
        (base/"DONNEES").mkdir()
        for nom in ("07Q2_AUDIT_PREUVES_SSI.py","preuves_ssi.py"):
            shutil.copy2(ROOT/"SCRIPTS_ACTIFS"/nom,base/"SCRIPTS_ACTIFS"/nom)
        sys.path.insert(0,str(base/"SCRIPTS_ACTIFS"))
        spec=importlib.util.spec_from_file_location("audit_ssi_test",base/"SCRIPTS_ACTIFS/07Q2_AUDIT_PREUVES_SSI.py")
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        dossiers=[
            {"Ticker":"FICTIF.F","Societe":"Fictif","Pays":"Allemagne","CIK":"MANQUANTE",
             "Identifiant_emetteur_verifie":"MANQUANTE","Conflit_identite_CIK":"NON"},
            {"Ticker":"AUTRE.F","Societe":"Autre","Pays":"France","CIK":"MANQUANTE",
             "Identifiant_emetteur_verifie":"MANQUANTE","Conflit_identite_CIK":"NON"}
        ]
        csv_ecrire(module.SRC,list(dossiers[0]),dossiers)
        csv_ecrire(module.ARCHIVE_IDENTITE,["Ticker","Societe","ISIN"],[])
        dossier=base/"AUDITS/SOURCES_OFFICIELLES/20261031T000000000000Z"
        dossier.mkdir(parents=True)
        octets=b"Document officiel fictif : pas de validation SSI."
        sha=hashlib.sha256(octets).hexdigest()
        brut=dossier/(sha+".bin")
        brut.write_bytes(octets)
        url="https://exemple.test/communique"
        date=datetime.now(timezone.utc).isoformat()
        ligne={"ID_document":"TEST","Ticker":"FICTIF.F","Identifiant_emetteur":"ISIN:FR0011271600",
               "Source_URL":url,"Type_source":"PUBLICATION_EMETTEUR",
               "Date_publication":"","Date_collecte_UTC":date,
               "Statut_date_publication":"INCONNUE_NE_PAS_UTILISER_RETROSPECTIVEMENT",
               "Statut":"DOCUMENT_COLLECTE_A_VERIFIER","SHA256":sha,
               "Fichier_brut":str(brut.relative_to(base))}
        colonnes=list(ligne)
        audit=dossier/"AUDIT_DOCUMENTS.csv"
        def enregistrer(lignes):
            csv_ecrire(audit,colonnes,lignes)
            manifeste={"fichiers":{"AUDIT_DOCUMENTS.csv":hashlib.sha256(audit.read_bytes()).hexdigest(),
                                   brut.name:sha}}
            (dossier/"MANIFESTE.json").write_text(json.dumps(manifeste),encoding="utf-8")
        def anomalies():
            with module.ANOMALIES.open(encoding="utf-8",newline="") as f:
                return list(csv.DictReader(f))
        enregistrer([ligne,dict(ligne,ID_document="TEST_BIS")])
        plan=module.executer()
        p=plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
        assert p.Captures_primaires_SHA256_OK_pistes=="2"
        assert p.URLs_primaires_distinctes_pistes=="1", "Deux captures de la meme URL ne sont pas deux sources"
        assert p.Identifiants_captures_non_certifies=="ISIN:FR0011271600"
        assert p.Captures_publication_inconnue=="2"
        assert p.Captures_sources_URL_pistes==url
        assert p.Captures_SHA256_pistes==sha
        assert p.Captures_dates_publication_pistes=="INCONNUE"
        assert p.Captures_dates_collecte_UTC_pistes==date
        assert p.Statut_captures_non_certifiees=="PISTES_CAPTUREES_NON_CERTIFIEES"
        assert p.Identifiant_emetteur_source=="MANQUANTE"
        assert p.Preuve_validee=="NON" and p.Note_presente=="NON"
        assert not (plan.Preuve_validee=="OUI").any()
        autre=plan[(plan.Ticker=="AUTRE.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
        assert autre.Captures_primaires_SHA256_OK_pistes=="0"
        assert int(__import__("pandas").read_csv(module.AUD).iloc[0].Captures_primaires_SHA256_OK_pistes)==2
        assert anomalies()==[], "Aucune anomalie dans la fixture saine"

        # Un document corrompu est ignoré, sans bloquer le candidat voisin.
        brut.write_bytes(octets+b"alteration")
        plan=module.executer()
        p=plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
        assert p.Captures_primaires_SHA256_OK_pistes=="0"
        assert int(__import__("pandas").read_csv(module.AUD).iloc[0].Captures_invalides_exclues)==2
        assert len(anomalies())==2 and {a["Code_anomalie"] for a in anomalies()}=={"SHA256_BRUT_DIVERGENT"}

        # La restauration des octets rend la piste réutilisable, jamais certifiée.
        brut.write_bytes(octets)
        # Une publication future est exclue, même si le SHA256 est correct.
        futur=(datetime.now(timezone.utc)+timedelta(days=5)).isoformat()
        enregistrer([dict(ligne,Date_publication=futur)])
        assert module.executer().query("Ticker == 'FICTIF.F' and Bloc_SSI == 'IDENTITE_SCE'").iloc[0].Captures_primaires_SHA256_OK_pistes=="0"
        assert anomalies()[0]["Code_anomalie"]=="DATE_PUBLICATION_APRES_COLLECTE"

        # Une date de publication malformee ne doit jamais devenir une date inconnue.
        enregistrer([dict(ligne,Date_publication="date-invalide")])
        plan=module.executer()
        p=plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
        assert p.Captures_primaires_SHA256_OK_pistes=="0"
        assert int(__import__("pandas").read_csv(module.AUD).iloc[0].Captures_invalides_exclues)==1
        assert anomalies()[0]["Code_anomalie"]=="DATE_PUBLICATION_INVALIDE"

        # Un type de source non primaire est refuse meme avec un SHA correct.
        enregistrer([dict(ligne,Type_source="FORUM")])
        plan=module.executer()
        assert anomalies()[0]["Code_anomalie"]=="TYPE_SOURCE_NON_PRIMAIRE"
        p=plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
        assert p.Captures_primaires_SHA256_OK_pistes=="0"

        # Deux identifiants divergents pour un ticker : conflit explicite, aucun score.
        enregistrer([ligne,dict(ligne,Identifiant_emetteur="ISIN:FR001400A3Q3")])
        plan=module.executer()
        p=plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
        assert p.Statut_captures_non_certifiees=="CONFLIT_IDENTIFIANTS_CAPTURE_NON_CERTIFIE"
        assert p.Identifiant_emetteur_source=="MANQUANTE" and p.Note_presente=="NON"

        # Un chemin de sortie du répertoire est refusé même si le SHA est correct.
        enregistrer([dict(ligne,Fichier_brut="../"+brut.name)])
        plan=module.executer()
        p=plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
        assert p.Captures_primaires_SHA256_OK_pistes=="0"
        assert not (plan.Preuve_validee=="OUI").any()
        assert anomalies()[0]["Code_anomalie"]=="CHEMIN_HORS_ARCHIVE"

        # La source bloquee est conservee en diagnostic sans etre une preuve.
        enregistrer([dict(ligne,Statut="BLOQUE_SOURCE")])
        plan=module.executer()
        assert anomalies()[0]["Code_anomalie"]=="SOURCE_BLOQUEE_07AA"
        assert int(__import__("pandas").read_csv(module.AUD).iloc[0].Sources_bloquees)==1
        assert not (plan.Preuve_validee=="OUI").any()

        # Manifeste corrompu : un rejet de lot, jamais une certification.
        (dossier/"MANIFESTE.json").write_text("{invalide",encoding="utf-8")
        module.executer()
        assert anomalies()[0]["Code_anomalie"]=="MANIFESTE_OU_AUDIT_INVALIDE"
        assert int(__import__("pandas").read_csv(module.AUD).iloc[0].Captures_invalides_exclues)==1

        # Ancien format 07AA sans dictionnaire de hashes : non indexable,
        # mais le diagnostic ne doit pas le confondre avec un SHA corrompu.
        (dossier/"MANIFESTE.json").write_text(json.dumps({"documents_collectes":1}),encoding="utf-8")
        module.executer()
        assert anomalies()[0]["Code_anomalie"]=="MANIFESTE_HISTORIQUE_SANS_FICHIERS"
        assert int(__import__("pandas").read_csv(module.AUD).iloc[0].Captures_invalides_exclues)==1
    print("INDEX_07AA_07Q2_OK : SHA256, URL distincte, date, conflit, traversal, aucune admission")

if __name__=="__main__":
    tester()

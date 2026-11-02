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
        octets=b"<html><title>Fictif FR0011271600</title><p>Source fictive</p></html>"
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
               "Fichier_brut":str(brut.relative_to(base)),"Type_contenu":"text/html; charset=UTF-8"}
        # Le schema fixture inclut les colonnes de provenance 07AA.
        ligne["URL_finale"]=url
        ligne["Domaine_autorise"]="exemple.test"
        colonnes=list(ligne)
        audit=dossier/"AUDIT_DOCUMENTS.csv"
        def enregistrer(lignes):
            csv_ecrire(audit,colonnes,lignes)
            fichiers={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dossier.glob("*.bin")}
            fichiers["AUDIT_DOCUMENTS.csv"]=hashlib.sha256(audit.read_bytes()).hexdigest()
            manifeste={"fichiers":fichiers}
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
        preuves_brutes=__import__("pandas").read_csv(
            module.D/"CONCORDANCES_IDENTITE_BRUTS_NON_CERTIFIEES.csv",
            dtype=str,keep_default_na=False)
        assert len(preuves_brutes)==1, "Captures identiques URL/SHA non dedoublees"
        trace=preuves_brutes.iloc[0]
        assert trace.ISIN_observe_dans_brut=="OUI"
        assert trace.Symbole_marche_observe_dans_brut=="NON_APPLICABLE"
        assert trace.SHA256_brut_verifie==sha
        assert trace.Identite_SCE_certifiee=="NON" and trace.Note_SSI=="MANQUANTE"
        assert trace.Archive_brute==str(brut.relative_to(base))
        import pandas as pd
        file_revue=pd.read_csv(module.D/"FILE_CERTIFICATION_IDENTITES_SSI.csv",dtype=str,keep_default_na=False)
        assert len(file_revue)==2
        ligne_revue=file_revue.set_index("Ticker").loc["FICTIF.F"]
        assert ligne_revue.Priorite_revue_documentaire=="P2_PISTES_PRIMAIRES_A_COMPLETER"
        assert ligne_revue.URLs_distinctes_pistes=="1"
        assert ligne_revue.Captures_SHA256_OK_pistes=="2"
        assert ligne_revue.Documents_uniques_URL_SHA256_pistes=="1"
        assert ligne_revue.Repetitions_captures_pistes=="1"
        assert ligne_revue.Publications_date_inconnue=="1"
        assert ligne_revue.Publications_date_connue_a_verifier=="0"
        assert ligne_revue.Statut_certification=="PISTES_NON_CERTIFIEES"
        assert ligne_revue.Qualification_economique=="NON_CALCULEE_PAR_CET_AUDIT"
        assert file_revue.set_index("Ticker").loc["AUTRE.F"].Priorite_revue_documentaire=="P4_AUCUNE_PISTE_PRIMAIRE"

        # Deux domaines et deux octets distincts priorisent la revue,
        # mais n'autorisent jamais une validation SCE ni une note.
        octets2=b"<html><title>FR0011271600</title><span>Symbol: FICTIF</span></html>"
        sha2=hashlib.sha256(octets2).hexdigest()
        brut2=dossier/(sha2+".bin")
        brut2.write_bytes(octets2)
        ligne2=dict(ligne,ID_document="TEST_AUTRE",
                    Source_URL="https://regulateur.test/fiche",
                    URL_finale="https://regulateur.test/fiche",
                    Domaine_autorise="regulateur.test",
                    SHA256=sha2,Fichier_brut=str(brut2.relative_to(base)),
                    Date_publication="2026-10-01",Type_source="DONNEE_MARCHE_IDENTITE",
                    Statut_date_publication="DATE_DECLAREE_A_VERIFIER")
        enregistrer([ligne,ligne2])
        plan=module.executer()
        file_revue=pd.read_csv(module.D/"FILE_CERTIFICATION_IDENTITES_SSI.csv",dtype=str,keep_default_na=False)
        ligne_revue=file_revue.set_index("Ticker").loc["FICTIF.F"]
        assert ligne_revue.Priorite_revue_documentaire=="P1_PISTES_MULTIDOMAINES_A_CERTIFIER"
        assert ligne_revue.Domaines_hebergement_distincts_pistes=="2"
        assert ligne_revue.SHA256_distincts_pistes=="2"
        assert ligne_revue.Documents_uniques_URL_SHA256_pistes=="2"
        assert ligne_revue.Repetitions_captures_pistes=="0"
        assert ligne_revue.Publications_date_inconnue=="1"
        assert ligne_revue.Statut_certification=="PISTES_NON_CERTIFIEES"
        preuves_brutes=__import__("pandas").read_csv(
            module.D/"CONCORDANCES_IDENTITE_BRUTS_NON_CERTIFIEES.csv",
            dtype=str,keep_default_na=False)
        assert len(preuves_brutes)==2
        marche=preuves_brutes[preuves_brutes.Type_source=="DONNEE_MARCHE_IDENTITE"].iloc[0]
        assert marche.ISIN_observe_dans_brut=="OUI"
        assert marche.Symbole_marche_observe_dans_brut=="OUI"
        assert marche.Date_publication_declaree=="2026-10-01"
        assert not (preuves_brutes.Identite_SCE_certifiee!="NON").any()
        assert not (preuves_brutes.Note_SSI!="MANQUANTE").any()
        assert not (plan.Preuve_validee=="OUI").any()
        enregistrer([ligne,dict(ligne,ID_document="TEST_BIS")])

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

        # Un horodatage de collecte sans UTC explicite ne doit jamais
        # etre interprete comme UTC par pandas. Les autres candidats restent.
        for collecte_invalide in (
            "2026-10-31T17:31:26",
            "2026-10-31T17:31:26+01:00",
            "2026-10-31 17:31:26+00:00",
        ):
            enregistrer([dict(ligne,Date_collecte_UTC=collecte_invalide)])
            plan=module.executer()
            p=plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
            assert p.Captures_primaires_SHA256_OK_pistes=="0"
            assert anomalies()[0]["Code_anomalie"]=="DATE_COLLECTE_SANS_UTC_EXPLICITE"
            assert plan[(plan.Ticker=="AUTRE.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].shape[0]==1
            assert not (plan.Preuve_validee=="OUI").any()
        # La forme Z UTC valide reste acceptee sans creer de preuve certifiee.
        enregistrer([dict(ligne,Date_collecte_UTC=date.replace("+00:00","Z"))])
        plan=module.executer()
        assert plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0].Captures_primaires_SHA256_OK_pistes=="1"
        assert not (plan.Preuve_validee=="OUI").any()

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

        # Le hash seul ne prouve pas la provenance : redirection vers un
        # autre editeur et domaine d'habilitation contradictoire sont rejetes.
        enregistrer([dict(ligne,URL_finale="https://autre-editeur.test/communique")])
        plan=module.executer()
        assert anomalies()[0]["Code_anomalie"]=="REDIRECTION_HORS_ORGANISATION"
        assert plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0].Captures_primaires_SHA256_OK_pistes=="0"
        assert not (plan.Preuve_validee=="OUI").any()

        enregistrer([dict(ligne,Domaine_autorise="autre-editeur.test")])
        module.executer()
        assert anomalies()[0]["Code_anomalie"]=="DOMAINE_SOURCE_NON_AUTORISE"

        enregistrer([dict(ligne,URL_finale="http://exemple.test/communique")])
        module.executer()
        assert anomalies()[0]["Code_anomalie"]=="URL_FINALE_INVALIDE"

        enregistrer([dict(ligne,Source_URL="https://user:secret@exemple.test/communique")])
        module.executer()
        assert anomalies()[0]["Code_anomalie"]=="URL_NON_HTTPS"

        # Redirection vers un sous-domaine du meme editeur : indice accepte,
        # sans jamais etre certifie comme identite SCE ou comme note.
        enregistrer([dict(ligne,URL_finale="https://cdn.exemple.test/communique",
                             Domaine_autorise="exemple.test")])
        plan=module.executer()
        assert anomalies()==[]
        assert plan[(plan.Ticker=="FICTIF.F")&(plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0].Captures_primaires_SHA256_OK_pistes=="1"
        assert not (plan.Preuve_validee=="OUI").any()

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

"""Audit statique bloquant AVANT toute sauvegarde totale MICRO CAPS.

Ne modifie aucun fichier. Une réussite de ce contrôle est nécessaire mais
non suffisante : les tests CI, la collecte réelle, l'affichage publié et
l'intégrité de l'archive reconstructible restent à vérifier séparément.
"""
from pathlib import Path
import csv
import re
import sys

BASE = Path(__file__).resolve().parents[1]
D = BASE / "DONNEES"

def lignes(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("FICHIER_ABSENT_OU_VIDE:" + str(path.relative_to(BASE)))
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def auditer():
    erreurs = []
    def controle(nom, operation):
        try:
            operation()
            print("OK:", nom)
        except Exception as exc:
            erreurs.append(nom + ": " + str(exc))
            print("BLOQUANT:", erreurs[-1])
    def taille_exacte(nom, taille):
        n = len(lignes(D / nom))
        if n != taille:
            raise ValueError("lignes=" + str(n) + ", attendu=" + str(taille))
    controle("cohorte_T0_40", lambda: taille_exacte("COHORTE_MICRO_CAPS_T0.csv", 40))
    controle("portefeuille_gere_40", lambda: taille_exacte("ETAT_INITIAL_PORTEFEUILLE_GERE.csv", 40))
    controle("valorisation_40", lambda: taille_exacte("TEST_PORTEFEUILLES_V3.csv", 40))
    controle("benchmarks_3", lambda: taille_exacte("TEST_BENCHMARKS_V3.csv", 3))
    def qualite():
        rows = lignes(D / "TEST_CONTROLE_QUALITE_V3.csv")
        if len(rows) != 40 or any(x.get("Statut_qualite") != "OK" for x in rows):
            raise ValueError("controle_qualite_incomplet_ou_anomalies")
    controle("qualite_40_sur_40", qualite)
    def chasse():
        rows = lignes(D / "CHASSE_CANDIDATS.csv")
        if not rows:
            raise ValueError("aucun_candidat")
    controle("chasse_non_vide", chasse)
    def dossiers():
        rows = lignes(D / "DOSSIERS_SSI_A_QUALIFIER.csv")
        if not rows:
            raise ValueError("aucun_dossier_SSI")
    controle("dossiers_SSI_presents", dossiers)
    def revue():
        rows = lignes(D / "REVUE_HEBDOMADAIRE_MCPA_IPS.csv")
        chall = [r for r in rows if r.get("Type", "").upper() == "CHALLENGER"
                 and r.get("Statut_analyse", "").strip()
                 and r.get("Sources", "").strip()
                 and r.get("Date_sources", "").strip()]
        qualifies = []
        for r in chall:
            try:
                if float(r.get("SSI", "")) >= 65 and float(r.get("MCPA", "")) >= 80:
                    qualifies.append(r)
            except ValueError:
                continue
        if not qualifies:
            raise ValueError("aucun_challenger_SSI65_MCPA80_avec_sources")
        return qualifies
    candidats = []
    def verifier_revue():
        candidats.extend(revue())
    controle("qualification_et_confrontation_MCPA", verifier_revue)
    def mobile():
        page = (BASE / "index.html").read_text(encoding="utf-8")
        app = (BASE / "APPLICATION/index.html").read_text(encoding="utf-8")
        if page != app:
            raise ValueError("tableaux_de_bord_divergents")
        if 'challengers qualifiés</div></div></div><div class="waiting">' in page:
            raise ValueError("affichage_mobile_challengers_en_attente")
        if not candidats:
            raise ValueError("aucun_challenger_qualifie_a_confronter")
        if not any(re.search(r"(?<![A-Z0-9])" + re.escape(r.get("Ticker", "")) + r"(?![A-Z0-9])", page) for r in candidats if r.get("Ticker")):
            raise ValueError("challengers_qualifies_absents_du_tableau")
    controle("challengers_visibles_mobile", mobile)
    print("AUDIT_PRE_SAUVEGARDE_STATIQUE:", "BLOQUE" if erreurs else "PASSE_CONDITIONS_MINIMALES")
    return 1 if erreurs else 0

if __name__ == "__main__":
    sys.exit(auditer())

"""Audit des trois transmissions MICRO CAPS. Lecture seule des sources, aucun ordre."""
from pathlib import Path
from datetime import datetime, timezone
import csv, json
BASE=Path(__file__).resolve().parents[1]
D=BASE/"DONNEES"

def rows(name):
    p=D/name
    if not p.exists() or p.stat().st_size==0:
        return []
    with p.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def n(x):
    try: return float(x)
    except (ValueError,TypeError): return 0.0

def executer():
    chasse=rows("SORTIE_SCREENER_CANDIDATS.csv")
    fond=rows("FONDAMENTAUX_CANDIDATS_MICRO_CAPS.csv")
    prets=rows("CANDIDATS_PRETS_SSI.csv")
    attentes=rows("CANDIDATS_SSI_DONNEES_MANQUANTES.csv")
    preuves=rows("REGISTRE_PREUVES_SSI.csv")
    resultats=rows("RESULTATS_SSI.csv")
    revue=rows("REVUE_HEBDOMADAIRE_MCPA_IPS.csv")
    duels=rows("DUELS_PROCHAIN_EURO.csv")
    journal=rows("JOURNAL_ARBITRAGES_GERE.csv")
    portefeuille=rows("TEST_PORTEFEUILLES_V3.csv")
    benchmarks=rows("TEST_BENCHMARKS_V3.csv")
    qualifies=[r for r in resultats if r.get("Statut_SSI")=="ADMIS_SSI"]
    tprets={r.get("Ticker") for r in prets}
    avec_preuves={r.get("Ticker") for r in preuves if r.get("Ticker") in tprets}
    titulaires=[r for r in revue if r.get("Type","").upper()=="TITULAIRE"]
    challengers=[r for r in revue if r.get("Type","").upper()=="CHALLENGER"]
    operations=[r for r in journal if r.get("Statut_operation","").upper() in {"EXECUTEE","EXECUTE","EXÉCUTÉE","EXÉCUTÉ"}]
    a1={"detections":len(chasse),"fondamentaux_recenses":len(fond),
        "fondamentaux_OK":sum(r.get("Statut_fondamentaux")=="OK" for r in fond),
        "fondamentaux_manquants":sum(r.get("Statut_fondamentaux")=="MANQUANTE" for r in fond),
        "prets_a_documenter_SSI":len(prets),"en_attente_ou_exclus":len(attentes),
        "prets_volume_median_positif":sum(n(r.get("Volume_monetaire_median_63s_local"))>0 for r in prets)}
    a2={"preuves_en_registre":len(preuves),"candidats_avec_au_moins_une_preuve":len(avec_preuves),
        "resultats_SSI":len(resultats),"admis_SSI":len(qualifies),
        "challengers_MCPA_documentes":len(challengers),
        "statut":"AUCUN_ADMIS_VERIFIE" if not qualifies else "ADMISSIONS_A_CONFRONTER"}
    a3={"titulaires_revus":len(titulaires),"duels":len(duels),
        "operations_virtuelles_executees_cumulees":len(operations),
        "positions_valorisees":len(portefeuille),"benchmarks":len(benchmarks),
        "statut":"BLOQUE_SANS_REVUE_VALIDEE" if not titulaires or not qualifies else "REVUE_A_CONTROLER"}
    if portefeuille:
        p=portefeuille[0]
        a3.update(date_valorisation=p.get("Date_cloture"),
            valeur_gere_EUR=round(n(p.get("Total_Gere_EUR")),2),
            valeur_temoin_EUR=round(n(p.get("Total_Temoin_EUR")),2),
            performance_gere_pct=round(n(p.get("Perf_Gere_Portefeuille_pct")),3),
            performance_temoin_pct=round(n(p.get("Perf_Temoin_Portefeuille_pct")),3))
    resultat={"date_audit_UTC":datetime.now(timezone.utc).isoformat(),
        "agent_1_chasse":a1,"agent_2_filtrage":a2,"agent_3_confrontation":a3,
        "arbitrage_nouveau_autorise":bool(qualifies and len(titulaires)>0 and len(duels)>0),
        "avertissement":"Audit de transmission, pas certification des preuves ni execution d'ordres."}
    p=D/"AUDIT_CHAINE_3_AGENTS.json"
    temp=p.with_suffix(".tmp")
    temp.write_text(json.dumps(resultat,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(p)
    print(json.dumps(resultat,ensure_ascii=False))
    return resultat

if __name__=="__main__":
    executer()

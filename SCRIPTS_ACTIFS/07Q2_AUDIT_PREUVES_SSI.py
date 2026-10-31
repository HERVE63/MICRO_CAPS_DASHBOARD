"""Plan SSI de collecte documentaire : 7 blocs, identite et exclusions.
Les observations fournisseur ne sont jamais des preuves primaires certifiees.
Le pays de cotation ne prouve pas le domicile juridique de l'emetteur.
"""
from pathlib import Path
import re
import pandas as pd

D=Path(__file__).resolve().parent.parent/"DONNEES"
SRC=D/"DOSSIERS_SSI_A_QUALIFIER.csv"
OUT=D/"PLAN_COLLECTE_PREUVES_SSI.csv"
AUD=D/"AUDIT_COLLECTE_PREUVES_SSI.csv"
CHAMPS={
 "B1":("B1_bilan_cash","B1_bilan_dette"),
 "B2":("B2_rentabilite_EBITDA","B2_rentabilite_FCF"),
 "B3":("B3_croissance_CA","B3_marge_brute"),
 "B4":("B4_skin_in_game",),
 "B5":("B5_actions_en_circulation",),
 "B6":("B6_source","B6_date"),
 "B7":("B7_volume_local",),
}
COMPLEMENTS={
 "B1":"Echeances de dette, besoins de financement et runway",
 "B2":"Historique EBITDA/EBIT, resultat, FCF et inflexion",
 "B3":"Historique CA, commandes, recurrence, clients",
 "B4":"Actions detenues directement, achats/ventes, options et gouvernance",
 "B5":"Historique emissions, dilution, options, remuneration, auditeur",
 "B6":"Comptes reglementes audites, dates et coherence",
 "B7":"Place de cotation, turnover et spread si disponible",
}
COLONNES=["Ticker","Societe","Bloc_SSI","Variables_absentes","Preuve_validee",
          "Note_presente","Preuves_complementaires_requises","Source_actuelle",
          "Date_source_actuelle","Statut","Identifiant_emetteur_source",
          "Pays_cotation_declare","Pays_emetteur_verifie"]
def manquant(v):
 return pd.isna(v) or str(v).strip().upper() in ("","MANQUANTE","NAN","NONE","N/A")

def executer():
 if not SRC.exists(): raise RuntimeError("Dossiers SSI absents")
 df=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 if "Ticker" not in df:raise RuntimeError("Ticker absent des dossiers SSI")
 if df["Ticker"].duplicated().any(): raise RuntimeError("Tickers dupliques: identite a resoudre")
 rows=[]
 for _,r in df.iterrows():
  cik=str(r.get("CIK","")).strip()
  ident="CIK:"+cik if re.fullmatch(r"[0-9]{10}",cik) else "MANQUANTE"
  base={"Ticker":r["Ticker"],"Societe":r.get("Societe",""),
        "Source_actuelle":r.get("B6_source",""),
        "Date_source_actuelle":r.get("B6_date",""),
        "Identifiant_emetteur_source":ident,
        "Pays_cotation_declare":r.get("Pays",""),
        "Pays_emetteur_verifie":"MANQUANTE"}
  # Ces deux controles sont des prealables a la notation, non des notes.
  # Ne jamais utiliser Pays (place de cotation) comme domicile de l'emetteur.
  rows.append({**base,"Bloc_SSI":"IDENTITE_SCE",
    "Variables_absentes":"CIK ou identifiant reglementaire ISIN/LEI verifie" if ident=="MANQUANTE" else "",
    "Preuve_validee":"A_CONTROLER" if not manquant(r.get("Preuves_identite_SCE","")) else "NON",
    "Note_presente":"NON",
    "Preuves_complementaires_requises":"Deux sources primaires independantes, concordance emetteur/ISIN/LEI/CIK, provenance, date et SHA256",
    "Statut":"EN_ATTENTE_DATA_IDENTITE" if ident=="MANQUANTE" else "A_VERIFIER_IDENTITE_SCE"})
  rows.append({**base,"Bloc_SSI":"EXCLUSIONS",
    "Variables_absentes":"Preuve primaire du controle des exclusions" if manquant(r.get("Motif_eliminatoire","")) else "",
    "Preuve_validee":"A_CONTROLER" if not manquant(r.get("Motif_eliminatoire","")) else "NON",
    "Note_presente":"NON",
    "Preuves_complementaires_requises":"Exclusions documentees sur le meme emetteur, date, fichier brut et SHA256",
    "Statut":"A_CONTROLER_EXCLUSIONS"})
  for bloc,fields in CHAMPS.items():
   absents=[f for f in fields if f not in df.columns or manquant(r.get(f,""))]
   preuve=r.get("Preuve_"+bloc,"MANQUANTE")
   note=r.get("Note_"+bloc,"MANQUANTE")
   rows.append({**base,"Bloc_SSI":bloc,
    "Variables_absentes":" | ".join(absents) if absents else "",
    "Preuve_validee":"NON" if manquant(preuve) else "A_CONTROLER",
    "Note_presente":"NON" if manquant(note) else "OUI",
    "Preuves_complementaires_requises":COMPLEMENTS[bloc],
    "Statut":"A_COMPLETER_PREUVES_SSI"})
 out=pd.DataFrame(rows,columns=COLONNES)
 out.to_csv(OUT,index=False)
 blocs=out[out.Bloc_SSI.isin(CHAMPS)]
 pd.DataFrame([{"Dossiers":len(df),"Blocs_a_auditer":len(blocs),
   "Blocs_avec_variables_absentes":int(blocs["Variables_absentes"].ne("").sum()),
   "Controles_identite_exclusions":len(out)-len(blocs),
   "Identites_CIK_source_absentes":sum(not bool(re.fullmatch(r"[0-9]{10}",str(x).strip())) for x in df["CIK"]) if "CIK" in df else len(df),
   "Lignes_plan":len(out),
   "Statut":"EN_ATTENTE_DATA" if df.empty else "AUCUNE_NOTE_AUTOMATIQUE_SANS_PREUVE"}]).to_csv(AUD,index=False)
 print("Plan de collecte SSI",len(df),"dossiers",len(blocs),"blocs",len(out)-len(blocs),"controles")
 return out
if __name__=="__main__": executer()

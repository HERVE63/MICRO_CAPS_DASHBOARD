"""Audit des preuves SSI manquantes et priorites de collecte, sans score invente."""
from pathlib import Path
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
def manquant(v):
 return pd.isna(v) or str(v).strip().upper() in ("","MANQUANTE","NAN","NONE","N/A")
def executer():
 if not SRC.exists(): raise RuntimeError("Dossiers SSI absents")
 df=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 if df.empty: raise RuntimeError("Dossiers SSI vides")
 if df["Ticker"].duplicated().any(): raise RuntimeError("Tickers dupliques: identite a resoudre")
 rows=[]
 for _,r in df.iterrows():
  for bloc,fields in CHAMPS.items():
   absents=[f for f in fields if f not in df.columns or manquant(r.get(f,""))]
   preuve=r.get("Preuve_"+bloc,"MANQUANTE")
   note=r.get("Note_"+bloc,"MANQUANTE")
   rows.append({
    "Ticker":r["Ticker"],"Societe":r.get("Societe",""),
    "Bloc_SSI":bloc,"Variables_absentes":" | ".join(absents) if absents else "",
    "Preuve_validee":"NON" if manquant(preuve) else "A_CONTROLER",
    "Note_presente":"NON" if manquant(note) else "OUI",
    "Preuves_complementaires_requises":COMPLEMENTS[bloc],
    "Source_actuelle":r.get("B6_source",""),
    "Date_source_actuelle":r.get("B6_date",""),
    "Statut":"A_COMPLETER_PREUVES_SSI"
   })
 out=pd.DataFrame(rows)
 out.to_csv(OUT,index=False)
 pd.DataFrame([{"Dossiers":len(df),"Blocs_a_auditer":len(out),
   "Blocs_avec_variables_absentes":int(out["Variables_absentes"].ne("").sum()),
   "Statut":"AUCUNE_NOTE_AUTOMATIQUE_SANS_PREUVE"}]).to_csv(AUD,index=False)
 print("Plan de collecte SSI",len(df),"dossiers",len(out),"blocs")
 return out
if __name__=="__main__": executer()

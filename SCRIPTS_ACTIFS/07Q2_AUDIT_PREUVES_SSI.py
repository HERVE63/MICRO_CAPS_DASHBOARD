"""Plan SSI de collecte documentaire : 7 blocs, identite et exclusions.
Les observations fournisseur ne sont jamais des preuves primaires certifiees.
Le pays de cotation ne prouve pas le domicile juridique de l'emetteur.
"""
from pathlib import Path
import hashlib
import re
import pandas as pd

D=Path(__file__).resolve().parent.parent/"DONNEES"
SRC=D/"DOSSIERS_SSI_A_QUALIFIER.csv"
OUT=D/"PLAN_COLLECTE_PREUVES_SSI.csv"
AUD=D/"AUDIT_COLLECTE_PREUVES_SSI.csv"
ARCHIVE_IDENTITE=D/"IDENTITE_COTATIONS_MULTIPLES.csv"
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
          "Pays_cotation_declare","Pays_emetteur_verifie",
          "ISIN_piste_non_certifiee","Societe_archive_ISIN","Statut_piste_ISIN",
          "Provenance_archive_ISIN","SHA256_archive_ISIN","Date_archive_ISIN"]
def manquant(v):
 return pd.isna(v) or str(v).strip().upper() in ("","MANQUANTE","NAN","NONE","N/A")


def isin_checksum_valide(v):
 """Controle formel ISO 6166 (Luhn), JAMAIS une preuve d'identite."""
 if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]",v):return False
 chiffres="".join(str(ord(c)-55) if "A"<=c<="Z" else c for c in v)
 total=0
 for position,c in enumerate(reversed(chiffres)):
  n=int(c)
  if position%2:
   n*=2
   n=n//10+n%10
  total+=n
 return total%10==0

def lire_pistes_archive():
 """Reutilisation strictement indicative de 07D ; aucune promotion en preuve SSI."""
 if not ARCHIVE_IDENTITE.exists():return {}, "MANQUANTE"
 brut=ARCHIVE_IDENTITE.read_bytes()
 empreinte=hashlib.sha256(brut).hexdigest()
 d=pd.read_csv(ARCHIVE_IDENTITE,dtype=str,keep_default_na=False)
 requis={"Ticker","Societe","ISIN"}
 if not requis.issubset(d.columns):
  raise RuntimeError("Schema archive ISIN historique incomplet : "+", ".join(sorted(requis-set(d.columns))))
 if d["Ticker"].astype(str).str.strip().eq("").any():
  raise RuntimeError("Ticker vide dans archive ISIN historique")
 pistes={}
 for ticker,g in d.groupby("Ticker",sort=False):
  if len(g)!=1:
   pistes[ticker]=("MANQUANTE","MANQUANTE","TICKER_AMBIGU_ARCHIVE")
   continue
  r=g.iloc[0]
  isin=str(r["ISIN"]).strip().upper()
  statut=("PISTE_ISIN_CHECKSUM_OK_NON_CERTIFIEE" if isin_checksum_valide(isin)
          else "ISIN_ABSENT_ARCHIVE" if isin in {"","-","MANQUANTE"}
          else "ISIN_INVALIDE_ARCHIVE")
  pistes[ticker]=(isin if isin_checksum_valide(isin) else "MANQUANTE",
                  str(r["Societe"]).strip(),statut)
 return pistes,empreinte

def executer():
 if not SRC.exists(): raise RuntimeError("Dossiers SSI absents")
 df=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 if "Ticker" not in df:raise RuntimeError("Ticker absent des dossiers SSI")
 if df["Ticker"].duplicated().any(): raise RuntimeError("Tickers dupliques: identite a resoudre")
 pistes,sha_archive=lire_pistes_archive()
 rows=[]
 for _,r in df.iterrows():
  cik=str(r.get("CIK","")).strip()
  ident="CIK:"+cik if re.fullmatch(r"[0-9]{10}",cik) else "MANQUANTE"
  isin_piste,societe_archive,statut_piste=pistes.get(r["Ticker"],("MANQUANTE","MANQUANTE","AUCUNE_PISTE_ARCHIVE"))
  base={"Ticker":r["Ticker"],"Societe":r.get("Societe",""),
        "Source_actuelle":r.get("B6_source",""),
        "Date_source_actuelle":r.get("B6_date",""),
        "Identifiant_emetteur_source":ident,
        "Pays_cotation_declare":r.get("Pays",""),
        "Pays_emetteur_verifie":"MANQUANTE",
        "ISIN_piste_non_certifiee":isin_piste,
        "Societe_archive_ISIN":societe_archive,
        "Statut_piste_ISIN":statut_piste,
        "Provenance_archive_ISIN":str(ARCHIVE_IDENTITE.relative_to(D.parent)) if statut_piste!="AUCUNE_PISTE_ARCHIVE" else "MANQUANTE",
        "SHA256_archive_ISIN":sha_archive if statut_piste!="AUCUNE_PISTE_ARCHIVE" else "MANQUANTE",
        "Date_archive_ISIN":"MANQUANTE"}
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
   "Pistes_ISIN_checksum_OK_non_certifiees":int((out["Bloc_SSI"].eq("IDENTITE_SCE") & out["Statut_piste_ISIN"].eq("PISTE_ISIN_CHECKSUM_OK_NON_CERTIFIEE")).sum()),
   "Pistes_ISIN_ambigues_ou_invalides":int((out["Bloc_SSI"].eq("IDENTITE_SCE") & out["Statut_piste_ISIN"].isin(["TICKER_AMBIGU_ARCHIVE","ISIN_INVALIDE_ARCHIVE"])).sum()),
   "Statut":"EN_ATTENTE_DATA" if df.empty else "AUCUNE_NOTE_AUTOMATIQUE_SANS_PREUVE"}]).to_csv(AUD,index=False)
 print("Plan de collecte SSI",len(df),"dossiers",len(blocs),"blocs",len(out)-len(blocs),"controles")
 return out
if __name__=="__main__": executer()

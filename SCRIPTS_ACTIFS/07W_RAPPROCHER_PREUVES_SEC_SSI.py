"""Rapprochement documentaire SEC -> SSI, lecture seule, sans modifier les notes."""
from pathlib import Path
import pandas as pd
D=Path(__file__).resolve().parents[1]/"DONNEES"
DOS=D/"DOSSIERS_SSI_A_QUALIFIER.csv"
SEC=D/"PREUVES_SEC_EDGAR_SSI.csv"
FACT=D/"FAITS_SEC_COMPARABLES_SSI.csv"
OUT=D/"RAPPROCHEMENT_PREUVES_SEC_SSI.csv"
AUD=D/"AUDIT_RAPPROCHEMENT_SEC_SSI.csv"
QUAR=D/"QUARANTAINE_RAPPROCHEMENT_SEC_SSI.csv"
BLOCS={"Cash":"B1","Assets":"B1","Liabilities":"B1","OperatingIncome":"B2","NetIncome":"B2","OperatingCashFlow":"B2","Revenues":"B3","Shares":"B5"}
BLOCS.update(DebtCurrent='B1',LongTermDebtCurrent='B1',LongTermDebtNoncurrent='B1',
             GrossProfit='B2',CapitalExpenditure='B2',ShareBasedCompensation='B5')
def executer():
 for p in (DOS,SEC,FACT):
  if not p.exists():raise RuntimeError("Fichier requis absent: "+p.name)
 dossiers=pd.read_csv(DOS,dtype=str,keep_default_na=False)
 sec=pd.read_csv(SEC,dtype=str,keep_default_na=False)
 faits=pd.read_csv(FACT,dtype=str,keep_default_na=False)
 # Un doublon d'identite n'invalide pas toute la cohorte : il bloque
 # uniquement les faits de cet emetteur. Ne jamais choisir arbitrairement
 # la premiere ligne d'un ticker ambigu.
 ambigus={}
 for name,df in (("dossiers",dossiers),("SEC",sec)):
  if not {"Ticker","CIK"}.issubset(df.columns):raise RuntimeError("Schema identite incomplet: "+name)
  cles=df["Ticker"].astype(str).str.strip().str.upper()
  invalides=cles.eq("") | cles.duplicated(keep=False)
  ambigus[name]=set(cles[invalides])
  propre=df.loc[~invalides].copy()
  propre["Ticker"]=cles[~invalides]
  if name=="dossiers":dossiers=propre
  else:sec=propre
 if not {"Ticker","CIK","Concept","Source_officielle","Date_depot","Fin_periode","Valeur","Unite","Statut_comparabilite"}.issubset(faits.columns):
  raise RuntimeError("Schema faits SEC incomplet")
 reg=sec.set_index("Ticker")
 dossiers_index=dossiers.set_index("Ticker")
 admis=set(dossiers["Ticker"])
 rows=[]; quarantaines=[]
 def cik_normalise(v):
  """CIK SEC: uniquement 1 a 10 chiffres, zero-padding sans inference."""
  import re
  s=str(v).strip()
  return s.zfill(10) if re.fullmatch(r"[0-9]{1,10}",s) else ""
 for _,f in faits.iterrows():
  ticker=str(f["Ticker"]).strip().upper()
  if ticker in ambigus["dossiers"] or (ticker in admis and ticker in ambigus["SEC"]):
   quarantaines.append({"Ticker":ticker,"CIK_dossier":"","CIK_SEC":"",
    "CIK_fait":str(f.get("CIK","")).strip(),
    "Statut":"EN_ATTENTE_DATA_IDENTITE_AMBIGUE",
    "Motif":"TICKER_DUPLIQUE_OU_VIDE_DOSSIER_OU_SEC",
    "Source_officielle":f.get("Source_officielle",""),
    "Accession":f.get("Accession","")})
   continue
  if ticker not in admis:continue
  identite=reg.loc[ticker] if ticker in reg.index else None
  cik_dossier=cik_normalise(dossiers_index.loc[ticker].get("CIK",""))
  cik_sec=cik_normalise(identite.get("CIK","")) if identite is not None else ""
  cik_fait=cik_normalise(f["CIK"])
  if not cik_dossier or not cik_sec or not cik_fait or len({cik_dossier,cik_sec,cik_fait})!=1:
   quarantaines.append({"Ticker":ticker,"CIK_dossier":cik_dossier,
    "CIK_SEC":cik_sec,"CIK_fait":cik_fait,
    "Statut":"EN_ATTENTE_DATA_IDENTITE_CIK",
    "Motif":"CIK_ABSENT_INVALIDE_OU_DIVERGENT",
    "Source_officielle":f.get("Source_officielle",""),
    "Accession":f.get("Accession","")})
   continue
  bloc=BLOCS.get(f["Concept"],"HORS_BLOCS")
  statut="A_VERIFIER_IDENTITE_ET_DOCUMENT"
  if identite.get("CIK_verifie","NON")=="OUI" and identite.get("Statut_SEC")=="IDENTITE_VERIFIEE":
   statut="A_VERIFIER_CONTENU_ET_PERIODE"
  rows.append({"Ticker":ticker,"Societe":dossiers_index.loc[ticker].get("Societe",""),
   "CIK":f["CIK"],"Bloc_SSI_cible":bloc,"Concept":f["Concept"],"Valeur":f["Valeur"],
   "Unite":f["Unite"],"Fin_periode":f["Fin_periode"],"Date_depot":f["Date_depot"],
   "Source_officielle":f["Source_officielle"],"Statut_preuve":statut,
   "Statut_comparabilite":f["Statut_comparabilite"],"Note_SSI_attribuee":"NON",
   "Accession":f.get("Accession",""),"Tag_SEC":f.get("Tag_SEC",""),"Taxonomie_SEC":f.get("Taxonomie_SEC","us-gaap"),
   "Debut_periode":f.get("Debut_periode",""),"Formulaire":f.get("Formulaire","")})
 cols=["Ticker","Societe","CIK","Bloc_SSI_cible","Concept","Valeur","Unite","Fin_periode","Date_depot","Source_officielle","Statut_preuve","Statut_comparabilite","Note_SSI_attribuee","Accession","Tag_SEC","Taxonomie_SEC","Debut_periode","Formulaire"]
 qcols=["Ticker","CIK_dossier","CIK_SEC","CIK_fait","Statut","Motif","Source_officielle","Accession"]
 for dest,frame in ((OUT,pd.DataFrame(rows,columns=cols)),
                    (QUAR,pd.DataFrame(quarantaines,columns=qcols))):
  tmp=dest.with_suffix(".tmp");frame.to_csv(tmp,index=False);tmp.replace(dest)
 audit=pd.DataFrame([{"Dossiers_SSI":len(dossiers),"Faits_rapproches":len(rows),
  "Faits_en_quarantaine_identite_CIK":sum(r["Statut"]=="EN_ATTENTE_DATA_IDENTITE_CIK" for r in quarantaines),
  "Faits_en_quarantaine_identite_ambigue":sum(r["Statut"]=="EN_ATTENTE_DATA_IDENTITE_AMBIGUE" for r in quarantaines),
  "Dossiers_identite_ambigue":len(ambigus["dossiers"]),
  "Registre_SEC_identite_ambigue":len(ambigus["SEC"]),
  "Emetteurs_avec_faits":len({r["Ticker"] for r in rows}),"Notes_SSI_attribuees":0,
  "Statut":"PISTES_DOCUMENTAIRES_NON_VALIDEES"}])
 tmp=AUD.with_suffix(".tmp");audit.to_csv(tmp,index=False);tmp.replace(AUD)
 print("Rapprochement SEC SSI:",len(rows),"faits; zero score")
 return rows
if __name__=="__main__":executer()

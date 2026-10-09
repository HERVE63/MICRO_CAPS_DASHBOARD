from pathlib import Path
import pandas as pd
B=Path(__file__).resolve().parent.parent; D=B/"DONNEES"
SRC=D/"CANDIDATS_PRETS_SSI.csv"; OUT=D/"DOSSIERS_SSI_A_QUALIFIER.csv"; AUD=D/"AUDIT_DOSSIERS_SSI.csv"
def executer():
 d=pd.read_csv(SRC)
 if "Date_scan_fond" not in d.columns:
  if "Date_scan" in d.columns:
   d["Date_scan_fond"]=d["Date_scan"]
  else:
   raise RuntimeError("Date des fondamentaux manquante : aucune date inventee")
 if d.empty: raise RuntimeError("Aucun candidat pret SSI")
 # Les 7 blocs du SSI maître. Les variables observées sont exposées, aucune note n'est inventée.
 out=pd.DataFrame({
  "Ticker":d["Ticker"],"Societe":d["Societe"],"Pays":d["Pays"],"Capitalisation_EUR":d["Capitalisation_EUR"],
  "B1_bilan_cash":d["Cash"],"B1_bilan_dette":d["Dette_totale"],
  "B2_rentabilite_EBITDA":d["EBITDA"],"B2_rentabilite_FCF":d["FCF"],
  "B3_croissance_CA":d["Croissance_CA"],"B3_marge_brute":d["Marge_brute"],
  "B4_skin_in_game":d["Insiders_pct"],
  "B5_actions_en_circulation":d["Actions"],
  "B6_source":d["Source_fondamentaux"],"B6_date":d["Date_scan_fond"],
  "B7_volume_local":d["Volume_monetaire_median_63s_local"],
  "Momentum_3m_pct":d["Momentum_3m_pct"],"Momentum_6m_pct":d["Momentum_6m_pct"],
  "Au_dessus_MM200":d["Au_dessus_MM200"]
 })
 # Gouvernance/dilution et qualité documentaire ne peuvent pas être déduites des seuls champs actuels.
 for bloc in ("B1","B2","B3","B4","B5","B6","B7"):
  out["Note_"+bloc]="MANQUANTE"
  out["Preuve_"+bloc]="MANQUANTE"
 out["SSI"]="MANQUANTE"; out["Statut_SSI"]="A_COMPLETER_PREUVES_SSI"
 out["Decision_eliminatoire"]="A_VERIFIER"
 out["Motif_eliminatoire"]="MANQUANTE"
 # Conservation des champs humains par ticker. Aucune collecte ne remet les notes à zéro.
 if OUT.exists():
  ancien=pd.read_csv(OUT,dtype=str,keep_default_na=False)
  if ancien["Ticker"].duplicated().any():raise RuntimeError("Ancien registre SSI dupliqué")
  from datetime import datetime,timezone
  archive=B/"AUDITS"/"DOSSIERS_SSI"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
  archive.mkdir(parents=True,exist_ok=False)
  import shutil
  shutil.copy2(OUT,archive/OUT.name)
  humains=[c for c in ancien if c.startswith(("Note_","Preuve_","Validation_","Correction_")) or c in ("Decision_eliminatoire","Motif_eliminatoire")]
  reg=ancien.set_index("Ticker")
  for c in humains:
   if c not in out:out[c]="MANQUANTE"
   mask=out["Ticker"].isin(reg.index)
   out.loc[mask,c]=out.loc[mask,"Ticker"].map(reg[c])
  # Les données collectées ne certifient jamais une admission antérieure.
  out["SSI"]="MANQUANTE";out["Statut_SSI"]="A_REVALIDER_PREUVES_SSI"
 tmp=OUT.with_suffix(".tmp");out.to_csv(tmp,index=False);tmp.replace(OUT)
 pd.DataFrame([{"Dossiers_prets":len(out),"SSI_notes":0,"SSI_admis_65":0,"Statut":"COLLECTE_PREUVES_SSI_REQUISE"}]).to_csv(AUD,index=False)
 print("Dossiers SSI a qualifier",len(out))
 return out
if __name__=="__main__": executer()

# production

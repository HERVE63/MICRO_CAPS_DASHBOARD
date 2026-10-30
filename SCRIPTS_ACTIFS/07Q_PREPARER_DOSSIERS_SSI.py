from pathlib import Path
import pandas as pd
B=Path(__file__).resolve().parent.parent; D=B/"DONNEES"
SRC=D/"CANDIDATS_PRETS_SSI.csv"; OUT=D/"DOSSIERS_SSI_A_QUALIFIER.csv"; AUD=D/"AUDIT_DOSSIERS_SSI.csv"
def archiver_registre():
 """Sauvegarde toute version précédente, y compris avant une cohorte vide."""
 if not OUT.exists():return
 from datetime import datetime,timezone
 import shutil
 archive=B/"AUDITS"/"DOSSIERS_SSI"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
 archive.mkdir(parents=True,exist_ok=False)
 shutil.copy2(OUT,archive/OUT.name)
def executer():
 # Les CIK sont des identifiants, pas des nombres : conserver leurs zéros initiaux.
 d=pd.read_csv(SRC,dtype={"Ticker":str,"CIK":str},keep_default_na=False)
 if "Date_scan_fond" not in d.columns:
  if "Date_scan" in d.columns:
   d["Date_scan_fond"]=d["Date_scan"]
  else:
   raise RuntimeError("Date des fondamentaux manquante : aucune date inventee")
 if "Momentum_12m_pct" not in d.columns: d["Momentum_12m_pct"]=pd.NA
 if d.empty:
  colonnes=["Ticker","CIK","SCE_valide","Preuves_identite_SCE","SSI","Statut_SSI","Decision_eliminatoire","Motif_eliminatoire"]
  for b in ("B1","B2","B3","B4","B5","B6","B7"):
   colonnes.extend(["Note_"+b,"Preuve_"+b])
  archiver_registre()
  pd.DataFrame(columns=colonnes).to_csv(OUT,index=False)
  pd.DataFrame([{"Dossiers_prets":0,"SSI_notes":0,"SSI_admis_65":0,"Conflits_CIK":0,"Statut":"EN_ATTENTE_DATA"}]).to_csv(AUD,index=False)
  return pd.DataFrame(columns=colonnes)
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
  "Momentum_12m_pct":d["Momentum_12m_pct"],
  "Au_dessus_MM200":d["Au_dessus_MM200"]
 })
 # Gouvernance/dilution et qualité documentaire ne peuvent pas être déduites des seuls champs actuels.
 for bloc in ("B1","B2","B3","B4","B5","B6","B7"):
  out["Note_"+bloc]="MANQUANTE"
  out["Preuve_"+bloc]="MANQUANTE"
 # Le contrôle SCE exige deux preuves indépendantes et un CIK.
 # Le ticker ou Yahoo ne suffisent pas à valider l'identité.
 out["CIK"]=d["CIK"].astype(str) if "CIK" in d.columns else "MANQUANTE"
 out["SCE_valide"]="NON"
 out["Preuves_identite_SCE"]="MANQUANTE"
 out["SSI"]="MANQUANTE"; out["Statut_SSI"]="A_COMPLETER_PREUVES_SSI"
 out["Conflit_identite_CIK"]="NON"
 out["Decision_eliminatoire"]="A_VERIFIER"
 out["Motif_eliminatoire"]="MANQUANTE"
 # Conservation des champs humains par ticker. Aucune collecte ne remet les notes à zéro.
 if OUT.exists():
  ancien=pd.read_csv(OUT,dtype=str,keep_default_na=False)
  if ancien["Ticker"].duplicated().any():raise RuntimeError("Ancien registre SSI dupliqué")
  archiver_registre()
  # Le ticker n'est pas une identité stable. Le CIK de la nouvelle collecte
  # prime s'il est renseigné ; l'ancien CIK n'est repris que si la source
  # actuelle ne fournit aucun identifiant. Une divergence met ce dossier
  # en quarantaine sans interrompre les autres candidats.
  humains=[c for c in ancien if c.startswith(("Note_","Preuve_","Validation_","Correction_")) or c in ("Decision_eliminatoire","Motif_eliminatoire","SCE_valide","Preuves_identite_SCE")]
  reg=ancien.set_index("Ticker")
  mask=out["Ticker"].isin(reg.index)
  for c in humains:
   if c not in out:out[c]="MANQUANTE"
   out.loc[mask,c]=out.loc[mask,"Ticker"].map(reg[c])
  anciens_cik=out.loc[mask,"Ticker"].map(reg["CIK"]) if "CIK" in reg else pd.Series("",index=out.index[mask])
  nouveau_cik=out.loc[mask,"CIK"].astype(str)
  absents={"","MANQUANTE","NAN","NONE","N/A"}
  reprendre=nouveau_cik.str.strip().str.upper().isin(absents) & ~anciens_cik.astype(str).str.strip().str.upper().isin(absents)
  out.loc[anciens_cik.index[reprendre],"CIK"]=anciens_cik[reprendre]
  conflit=(~nouveau_cik.str.strip().str.upper().isin(absents)
           & ~anciens_cik.astype(str).str.strip().str.upper().isin(absents)
           & nouveau_cik.str.strip().ne(anciens_cik.astype(str).str.strip()))
  # La quarantaine reste active après les régénérations suivantes : le fait
  # que le nouveau CIK ait remplacé l'ancien ne prouve PAS la résolution
  # indépendante de la collision initiale.
  deja_bloques=(out.loc[mask,"Ticker"].map(reg["Conflit_identite_CIK"]).eq("OUI")
                if "Conflit_identite_CIK" in reg else pd.Series(False,index=out.index[mask]))
  conflit=conflit | deja_bloques
  if conflit.any():
   indices=anciens_cik.index[conflit]
   for c in humains:
    out.loc[indices,c]="MANQUANTE"
   out.loc[indices,"SCE_valide"]="NON"
   out.loc[indices,"Preuves_identite_SCE"]="MANQUANTE"
   out.loc[indices,"Decision_eliminatoire"]="A_VERIFIER"
   out.loc[indices,"Motif_eliminatoire"]="MANQUANTE"
   out.loc[indices,"Conflit_identite_CIK"]="OUI"
  # Les données collectées ne certifient jamais une admission antérieure.
  out["SSI"]="MANQUANTE";out["Statut_SSI"]="A_REVALIDER_PREUVES_SSI"
  if conflit.any():out.loc[anciens_cik.index[conflit],"Statut_SSI"]="EN_ATTENTE_DATA_IDENTITE_CIK"
 tmp=OUT.with_suffix(".tmp");out.to_csv(tmp,index=False);tmp.replace(OUT)
 pd.DataFrame([{"Dossiers_prets":len(out),"SSI_notes":0,"SSI_admis_65":0,
                "Conflits_CIK":int(out["Conflit_identite_CIK"].eq("OUI").sum()),
                "Statut":"COLLECTE_PREUVES_SSI_REQUISE"}]).to_csv(AUD,index=False)
 print("Dossiers SSI a qualifier",len(out))
 return out
if __name__=="__main__": executer()

# production

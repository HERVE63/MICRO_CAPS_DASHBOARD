from pathlib import Path
import pandas as pd
B=Path(__file__).resolve().parent.parent; D=B/"DONNEES"
SRC=D/"CANDIDATS_PRETS_SSI.csv"; OUT=D/"DOSSIERS_SSI_A_QUALIFIER.csv"; AUD=D/"AUDIT_DOSSIERS_SSI.csv"
def executer():
 d=pd.read_csv(SRC)
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
 out["SSI"]="MANQUANTE"; out["Statut_SSI"]="A_COMPLETER_PREUVES_SSI"
 out.to_csv(OUT,index=False)
 pd.DataFrame([{"Dossiers_prets":len(out),"SSI_notes":0,"SSI_admis_65":0,"Statut":"COLLECTE_PREUVES_SSI_REQUISE"}]).to_csv(AUD,index=False)
 print("Dossiers SSI a qualifier",len(out))
 return out
if __name__=="__main__": executer()

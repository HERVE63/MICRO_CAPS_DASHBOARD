"""Regression 07Q2 hors reseau : identite non US et exclusions avant notation.
Fixtures fictives. Aucun score, document primaire ou ordre financier.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"SCRIPTS_ACTIFS/07Q2_AUDIT_PREUVES_SSI.py"

def executer():
 spec=importlib.util.spec_from_file_location("plan_ssi_identite_test",SCRIPT)
 module=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(module)
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  module.SRC=d/"DOSSIERS_SSI_A_QUALIFIER.csv"
  module.OUT=d/"PLAN_COLLECTE_PREUVES_SSI.csv"
  module.AUD=d/"AUDIT_COLLECTE_PREUVES_SSI.csv"
  fixture=[]
  for ticker,cik,preuve in [
      ("FICTIF.F","","MANQUANTE"),
      ("FICTIF.US","0000000123","PREUVE_A|PREUVE_B")]:
   row={"Ticker":ticker,"Societe":"Emetteur fictif "+ticker,
        "Pays":"Allemagne" if ticker.endswith(".F") else "USA",
        "CIK":cik,"SCE_valide":"NON",
        "Preuves_identite_SCE":preuve,"Motif_eliminatoire":"MANQUANTE",
        "B6_source":"OBSERVATION_FOURNISSEUR","B6_date":"2026-10-08"}
   for b in ("B1","B2","B3","B4","B5","B6","B7"):
    row["Note_"+b]="MANQUANTE";row["Preuve_"+b]="MANQUANTE"
   fixture.append(row)
  pd.DataFrame(fixture).to_csv(module.SRC,index=False)
  avant=module.SRC.read_bytes()
  out=module.executer()
  assert len(out)==18, "2 dossiers * (2 controles + 7 blocs)"
  assert out.groupby("Ticker").size().to_dict()=={"FICTIF.F":9,"FICTIF.US":9}
  assert set(out.Bloc_SSI)=={"IDENTITE_SCE","EXCLUSIONS","B1","B2","B3","B4","B5","B6","B7"}
  f=out[(out.Ticker=="FICTIF.F") & (out.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
  assert f.Statut=="EN_ATTENTE_DATA_IDENTITE"
  assert f.Identifiant_emetteur_source=="MANQUANTE"
  assert f.Pays_cotation_declare=="Allemagne"
  assert f.Pays_emetteur_verifie=="MANQUANTE"
  u=out[(out.Ticker=="FICTIF.US") & (out.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
  assert u.Identifiant_emetteur_source=="CIK:0000000123"
  assert u.Preuve_validee=="A_CONTROLER", "Une reference ne certifie pas la preuve"
  assert u.Pays_emetteur_verifie=="MANQUANTE"
  assert set(out.Note_presente)=={"NON"}
  assert not (out.Preuve_validee=="OUI").any()
  audit=pd.read_csv(module.AUD).iloc[0]
  assert int(audit.Dossiers)==2
  assert int(audit.Blocs_a_auditer)==14
  assert int(audit.Controles_identite_exclusions)==4
  assert int(audit.Identites_CIK_source_absentes)==1
  assert int(audit.Lignes_plan)==18
  assert module.SRC.read_bytes()==avant, "Le plan ne doit jamais modifier la cohorte source"
  pd.DataFrame(columns=fixture[0].keys()).to_csv(module.SRC,index=False)
  vide=module.executer()
  assert vide.empty and list(vide.columns)==module.COLONNES
  assert int(pd.read_csv(module.AUD).iloc[0].Dossiers)==0
  assert module.SRC.exists()
 print("07Q2 OK : identite/exclusions prioritaires, aucun score, attente non-US, source intacte")

if __name__=="__main__":executer()

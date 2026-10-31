"""Regression 07Q2 hors reseau : identite non US et exclusions avant notation.
Fixtures fictives. Aucun score, document primaire ou ordre financier.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import hashlib
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"SCRIPTS_ACTIFS"))
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
  module.ARCHIVE_IDENTITE=d/"IDENTITE_COTATIONS_MULTIPLES.csv"
  pd.DataFrame([
   {"Ticker":"FICTIF.F","Societe":"Nom sans verification","ISIN":"US0378331005"},
   {"Ticker":"FICTIF.US","Societe":"Autre nom non verifie","ISIN":"US0378331006"}
  ]).to_csv(module.ARCHIVE_IDENTITE,index=False)
  sha_archive=hashlib.sha256(module.ARCHIVE_IDENTITE.read_bytes()).hexdigest()
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
  assert (d/'ANOMALIES_CAPTURES_SSI.csv').exists(), 'Diagnostic 07Q2 doit rester dans la fixture isolee'
  assert len(out)==18, "2 dossiers * (2 controles + 7 blocs)"
  assert out.groupby("Ticker").size().to_dict()=={"FICTIF.F":9,"FICTIF.US":9}
  assert set(out.Bloc_SSI)=={"IDENTITE_SCE","EXCLUSIONS","B1","B2","B3","B4","B5","B6","B7"}
  f=out[(out.Ticker=="FICTIF.F") & (out.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
  assert f.Statut=="EN_ATTENTE_DATA_IDENTITE"
  assert f.Identifiant_emetteur_source=="MANQUANTE"
  assert f.Pays_cotation_declare=="Allemagne"
  assert f.Pays_emetteur_verifie=="MANQUANTE"
  assert f.ISIN_piste_non_certifiee=="US0378331005"
  assert f.Statut_piste_ISIN=="PISTE_ISIN_CHECKSUM_OK_NON_CERTIFIEE"
  assert f.SHA256_archive_ISIN==sha_archive
  assert f.Provenance_archive_ISIN=="DONNEES/IDENTITE_COTATIONS_MULTIPLES.csv"
  assert f.Date_archive_ISIN=="MANQUANTE", "Date source non prouvee, jamais inventee"
  assert f.Preuve_validee=="NON", "Checksum ISIN ne vaut pas verification de preuve"
  assert f.Identifiant_emetteur_source=="MANQUANTE", "Piste non certifiee ne devient pas identite"
  u=out[(out.Ticker=="FICTIF.US") & (out.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
  assert u.Identifiant_emetteur_source=="CIK:0000000123"
  assert u.Preuve_validee=="A_CONTROLER", "Une reference ne certifie pas la preuve"
  assert u.Pays_emetteur_verifie=="MANQUANTE"
  assert u.Statut_piste_ISIN=="ISIN_INVALIDE_ARCHIVE"
  assert u.ISIN_piste_non_certifiee=="MANQUANTE"
  assert u.Identifiant_emetteur_source=="CIK:0000000123"
  assert set(out.Note_presente)=={"NON"}
  assert not (out.Preuve_validee=="OUI").any()
  audit=pd.read_csv(module.AUD).iloc[0]
  assert int(audit.Dossiers)==2
  assert int(audit.Blocs_a_auditer)==14
  assert int(audit.Controles_identite_exclusions)==4
  assert int(audit.Identites_CIK_source_absentes)==1
  assert int(audit.Lignes_plan)==18
  assert int(audit.Pistes_ISIN_checksum_OK_non_certifiees)==1
  assert int(audit.Pistes_ISIN_ambigues_ou_invalides)==1
  assert module.SRC.read_bytes()==avant, "Le plan ne doit jamais modifier la cohorte source"
  # Une identité ISIN formellement valide et déclarée ne doit pas être
  # faussement signalée comme absente par 07Q2, mais elle n'est pas certifiée.
  # Aucun score ni admission ne peut être déduit de cette déclaration.
  candidats=pd.read_csv(module.SRC,dtype=str,keep_default_na=False)
  candidats["Identifiant_emetteur_verifie"]="MANQUANTE"
  candidats.loc[candidats.Ticker.eq("FICTIF.F"),"Identifiant_emetteur_verifie"]="ISIN:US0378331005"
  candidats.to_csv(module.SRC,index=False)
  plan=module.executer()
  identite=plan[(plan.Ticker=="FICTIF.F") & (plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
  assert identite.Identifiant_emetteur_source=="ISIN:US0378331005"
  assert identite.Statut=="A_VERIFIER_IDENTITE_SCE"
  assert identite.Preuve_validee=="NON"
  assert identite.Pays_emetteur_verifie=="MANQUANTE"
  assert not (plan.Preuve_validee=="OUI").any()
  # Un CIK malformé interdit tout repli opportuniste vers un ISIN déclaré.
  candidats.loc[candidats.Ticker.eq("FICTIF.F"),"CIK"]="123"
  candidats.to_csv(module.SRC,index=False)
  plan=module.executer()
  identite=plan[(plan.Ticker=="FICTIF.F") & (plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
  assert identite.Identifiant_emetteur_source=="MANQUANTE"
  assert identite.Statut=="EN_ATTENTE_DATA_IDENTITE"
  # Une collision explicite reste en quarantaine même si le CIK est valide.
  candidats.loc[candidats.Ticker.eq("FICTIF.F"),"CIK"]="0000000123"
  candidats["Conflit_identite_CIK"]="NON"
  candidats.loc[candidats.Ticker.eq("FICTIF.F"),"Conflit_identite_CIK"]="OUI"
  candidats.to_csv(module.SRC,index=False)
  plan=module.executer()
  identite=plan[(plan.Ticker=="FICTIF.F") & (plan.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
  assert identite.Statut=="EN_ATTENTE_DATA_IDENTITE_CIK"
  assert identite.Preuve_validee=="NON"
  assert not (plan.Preuve_validee=="OUI").any()
  pd.DataFrame(columns=fixture[0].keys()).to_csv(module.SRC,index=False)
  vide=module.executer()
  assert vide.empty and list(vide.columns)==module.COLONNES
  assert int(pd.read_csv(module.AUD).iloc[0].Dossiers)==0
  assert module.SRC.exists()
  # Un ticker duplique dans l\'archive ne permet jamais de choisir un ISIN.
  pd.DataFrame(fixture).to_csv(module.SRC,index=False)
  pd.DataFrame([
   {"Ticker":"FICTIF.F","Societe":"A","ISIN":"US0378331005"},
   {"Ticker":"FICTIF.F","Societe":"B","ISIN":"US0378331005"}
  ]).to_csv(module.ARCHIVE_IDENTITE,index=False)
  ambigu=module.executer()
  ligne=ambigu[(ambigu.Ticker=="FICTIF.F") & (ambigu.Bloc_SSI=="IDENTITE_SCE")].iloc[0]
  assert ligne.Statut_piste_ISIN=="TICKER_AMBIGU_ARCHIVE"
  assert ligne.ISIN_piste_non_certifiee=="MANQUANTE"
  assert ligne.Preuve_validee=="NON"
  # Archive sans schema requis : erreur explicite, resultats precedents preserves.
  avant_plan=module.OUT.read_bytes();avant_audit=module.AUD.read_bytes()
  pd.DataFrame([{"Ticker":"FICTIF.F","ISIN":"US0378331005"}]).to_csv(module.ARCHIVE_IDENTITE,index=False)
  try:module.executer()
  except RuntimeError as exc:assert "Schema archive ISIN historique incomplet" in str(exc)
  else:raise AssertionError("Archive ISIN sans nom acceptee")
  assert module.OUT.read_bytes()==avant_plan and module.AUD.read_bytes()==avant_audit
 print("07Q2 OK : 2 controles + 7 blocs, ISIN historique non certifie, checksum, SHA256, ambiguite et source intacte")

if __name__=="__main__":executer()

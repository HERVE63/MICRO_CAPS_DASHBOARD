"""07Q non-US : reprise uniquement si source stable et preuves SCE SHA256 re-verifiees.
Toutes les societes et tous les documents de ce test sont des fixtures fictives.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import hashlib
import shutil
import subprocess
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ISIN_A="ISIN:US0378331005"
ISIN_B="ISIN:US5949181045"

def executer():
 with TemporaryDirectory() as dossier:
  base=Path(dossier)
  scripts=base/"SCRIPTS_ACTIFS";scripts.mkdir()
  donnees=base/"DONNEES";donnees.mkdir()
  for nom in ("07Q_PREPARER_DOSSIERS_SSI.py","preuves_ssi.py"):
   shutil.copy2(ROOT/"SCRIPTS_ACTIFS"/nom,scripts/nom)
  lignes=[]
  for ticker,ident in (("FIX_A.F",ISIN_A),("FIX_B.F",ISIN_B),("FIX_C.F",ISIN_B)):
   lignes.append(dict(Ticker=ticker,CIK="",Societe="Emetteur fictif "+ticker,
     Pays="Allemagne",Capitalisation_EUR="10000000",Cash="100",
     Dette_totale="20",EBITDA="10",FCF="8",Croissance_CA="0.1",
     Marge_brute="0.3",Insiders_pct="0.05",Actions="1000000",
     Source_fondamentaux="SOURCE_TEST_NON_PRIMAIRE",Date_scan_fond="2026-10-01",
     Volume_monetaire_median_63s_local="200000",Momentum_3m_pct="1",
     Momentum_6m_pct="2",Au_dessus_MM200="OUI",
     Identifiant_emetteur_verifie=ident))
  pd.DataFrame(lignes).to_csv(donnees/"CANDIDATS_PRETS_SSI.csv",index=False)
  anciens=[]
  for ticker,ident in (("FIX_A.F",ISIN_A),("FIX_B.F",ISIN_B),("FIX_C.F",ISIN_A)):
   prefix=ticker.split(".")[0]
   anciens.append(dict(Ticker=ticker,CIK="",Identifiant_emetteur_verifie=ident,
     SCE_valide="OUI",Preuves_identite_SCE=prefix+"1|"+prefix+"2",
     Conflit_identite_CIK="NON",Note_B1="12",Preuve_B1="ANCIENNE_NOTE_"+prefix,
     Decision_eliminatoire="NON",Motif_eliminatoire="EXCLUSION_"+prefix))
  pd.DataFrame(anciens).to_csv(donnees/"DOSSIERS_SSI_A_QUALIFIER.csv",index=False)
  from sys import path
  path.insert(0,str(scripts))
  from preuves_ssi import CHAMPS
  preuves=[]
  for prefix,ticker,ident in (("FIX_A","FIX_A.F",ISIN_A),("FIX_B","FIX_B.F",ISIN_B)):
   for i in (1,2):
    fichier=donnees/(prefix+str(i)+".txt")
    fichier.write_text("Fixture identite "+prefix+" "+str(i),encoding="utf-8")
    sha=hashlib.sha256(fichier.read_bytes()).hexdigest()
    if prefix=="FIX_B" and i==2:
     sha="0"*64  # Document non concordant : B doit etre purge sans bloquer A.
    preuve=dict.fromkeys(CHAMPS,"")
    preuve.update(ID_preuve=prefix+str(i),Remplace_ID="",Ticker=ticker,
     Bloc="IDENTITE_SCE",Identifiant_emetteur=ident,
     Source_URL="https://example.org/fixture/"+prefix+"/"+str(i),
     Type_source="DEPOT_REGLEMENTAIRE",Date_publication="2026-09-01",
     Fichier_brut="DONNEES/"+fichier.name,SHA256=sha,
     Statut_identite="VERIFIEE",Statut_verification="VERIFIEE",
     Verificateur="TEST_HORS_RESEAU",Date_verification_UTC="2026-09-02T00:00:00+00:00",
     Justification="Fixture fictive, aucune qualification economique",Note="")
    preuves.append(preuve)
  pd.DataFrame(preuves,columns=CHAMPS).to_csv(donnees/"REGISTRE_PREUVES_SSI.csv",index=False)
  script=scripts/"07Q_PREPARER_DOSSIERS_SSI.py"
  def lancer():
   p=subprocess.run([sys.executable,"-B",str(script)],cwd=base,text=True,capture_output=True)
   assert p.returncode==0,(p.stdout,p.stderr)
   return pd.read_csv(donnees/"DOSSIERS_SSI_A_QUALIFIER.csv",
                      dtype=str,keep_default_na=False).set_index("Ticker")
  resultat=lancer()
  assert len(resultat)==3
  assert resultat.loc["FIX_A.F","Identifiant_emetteur_verifie"]==ISIN_A
  assert resultat.loc["FIX_A.F","Preuve_B1"]=="ANCIENNE_NOTE_FIX_A"
  assert resultat.loc["FIX_A.F","Note_B1"]=="12"
  assert resultat.loc["FIX_A.F","SCE_valide"]=="OUI"
  assert resultat.loc["FIX_A.F","Statut_SSI"]=="A_REVALIDER_PREUVES_SSI"
  for ticker in ("FIX_B.F","FIX_C.F"):
   assert resultat.loc[ticker,"Identifiant_emetteur_verifie"]=="MANQUANTE"
   assert resultat.loc[ticker,"Preuve_B1"]=="MANQUANTE"
   assert resultat.loc[ticker,"Note_B1"]=="MANQUANTE"
   assert resultat.loc[ticker,"SCE_valide"]=="NON"
   assert resultat.loc[ticker,"Statut_SSI"]=="EN_ATTENTE_DATA_IDENTITE_CIK"
  audit=pd.read_csv(donnees/"AUDIT_DOSSIERS_SSI.csv").iloc[0]
  assert int(audit.Reprises_identite_ISIN_LEI_sur_preuves)==1
  resultat2=lancer()
  assert resultat2.loc["FIX_A.F","Preuve_B1"]=="ANCIENNE_NOTE_FIX_A"
  assert int(pd.read_csv(donnees/"AUDIT_DOSSIERS_SSI.csv").iloc[0].Reprises_identite_ISIN_LEI_sur_preuves)==1
  # La perte d integrite du document primaire interdit aussi la reprise suivante.
  (donnees/"FIX_A1.txt").write_text("CORROMPU",encoding="utf-8")
  resultat3=lancer()
  assert resultat3.loc["FIX_A.F","Identifiant_emetteur_verifie"]=="MANQUANTE"
  assert resultat3.loc["FIX_A.F","Preuve_B1"]=="MANQUANTE"
  assert resultat3.loc["FIX_A.F","SCE_valide"]=="NON"
  assert int(pd.read_csv(donnees/"AUDIT_DOSSIERS_SSI.csv").iloc[0].Reprises_identite_ISIN_LEI_sur_preuves)==0
  assert not (resultat3["SSI"]!="MANQUANTE").any()
 print("07Q non-US OK : 1 reprise SCE re-verifiee, 2 quarantaines, SHA invalide => purge")

if __name__=="__main__":
 executer()

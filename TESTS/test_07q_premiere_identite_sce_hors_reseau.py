"""Premiere identite non-US 07Q : uniquement deux preuves primaires SCE SHA256.
Fixtures fictives hors reseau, aucun score, aucune transaction.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import shutil
import subprocess
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ISIN="ISIN:FR001400A3Q3"

def executer():
 with TemporaryDirectory() as tmp:
  base=Path(tmp);scripts=base/"SCRIPTS_ACTIFS";scripts.mkdir()
  data=base/"DONNEES";data.mkdir()
  for nom in ("07Q_PREPARER_DOSSIERS_SSI.py","preuves_ssi.py"):
   shutil.copy2(ROOT/"SCRIPTS_ACTIFS"/nom,scripts/nom)
  sys.path.insert(0,str(scripts))
  from preuves_ssi import CHAMPS
  lignes=[]
  for ticker,cik,ids in (
      ("GOOD.F","","GOOD_1|GOOD_2"),
      ("BAD_SHA.F","","BAD_1|BAD_2"),
      ("ONE_PROOF.F","","ONE_1"),
      ("BAD_CIK.F","123","CIK_1|CIK_2"),
      ("COLLISION.F","","COL_1|COL_2")):
   lignes.append(dict(Ticker=ticker,CIK=cik,Societe="Emetteur fictif "+ticker,
    Pays="Allemagne",Capitalisation_EUR="10000000",Cash="100",Dette_totale="20",
    EBITDA="10",FCF="8",Croissance_CA="0.1",Marge_brute="0.3",
    Insiders_pct="0.05",Actions="1000000",
    Source_fondamentaux="FOURNISSEUR_NON_PRIMAIRE",Date_scan_fond="2026-10-01",
    Volume_monetaire_median_63s_local="200000",Momentum_3m_pct="1",
    Momentum_6m_pct="2",Au_dessus_MM200="OUI",
    Identifiant_emetteur_verifie=ISIN,SCE_valide="OUI",
    Preuves_identite_SCE=ids))
  pd.DataFrame(lignes).to_csv(data/"CANDIDATS_PRETS_SSI.csv",index=False)
  # Collision historique explicite : aucune nouvelle source ne la leve.
  pd.DataFrame([{"Ticker":"COLLISION.F","CIK":"",
    "Identifiant_emetteur_verifie":"MANQUANTE",
    "SCE_valide":"NON","Preuves_identite_SCE":"MANQUANTE",
    "Conflit_identite_CIK":"OUI"}]).to_csv(
      data/"DOSSIERS_SSI_A_QUALIFIER.csv",index=False)
  preuves=[]
  for ligne in lignes:
   ticker=ligne["Ticker"]
   for i,preuve_id in enumerate(ligne["Preuves_identite_SCE"].split("|")):
    fichier=data/(preuve_id+".txt")
    fichier.write_text("Document de test fictif "+preuve_id,encoding="utf-8")
    sha=hashlib.sha256(fichier.read_bytes()).hexdigest()
    if ticker=="BAD_SHA.F" and i==1:sha="0"*64
    p=dict.fromkeys(CHAMPS,"")
    p.update(ID_preuve=preuve_id,Ticker=ticker,Bloc="IDENTITE_SCE",
     Identifiant_emetteur=ISIN,Source_URL="https://example.org/test/"+preuve_id,
     Type_source="DEPOT_REGLEMENTAIRE",Date_publication="2026-09-01",
     Fichier_brut="DONNEES/"+fichier.name,SHA256=sha,
     Statut_identite="VERIFIEE",Statut_verification="VERIFIEE",
     Verificateur="TEST_HORS_RESEAU",
     Date_verification_UTC="2026-09-02T00:00:00+00:00",
     Justification="Fixture sans verification financiere",Note="")
    preuves.append(p)
  pd.DataFrame(preuves,columns=CHAMPS).to_csv(
    data/"REGISTRE_PREUVES_SSI.csv",index=False)
  def lancer():
   p=subprocess.run([sys.executable,"-B",str(scripts/"07Q_PREPARER_DOSSIERS_SSI.py")],
     cwd=base,capture_output=True,text=True)
   assert p.returncode==0,(p.stdout,p.stderr)
   return pd.read_csv(data/"DOSSIERS_SSI_A_QUALIFIER.csv",
      dtype=str,keep_default_na=False).set_index("Ticker")
  d=lancer()
  assert len(d)==5
  good=d.loc["GOOD.F"]
  assert good.Identifiant_emetteur_verifie==ISIN
  assert good.SCE_valide=="OUI"
  assert good.Preuves_identite_SCE=="GOOD_1|GOOD_2"
  assert good.Statut_SSI=="A_REVALIDER_PREUVES_SSI"
  assert good.Note_B1=="MANQUANTE" and good.SSI=="MANQUANTE"
  for ticker in ("BAD_SHA.F","ONE_PROOF.F","BAD_CIK.F","COLLISION.F"):
   r=d.loc[ticker]
   assert r.Identifiant_emetteur_verifie=="MANQUANTE",ticker
   assert r.SCE_valide=="NON" and r.SSI=="MANQUANTE",ticker
  assert d.loc["COLLISION.F","Conflit_identite_CIK"]=="OUI"
  a=pd.read_csv(data/"AUDIT_DOSSIERS_SSI.csv").iloc[0]
  assert int(a.Nouvelles_identites_ISIN_LEI_sur_preuves)==1
  assert int(a.SSI_admis_65)==0
  # La reprise sur le second passage ne doit pas creer de note ou d'admission.
  d2=lancer()
  assert d2.loc["GOOD.F","Identifiant_emetteur_verifie"]==ISIN
  assert d2.loc["GOOD.F","SSI"]=="MANQUANTE"
  # Une piece modifiee invalide aussi la nouvelle introduction.
  (data/"GOOD_1.txt").write_text("CORROMPU",encoding="utf-8")
  d3=lancer()
  assert d3.loc["GOOD.F","Identifiant_emetteur_verifie"]=="MANQUANTE"
  assert d3.loc["GOOD.F","SCE_valide"]=="NON"
  assert d3.loc["GOOD.F","SSI"]=="MANQUANTE"
  assert int(pd.read_csv(data/"AUDIT_DOSSIERS_SSI.csv").iloc[0].Nouvelles_identites_ISIN_LEI_sur_preuves)==0
 print("07Q premiere identite : 1 SCE revalidee, SHA invalide/CIK/collision isoles, zero score")

if __name__=="__main__":executer()

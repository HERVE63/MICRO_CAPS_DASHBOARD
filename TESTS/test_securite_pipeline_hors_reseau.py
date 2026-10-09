"""Régressions : preuve fictive, date future, conservation, 65/64 et frais."""
import hashlib, importlib.util, json, sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'SCRIPTS_ACTIFS'))
from preuves_ssi import MAX, CHAMPS

def charger(name):
 s=importlib.util.spec_from_file_location(name[:-3],ROOT/'SCRIPTS_ACTIFS'/name)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_preuves():
 with TemporaryDirectory() as tmp:
  b=Path(tmp);d=b/'DONNEES';d.mkdir();f=b/'preuve.bin';f.write_bytes(b'TEST FIXTURE - NOT A REAL ISSUER DOCUMENT')
  notes=[15,10,10,15,5,5,5] # seuil exact 65
  row={'Ticker':'TEST','Societe':'TEST','Decision_eliminatoire':'NON','Motif_eliminatoire':'EX',
       'SSI':'MANQUANTE','Statut_SSI':'A_COMPLETER'}
  preuves=[]
  for bloc,n in zip(MAX,notes):
   row['Note_'+bloc]=str(n);row['Preuve_'+bloc]=bloc
   preuves.append({'ID_preuve':bloc,'Remplace_ID':'','Ticker':'TEST','Bloc':bloc,
    'Identifiant_emetteur':'CIK:0000001234','Source_URL':'https://www.sec.gov/Archives/test',
    'Type_source':'DEPOT_REGLEMENTAIRE','Date_publication':'2026-01-01','Fichier_brut':'preuve.bin',
    'SHA256':hashlib.sha256(f.read_bytes()).hexdigest(),'Statut_identite':'VERIFIEE',
    'Statut_verification':'VERIFIEE','Verificateur':'TEST_FIXTURE','Date_verification_UTC':'2026-02-01T00:00:00Z',
    'Justification':'TEST: vérification documentée du critère','Note':str(n)})
  preuves.append(dict(preuves[0],ID_preuve='EX',Bloc='EXCLUSIONS',Note=''))
  pd.DataFrame(preuves,columns=CHAMPS).to_csv(d/'REGISTRE_PREUVES_SSI.csv',index=False)
  source=d/'DOSSIERS_SSI_A_QUALIFIER.csv';pd.DataFrame([row]).to_csv(source,index=False)
  m=charger('07R_VALIDER_NOTES_SSI.py')
  with patch.object(m,'D',d),patch.object(m,'SRC',source),patch.object(m,'OUT',d/'RESULTATS_SSI.csv'),patch.object(m,'AUD',d/'AUDIT_SSI.csv'):
   result=m.executer();assert result.iloc[0].SSI=='65' and result.iloc[0].Statut_SSI=='ADMIS_SSI'
   row['Note_B1']='14';preuves[0]['Note']='14'
   pd.DataFrame([row]).to_csv(source,index=False);pd.DataFrame(preuves).to_csv(d/'REGISTRE_PREUVES_SSI.csv',index=False)
   result=m.executer();assert result.iloc[0].SSI=='64' and result.iloc[0].Statut_SSI=='REFUSE_SSI'
   row['Preuve_B1']='https://source-texte-fictif';pd.DataFrame([row]).to_csv(source,index=False)
   assert m.executer().iloc[0].Statut_SSI=='A_COMPLETER_PREUVES_SSI'
   row['Preuve_B1']='B1';pd.DataFrame([row]).to_csv(source,index=False)
   f.write_bytes(b'TAMPERED');assert m.executer().iloc[0].Statut_SSI=='A_COMPLETER_PREUVES_SSI'
   f.write_bytes(b'TEST FIXTURE - NOT A REAL ISSUER DOCUMENT')
   preuves[0]['Date_publication']='2099-01-01';pd.DataFrame(preuves).to_csv(d/'REGISTRE_PREUVES_SSI.csv',index=False)
   assert m.executer().iloc[0].Statut_SSI=='A_COMPLETER_PREUVES_SSI'
 print('PREUVES: seuil 65/64, texte fictif, document modifié et date future contrôlés')

def test_conservation():
 with TemporaryDirectory() as tmp:
  b=Path(tmp);d=b/'DONNEES';d.mkdir()
  candidat=pd.read_csv(ROOT/'DONNEES/CANDIDATS_PRETS_SSI.csv').head(1)
  candidat.to_csv(d/'CANDIDATS_PRETS_SSI.csv',index=False)
  m=charger('07Q_PREPARER_DOSSIERS_SSI.py')
  with patch.object(m,'B',b),patch.object(m,'D',d),patch.object(m,'SRC',d/'CANDIDATS_PRETS_SSI.csv'),patch.object(m,'OUT',d/'DOSSIERS_SSI_A_QUALIFIER.csv'),patch.object(m,'AUD',d/'AUDIT_DOSSIERS_SSI.csv'):
   result=m.executer();result['Note_B1']='17';result['Preuve_B1']='HUMAN_PROOF';result['Correction_identite']='TEST_CORRECTION'
   result.to_csv(m.OUT,index=False);m.executer()
   re=pd.read_csv(m.OUT,dtype=str);assert re.iloc[0].Note_B1=='17' and re.iloc[0].Preuve_B1=='HUMAN_PROOF'
   assert re.iloc[0].Correction_identite=='TEST_CORRECTION'
   assert len(list((b/'AUDITS/DOSSIERS_SSI').glob('*/DOSSIERS_SSI_A_QUALIFIER.csv')))==1
 print('CONSERVATION: notes, preuves, corrections et archive précédente contrôlées')

def test_hors_fenetre_et_frais():
 m=charger('10_EXECUTION_MENSUELLE.py')
 with patch.dict(m.os.environ,{'MICRO_CAPS_FORCE_MENSUEL':'1','MICRO_CAPS_DRY_RUN':'0'}):
  try:m.executer()
  except RuntimeError as e:assert 'exception grave' in str(e)
  else:raise AssertionError('Force réel a contourné fenêtre')
 achat,vente=m.taux();assert achat==vente==.025
 assert abs(100*(1-vente)/(1+achat)-95.1219512195122)<1e-10
 assert m.dernier_mardi(pd.Timestamp('2026-10-27').date())
 assert not m.dernier_mardi(pd.Timestamp('2026-10-20').date())
 print('CALENDRIER/FRAIS: 2,5% sur chaque côté, absence de forçage réel')

def test_t0():
 m=charger('07AC_CONTROLER_T0.py')
 with TemporaryDirectory() as tmp:
  b=Path(tmp);(b/'CONFIG').mkdir();p=b/'T0.csv';p.write_bytes(b'ORIGINAL')
  (b/'CONFIG/EMPREINTES_T0.json').write_text(json.dumps({'fichiers':{'T0.csv':hashlib.sha256(p.read_bytes()).hexdigest()}}))
  with patch.object(m,'BASE',b):
   m.executer();p.write_bytes(b'CORRUPT')
   try:m.executer()
   except RuntimeError:pass
   else:raise AssertionError('Mutation T0 acceptée')
 print('T0: modification de référence rejetée avant valorisation')

def test_asof_et_cik():
 m=charger('07V_NORMALISER_FAITS_SEC.py')
 with TemporaryDirectory() as tmp:
  d=Path(tmp)
  row={'Ticker':'TEST','CIK':'0000001234','Concept':'Cash','Tag_SEC':'CashAndCashEquivalentsAtCarryingValue','Valeur':'100','Unite':'USD','Debut_periode':'','Fin_periode':'2025-12-31','Date_depot':'2026-02-01','Formulaire':'10-K','Accession':'0000001234-26-000001','Exercice':'2025','Periode':'FY','Source_officielle':'https://data.sec.gov/test','Date_collecte_UTC':'2026-03-01T00:00:00Z','Statut_preuve':'A_VERIFIER'}
  pd.DataFrame([row,dict(row,Valeur='999',Date_depot='2026-03-01')]).to_csv(d/'FAITS_FINANCIERS_SEC_SSI.csv',index=False)
  with patch.object(m,'SRC',d/'FAITS_FINANCIERS_SEC_SSI.csv'),patch.object(m,'OUT',d/'FAITS_SEC_COMPARABLES_SSI.csv'),patch.object(m,'AUD',d/'AUDIT_COMPARABILITE_SEC_SSI.csv'),patch.dict(m.os.environ,{'MICRO_CAPS_AS_OF':'2026-02-15'}):
   r=m.executer();assert len(r)==1 and r.iloc[0].Valeur=='100'
 t=charger('07T_ENRICHIR_PREUVES_SEC_EDGAR.py')
 with TemporaryDirectory() as tmp:
  d=Path(tmp);pd.DataFrame([{'Ticker':'TEST','Societe':'TEST'}]).to_csv(d/'DOSSIERS.csv',index=False)
  def faux(url,agent):return {'0':{'ticker':'TEST','cik_str':1234}} if 'company_tickers' in url else {'cik':9999,'name':'Wrong issuer'}
  with patch.object(t,'SRC',d/'DOSSIERS.csv'),patch.object(t,'OUT',d/'OUT.csv'),patch.object(t,'AUD',d/'AUD.csv'),patch.object(t,'lire_json',side_effect=faux),patch.object(t.time,'sleep'),patch.dict(t.os.environ,{'SEC_USER_AGENT':'TEST contact@example.org'}):
   r=t.executer();assert r.iloc[0].Statut_SEC=='ERREUR_SOURCE' and r.iloc[0].Nb_depots==0
 print('PIT/IDENTITE: dépôt postérieur exclu, CIK submissions divergent refusé')

if __name__=='__main__':
 test_preuves();test_conservation();test_hors_fenetre_et_frais();test_t0();test_asof_et_cik()

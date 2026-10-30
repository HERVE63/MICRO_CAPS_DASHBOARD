"""Notes partielles prouvées, plafond conditionnel, aucune admission implicite."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,importlib.util,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'SCRIPTS_ACTIFS'))
from preuves_ssi import CHAMPS,bilan_blocs_documentes

def charger(nom):
 s=importlib.util.spec_from_file_location(nom[:-3],ROOT/'SCRIPTS_ACTIFS'/nom)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test():
 with TemporaryDirectory() as tmp:
  root=Path(tmp);d=root/'DONNEES';d.mkdir();raw=root/'fixture.bin';raw.write_bytes(b'EXEMPLE DE TEST - AUCUNE DONNEE REELLE')
  rows=[];dossier={'Ticker':'FIXTURE.US','CIK':'0000001234','SCE_valide':'NON','Preuves_identite_SCE':'MANQUANTE','Conflit_identite_CIK':'NON','Decision_eliminatoire':'A_VERIFIER','Motif_eliminatoire':'MANQUANTE'}
  for n in range(1,8):dossier['Note_B'+str(n)]='MANQUANTE';dossier['Preuve_B'+str(n)]='MANQUANTE'
  for bloc,note in {'B1':8,'B2':5,'B3':3,'B6':8}.items():
   r=dict.fromkeys(CHAMPS,'');r.update(ID_preuve='FIX_'+bloc,Ticker='FIXTURE.US',Bloc=bloc,Identifiant_emetteur='CIK:0000001234',Source_URL='https://example.org/fixture',Type_source='DEPOT_REGLEMENTAIRE',Date_publication='2026-01-01',Fichier_brut='fixture.bin',SHA256=hashlib.sha256(raw.read_bytes()).hexdigest(),Statut_identite='VERIFIEE',Statut_verification='VERIFIEE',Verificateur='Fixture',Date_verification_UTC='2026-01-02T00:00:00+00:00',Justification='EXEMPLE de test seulement',Note=str(note));rows.append(r)
   dossier['Note_'+bloc]=str(note);dossier['Preuve_'+bloc]=r['ID_preuve']
  preuves=pd.DataFrame(rows);r=pd.Series(dossier);b=bilan_blocs_documentes(r,preuves,root)
  assert b['Nombre_blocs_SSI_documentes']==4 and b['Points_sur_blocs_documentes']==24 and b['Maximum_blocs_documentes']==60 and b['Plafond_SSI_si_blocs_restants_maximaux']==64
  autres=preuves.copy();autres.loc[0,'Identifiant_emetteur']='CIK:0000009999'
  assert bilan_blocs_documentes(r,autres,root)['Nombre_blocs_SSI_documentes']==3
  autre=r.copy();autre['Note_B1']='9'
  assert bilan_blocs_documentes(autre,preuves,root)['Nombre_blocs_SSI_documentes']==3
  preuves.to_csv(d/'REGISTRE_PREUVES_SSI.csv',index=False);pd.DataFrame([dossier]).to_csv(d/'DOSSIERS_SSI_A_QUALIFIER.csv',index=False)
  m=charger('07R_VALIDER_NOTES_SSI.py')
  with patch.object(m,'D',d),patch.object(m,'SRC',d/'DOSSIERS_SSI_A_QUALIFIER.csv'),patch.object(m,'OUT',d/'RESULTATS_SSI.csv'),patch.object(m,'AUD',d/'AUDIT_SSI.csv'):
   result=m.executer()
  assert result.iloc[0].SSI=='MANQUANTE' and result.iloc[0].Statut_SSI=='A_COMPLETER_PREUVES_SSI'
  # Le refus par plafond exige identité SCE et contrôle négatif des exclusions prouvés.
  ex=rows[0].copy();ex.update(ID_preuve='FIX_EX',Bloc='EXCLUSIONS',Note='');identites=[]
  for i in range(2):
   ident=ex.copy();ident.update(ID_preuve='FIX_ID_'+str(i),Bloc='IDENTITE_SCE',Source_URL='https://example.org/identite/'+str(i));identites.append(ident)
  preuves=pd.concat([preuves,pd.DataFrame([ex,*identites])],ignore_index=True)
  preuves.to_csv(d/'REGISTRE_PREUVES_SSI.csv',index=False)
  dossier.update(SCE_valide='OUI',Preuves_identite_SCE='FIX_ID_0|FIX_ID_1',Decision_eliminatoire='NON',Motif_eliminatoire='FIX_EX')
  pd.DataFrame([dossier]).to_csv(d/'DOSSIERS_SSI_A_QUALIFIER.csv',index=False)
  with patch.object(m,'D',d),patch.object(m,'SRC',d/'DOSSIERS_SSI_A_QUALIFIER.csv'),patch.object(m,'OUT',d/'RESULTATS_SSI.csv'),patch.object(m,'AUD',d/'AUDIT_SSI.csv'):
   result=m.executer()
  assert result.iloc[0].Statut_SSI=='REFUSE_SSI_PLAFOND_VERIFIE' and result.iloc[0].SSI=='MANQUANTE'
  dossier['Motif_eliminatoire']='ABSENTE';pd.DataFrame([dossier]).to_csv(d/'DOSSIERS_SSI_A_QUALIFIER.csv',index=False)
  with patch.object(m,'D',d),patch.object(m,'SRC',d/'DOSSIERS_SSI_A_QUALIFIER.csv'),patch.object(m,'OUT',d/'RESULTATS_SSI.csv'),patch.object(m,'AUD',d/'AUDIT_SSI.csv'):
   assert m.executer().iloc[0].Statut_SSI=='A_COMPLETER_PREUVES_SSI'
  raw.write_bytes(b'CORROMPU');assert bilan_blocs_documentes(r,preuves,root)['Nombre_blocs_SSI_documentes']==0
  # Le raccordement accepte les notes documentaires sans effacer une correction humaine.
  al=charger('07AL_RACCORDER_SCE_DISCOVERY_SSI_US.py')
  ordre=[{'Ticker':'FIXTURE.US','Societe':'FIXTURE','CIK':'0000001234','Statut_SCE':'A_COMPLETER','SCE_valide':'NON','Rang_controle_SCE':'1'}]
  cols=['Ticker',*[p+'B'+str(n) for n in range(1,8) for p in ['Note_','Preuve_']]]
  note=dict.fromkeys(cols,'');note.update(Ticker='FIXTURE.US',Note_B1='8',Preuve_B1='FIX_B1');doc=pd.DataFrame([note])
  humain=pd.DataFrame([{'Ticker':'FIXTURE.US','Note_B1':'9','Preuve_B1':'CORRECTION'}]);avant=humain.copy(deep=True)
  q=al.dossiers_ssi(ordre,humain,notes_documentaires=doc);assert q.iloc[0].Note_B1=='9' and q.iloc[0].Preuve_B1=='CORRECTION';pd.testing.assert_frame_equal(humain,avant)
  for mauvais in [doc.assign(Decision_eliminatoire='NON'),doc.assign(Preuve_B1=''),doc.assign(Ticker='AUTRE.US')]:
   try:al.dossiers_ssi(ordre,humain,notes_documentaires=mauvais)
   except RuntimeError:pass
   else:raise AssertionError('Notes documentaires hors schéma acceptées')
 print('Notes partielles : preuves/CIK/empreintes concordants, plafond sans admission, correction humaine prioritaire')
if __name__=='__main__':test()

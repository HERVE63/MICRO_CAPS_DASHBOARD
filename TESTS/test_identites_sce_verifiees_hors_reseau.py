"""Réouverture SCE uniquement sur deux preuves concordantes et archives intactes."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib,importlib.util,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'SCRIPTS_ACTIFS'))
from preuves_ssi import CHAMPS
s=importlib.util.spec_from_file_location('sce',ROOT/'SCRIPTS_ACTIFS/07AL_RACCORDER_SCE_DISCOVERY_SSI_US.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 with TemporaryDirectory() as tmp:
  base=Path(tmp);p=base/'fixture';p.write_bytes(b'EXEMPLE TEST SANS EMETTEUR REEL')
  isin='US0378331005';d=[dict(Ticker_US='FIX.US',CIK='0000001234',ISIN_catalogue=isin,Capitalisation_EUR='100000000',Lien_ticker_CIK='CONCORDANCE_EXACTE_SEC',Statut_origine='PISTE_US_CONCORDANTE')]
  ins={'FIX.US':{'Statut_instrument':'ABSENT_REPERTOIRES_LISTES_OTC_OU_IDENTITE_A_COMPLETER'}};proof=[]
  for i,b in enumerate(['IDENTITE_SCE','IDENTITE_SCE','EXCLUSIONS']):
   r=dict.fromkeys(CHAMPS,'');r.update(ID_preuve='FIX_'+str(i),Ticker='FIX.US',Bloc=b,Identifiant_emetteur='CIK:0000001234',Source_URL='https://example.org/test/'+str(i),Type_source='DEPOT_REGLEMENTAIRE',Date_publication='2026-01-01',Fichier_brut='fixture',SHA256=hashlib.sha256(p.read_bytes()).hexdigest(),Statut_identite='VERIFIEE',Statut_verification='VERIFIEE',Verificateur='Fixture',Date_verification_UTC='2026-01-02T00:00:00+00:00',Justification='Fixture, pas une qualification réelle');proof.append(r)
  proofs=pd.DataFrame(proof);reviews=pd.DataFrame([dict(Ticker='FIX.US',CIK='0000001234',ISIN=isin,Preuves_identite='FIX_0|FIX_1',Preuve_exclusions='FIX_2',Recensement_SHA256='ABC',Statut_revue='VERIFIEE')])
  def result(v=reviews,q=proofs):return m.appliquer_revues(m.ordonner(d,ins),v,q,base,'ABC')[0]
  assert result()['SCE_valide']=='OUI'
  for bad in [reviews.assign(CIK='0000009999'),reviews.assign(ISIN='US0378331006'),reviews.assign(Recensement_SHA256='OLD'),reviews.assign(Preuves_identite='FIX_0'),reviews.assign(Preuve_exclusions='ABSENTE')]:assert result(bad)['SCE_valide']=='NON'
  other=proofs.copy();other.loc[0,'Identifiant_emetteur']='CIK:0000009999';assert result(q=other)['SCE_valide']=='NON'
  same=proofs.copy();same.loc[1,'Source_URL']=same.loc[0,'Source_URL'];assert result(q=same)['SCE_valide']=='NON'
  ordre=m.appliquer_revues(m.ordonner(d,ins),reviews,proofs,base,'ABC');q=m.dossiers_ssi(ordre,pd.DataFrame(columns=['Ticker']));assert q.iloc[0].Decision_eliminatoire=='NON' and q.iloc[0].Motif_eliminatoire=='FIX_2'
  q=m.dossiers_ssi(ordre,pd.DataFrame([dict(Ticker='FIX.US',Decision_eliminatoire='OUI',Motif_eliminatoire='CORRECTION_HUMAINE')]));assert q.iloc[0].Decision_eliminatoire=='OUI'
  p.write_bytes(b'CORROMPU');assert result()['SCE_valide']=='NON'
 print('SCE vérifié : identité/ISIN/source/dénominateur/archives contrôlés ; corrections humaines prioritaires')
if __name__=='__main__':test()

"""Ordre maître sans privilège, ISIN, conservation des corrections et zéro note créée."""
from pathlib import Path
import importlib.util
import pandas as pd
s=importlib.util.spec_from_file_location('sce_us',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AL_RACCORDER_SCE_DISCOVERY_SSI_US.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 assert m.isin_valide('US0378331005') and not m.isin_valide('US0378331006')
 assert not m.isin_valide('MANQUANTE')
 base={'Capitalisation_EUR':'50000000','ISIN_catalogue':'US0378331005','Lien_ticker_CIK':'CONCORDANCE_EXACTE_SEC','Statut_origine':'PISTE_US_CONCORDANTE'}
 d=[dict(base,Ticker_US='P.US'),dict(base,Ticker_US='SECOND.US'),
    dict(base,Ticker_US='SANSISIN.US',ISIN_catalogue='',Capitalisation_EUR='300000001')]
 instruments={r['Ticker_US']:{'Statut_instrument':'ACTION_ORDINAIRE_LIBELLE_OFFICIEL'} for r in d}
 ordre=m.ordonner(d,instruments)
 assert ordre==m.ordonner(list(reversed(d)),instruments)
 assert len(ordre)==3 and all(x['SCE_valide']=='NON' and x['SSI']=='MANQUANTE' for x in ordre)
 assert sum(x['Doublons_ISIN']==2 for x in ordre)==2
 assert all('DOUBLON_ISIN_COTATION_PRIMAIRE_A_CONFIRMER' in x['Motifs'] for x in ordre if x['Doublons_ISIN']==2)
 assert 'HORS_MANDAT_CAPITALISATION' in next(x for x in ordre if x['Ticker']=='SANSISIN.US')['Motifs']
 humains=pd.DataFrame([{'Ticker':'P.US','Note_B4':'15','Preuve_B4':'FIXTURE_PREUVE_NON_VALIDEE','Correction_commentaire':'ne pas effacer'}])
 avant=humains.copy(deep=True);q=m.dossiers_ssi(ordre,humains)
 assert q.set_index('Ticker').loc['P.US','Note_B4']=='15'
 assert q.set_index('Ticker').loc['P.US','Correction_commentaire']=='ne pas effacer'
 assert q.set_index('Ticker').loc['SECOND.US','Note_B4']=='MANQUANTE'
 pd.testing.assert_frame_equal(humains,avant)
 try:m.dossiers_ssi(ordre,pd.concat([humains,humains]))
 except RuntimeError as e:assert 'DUPLIQUE' in str(e)
 else:raise AssertionError('Registre humain ambigu accepté')
 doc=pd.DataFrame([{'Ticker':'SECOND.US','Decision_eliminatoire':'OUI','Motif_eliminatoire':'PREUVE_EXCLUSION'}])
 q=m.dossiers_ssi(ordre,humains,doc).set_index('Ticker')
 assert q.loc['SECOND.US','Decision_eliminatoire']=='OUI' and q.loc['SECOND.US','Note_B4']=='MANQUANTE'
 correction=pd.DataFrame([{'Ticker':'SECOND.US','Decision_eliminatoire':'NON','Motif_eliminatoire':'CORRECTION_HUMAINE'}])
 assert m.dossiers_ssi(ordre,correction,doc).set_index('Ticker').loc['SECOND.US','Decision_eliminatoire']=='NON'
 for mauvais in [doc.assign(Note_B4='20'),doc.assign(Decision_eliminatoire='NON'),doc.assign(Ticker='INCONNU.US')]:
  try:m.dossiers_ssi(ordre,humains,mauvais)
  except RuntimeError:pass
  else:raise AssertionError('Revue documentaire trop permissive')
 print('SCE maître : ordre indépendant du fournisseur, dénominateur, ISIN, doublons et champs humains conservés sans note inventée')
if __name__=='__main__':test()

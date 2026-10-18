"""Une analyse chiffrée ne contourne ni SSI, ni frais, ni probabilités."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib,importlib.util,json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('as_us',ROOT/'SCRIPTS_ACTIFS/07AS_RACCORDER_SSI_MCPA_US.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 with TemporaryDirectory() as tmp:
  p=Path(tmp);(p/'DONNEES').mkdir();co=p/'DONNEES/COHORTE_MICRO_CAPS_T0.csv';co.write_text('FIXTURE SANS POSITION REELLE')
  ref={x+str(n):'FIXTURE_'+x+str(n) for n in range(1,8) for x in ['Note_B','Preuve_B']};ssi=pd.Series(dict(Ticker='FIX.US',SSI='70',Statut_SSI='ADMIS_SSI',SCE_valide='OUI',**ref))
  notes=pd.DataFrame([dict(Ticker='FIX.US',Bloc=b,Note=n,Maximum=x,Justification='Fixture fictive de test') for b,n,x in [('Q',24,30),('V',13,20),('G',13,20),('R',6,10),('M',8,10),('D',8,10)]]);notes.to_csv(p/'NOTES_MCPA_JUSTIFIEES.csv',index=False)
  pd.DataFrame([dict(Bloc=str(i),Note_sur_20=15,Poids_pct=20) for i in range(5)]).to_csv(p/'WWWS.csv',index=False)
  scenarios=pd.DataFrame([dict(Horizon_mois=h,Scenario=s,Probabilite_jugement_pct=pr,Variation_prix_hypothese_pct=r,Rendement_apres_achat_vente_2_5_pct=((1+r/100)*.975/1.025-1)*100) for h in [3,6] for s,pr,r in [('BEAR',25,-10),('CENTRAL',50,3),('BULL',25,15)]]);scenarios.to_csv(p/'SCENARIOS_3_6_MOIS.csv',index=False)
  j=dict(Ticker='FIX.US',Date_analyse_UTC='2026-01-01T00:00:00+00:00',SSI=70,MCPA=72,IC_sur_5=3,CX_sur_5=2,WWWS=75,Candidat_serieux=False,reference_notes_SSI=ref,cohorte_T0_SHA256=m.sha(co))
  def save():
   j['fichiers']={q.name:m.sha(q) for q in p.glob('*.csv')};(p/'MANIFESTE.json').write_text(json.dumps(j))
  save();assert m.valider_analyse(p/'MANIFESTE.json',ssi,p)['MCPA']==72
  for bad in [ssi.copy().set_axis(ssi.index)]:
   bad['Statut_SSI']='A_COMPLETER_PREUVES_SSI'
   try:m.valider_analyse(p/'MANIFESTE.json',bad,p)
   except RuntimeError:pass
   else:raise AssertionError('SSI absent accepté')
  for key,value in [('Date_analyse_UTC','2099-01-01T00:00:00+00:00'),('MCPA',80),('Candidat_serieux',True)]:
   old=j[key];j[key]=value;save()
   try:m.valider_analyse(p/'MANIFESTE.json',ssi,p)
   except RuntimeError:pass
   else:raise AssertionError('Analyse divergente acceptée '+key)
   j[key]=old
  scenarios.loc[0,'Rendement_apres_achat_vente_2_5_pct']=-10;scenarios.to_csv(p/'SCENARIOS_3_6_MOIS.csv',index=False);save()
  try:m.valider_analyse(p/'MANIFESTE.json',ssi,p)
  except RuntimeError as e:assert 'FRAIS' in str(e)
  else:raise AssertionError('Frais omis acceptés')
 print('Raccordement MCPA : admission, preuves SSI, dates, somme, seuil et frais contrôlés')
if __name__=='__main__':test()

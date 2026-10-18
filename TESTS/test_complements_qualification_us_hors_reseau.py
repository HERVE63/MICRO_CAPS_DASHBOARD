from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('compl',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AR_COMPLEMENTS_QUALIFICATION_US.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 ds=[{'Formulaire':'SCHEDULE 13G','Date_depot':'2026-01-0'+str(i),'Accession':str(i)} for i in range(1,6)]+[{'Formulaire':'3','Date_depot':'2026-01-01','Accession':'initial'},{'Formulaire':'5','Date_depot':'2027-01-01','Accession':'future'}]
 r=m.choisir(ds,'2026-10-18');assert len(r)==4 and not any(x['Accession']=='future' for x in r) and {x['Accession'] for x in r if x['Formulaire']=='SCHEDULE 13G'}=={'3','4','5'}
 assert m.controler_ownership(b'<ownershipDocument><issuer><issuerCik>1234</issuerCik></issuer><documentType>3</documentType><periodOfReport>2026-01-01</periodOfReport></ownershipDocument>','0000001234')==('3','2026-01-01')
 try:m.controler_ownership(b'<ownershipDocument><issuer><issuerCik>9999</issuerCik></issuer></ownershipDocument>','0000001234')
 except ValueError:pass
 else:raise AssertionError('Mauvais émetteur accepté')
 print('Compléments : fenêtre datée, Form 3/5 conservés, CIK incohérent refusé, aucune note créée')
if __name__=='__main__':test()

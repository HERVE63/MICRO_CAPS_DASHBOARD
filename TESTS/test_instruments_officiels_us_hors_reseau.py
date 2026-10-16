"""Cas empêchant de confondre action, titre de dette, préférence et ADR."""
from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('instruments',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AK_CONTROLER_INSTRUMENTS_US_OFFICIELS.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 def r(nom):return {'Security Name':nom,'Test Issue':'N','ETF':'N','Symbol':'P'}
 assert m.classer(r('Preferred Bank - Common Stock'))=='ACTION_ORDINAIRE_LIBELLE_OFFICIEL'
 assert m.classer(r('Apogee - Class A Ordinary Shares'))=='ACTION_ORDINAIRE_LIBELLE_OFFICIEL'
 assert m.classer(r('Fixture - 5.5% Senior Notes due 2066'))=='AUTRE_INSTRUMENT_NON_ORDINAIRE'
 assert m.classer(r('Fixture - Warrants representing ordinary shares'))=='AUTRE_INSTRUMENT_NON_ORDINAIRE'
 assert m.classer(r('Fixture - Units, each consisting of one ordinary share'))=='UNITES_A_VERIFIER'
 assert m.classer(r('Fixture - American Depositary Shares representing common shares'))=='REPRESENTATION_DEPOSITAIRE_A_VERIFIER'
 assert m.classer(r('Fixture - Depositary Shares representing Preferred Stock'))=='PREFERENTIELLE_NON_ORDINAIRE'
 assert m.classer(dict(r('Common Stock'),ETF='Y'))=='ETF_ETP_NON_ADMISSIBLE'
 assert m.classer(dict(r('Common Stock'),**{'Test Issue':'Y'}))=='INSTRUMENT_TEST_NON_ADMISSIBLE'
 rows,stamp=m.lire_repertoire(b'Symbol|Security Name|Test Issue|ETF\nP|Fixture - Common Stock|N|N\nFile Creation Time: 1015202608:31|||\n')
 assert len(rows)==1 and stamp=='1015202608:31'
 result=m.rapprocher([{'Ticker_US':'P.US'},{'Ticker_US':'OTCINCONNU.US'}],[('fixture_officielle',rows)])
 assert result[0]['Statut_instrument']=='ACTION_ORDINAIRE_LIBELLE_OFFICIEL'
 assert result[1]['Statut_instrument'].startswith('ABSENT_REPERTOIRES')
 assert len(result)==2 and all(x['Admission_SSI']=='NON' for x in result)
 print('Instruments officiels : actions finissant par P, dette, préférences, ADR, unités et absences sans rejet financier contrôlés')
if __name__=='__main__':test()

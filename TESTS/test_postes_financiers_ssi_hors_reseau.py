"""Ne pas confondre passif et dette ni inventer un FCF ou mélanger les périodes."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
s=importlib.util.spec_from_file_location('postes_us',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AI_RACCORDER_COMPTES_US_SSI.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 base={'form':'10-K','filed':'2026-03-01','end':'2025-12-31','accn':'0000000001-26-000001'}
 flux=dict(base,start='2025-01-01')
 facts={'DebtCurrent':{'units':{'USD':[dict(base,val=10)]}},
        'LongTermDebtCurrent':{'units':{'USD':[dict(base,val=6)]}},
        'LongTermDebtNoncurrent':{'units':{'USD':[dict(base,val=30)]}},
        'GrossProfit':{'units':{'USD':[dict(flux,val=50)]}},
        'PaymentsToAcquirePropertyPlantAndEquipment':{'units':{'USD':[dict(flux,val=12),dict(base,val=999)]}},
        'ShareBasedCompensation':{'units':{'USD':[dict(flux,val=3)]}}}
 with TemporaryDirectory() as tmp:
  tables=m.raccorder_emetteur([{'Ticker_US':'FIXTURE.US','CIK':'0000000001','Nom_SEC':'Fixture'}],
      {'cik':1,'facts':{'us-gaap':facts}},'https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json',
      '2026-10-15T00:00:00Z','2026-10-15',Path(tmp))
  q=tables['COMPARABLES'];w=tables['RAPPROCHEMENT']
  assert len(q)==6 and '999' not in set(q.Valeur)
  assert set(q.Concept)=={'DebtCurrent','LongTermDebtCurrent','LongTermDebtNoncurrent','GrossProfit','CapitalExpenditure','ShareBasedCompensation'}
  assert set(w[w.Concept.str.contains('Debt')].Bloc_SSI_cible)=={'B1'}
  assert set(w[w.Concept.eq('ShareBasedCompensation')].Bloc_SSI_cible)=={'B5'}
  assert set(w.Note_SSI_attribuee)=={'NON'}
  assert 'FCF' not in set(q.Concept) and 'TotalDebt' not in set(q.Concept)
 print('Postes SSI : composantes de dette distinctes, flux avec durée, pas de total ni FCF inventé, aucun score')
if __name__=='__main__':test()

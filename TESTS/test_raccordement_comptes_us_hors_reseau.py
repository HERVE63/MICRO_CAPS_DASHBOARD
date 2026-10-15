"""Le nouveau recensement utilise réellement 07U/V/W sans écrire dans DONNEES."""
import importlib.util, json, hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

s=importlib.util.spec_from_file_location('raccord_us',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AI_RACCORDER_COMPTES_US_SSI.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def test():
    row={'Ticker_US':'FIXTURE.US','CIK':'0000000001','Nom_SEC':'Fixture de test'}
    annuel={'form':'10-K','start':'2024-01-01','end':'2024-12-31','filed':'2025-03-01',
             'val':123,'accn':'0000000001-25-000001','fy':2024,'fp':'FY'}
    futur=dict(annuel,filed='2026-11-01',val=999)
    obj={'cik':1,'facts':{'us-gaap':{
        'Revenues':{'units':{'USD':[annuel,futur]}},
        'Assets':{'units':{'USD':[{'form':'10-K','end':'2024-12-31','filed':'2025-03-01','val':456}]}}
    }}}
    url='https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json'
    with TemporaryDirectory() as tmp:
        p=Path(tmp)
        tables=m.raccorder_emetteur([row],obj,url,'2026-10-15T00:00:00Z','2026-10-15',p)
        assert len(tables['BRUTS'])==2 and len(tables['COMPARABLES'])==2
        assert set(tables['RAPPROCHEMENT']['Bloc_SSI_cible'])=={'B1','B3'}
        assert set(tables['RAPPROCHEMENT']['Note_SSI_attribuee'])=={'NON'}
        assert set(tables['RAPPROCHEMENT']['Statut_preuve'])=={'A_VERIFIER_IDENTITE_ET_DOCUMENT'}
        assert set(tables['BRUTS']['Date_collecte_UTC'])=={'2026-10-15T00:00:00Z'}
        assert '999' not in set(tables['BRUTS']['Valeur'])
        archive=p/'fixture.enc.json';archive.write_text('{"fixture":1}')
        manifeste={'fichiers':{archive.name:hashlib.sha256(archive.read_bytes()).hexdigest()}}
        entree={'route':'SEC:'+url,'archive_chiffree':archive.name}
        dec=lambda o,k:json.dumps(obj).encode()
        assert m.lire_archive_sec(p,manifeste,entree,'fixture',dec)['cik']==1
        archive.write_text('{"fixture":2}')
        try:m.lire_archive_sec(p,manifeste,entree,'fixture',dec)
        except RuntimeError as e:assert 'EMPREINTE' in str(e)
        else:raise AssertionError('Archive modifiée acceptée')
        try:m.verifier_fichier(p,manifeste,'../fixture.enc.json')
        except RuntimeError as e:assert 'CHEMIN' in str(e)
        else:raise AssertionError('Sortie de dossier acceptée')
        try:m.lire_archive_sec(p,manifeste,dict(entree,route='fundamentals/FIXTURE.US'),'fixture',dec)
        except RuntimeError as e:assert 'NON_COMPANYFACTS' in str(e)
        else:raise AssertionError('Données fournisseur publiées comme SEC')
    print('Raccordement réel 07U/07V/07W : périodes, provenance, archives, absence de notes et chemins isolés contrôlés')

if __name__=='__main__':test()

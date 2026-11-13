#!/usr/bin/env python3
"""Regression test for SEC bridge: two proof files, duplicate, unverified identity."""
import csv
import tempfile
from pathlib import Path
from bridge_sec_identites_confirmees import run

def write(path, headers, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)

def test():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        a, b, facts, out = [p / n for n in ('proof1.csv', 'proof2.csv', 'facts.csv', 'out.csv')]
        cols = ['Ticker', 'CIK', 'Statut_identite']
        write(a, cols, [dict(Ticker='IDN', CIK='0001040896', Statut_identite='CIK_CONFIRME_SEC')])
        write(b, cols, [dict(Ticker='INFU', CIK='0001337013', Statut_identite='CIK_CONFIRME_SEC_ISIN_NON_VERIFIE')])
        base = dict(ID_position='2', Ticker='INFU', CIK_piste='0001337013',
                    Concept='Assets', Unite='USD', Valeur='100', Date_debut='',
                    Date_fin='2026-06-30', Date_depot='2026-08-04',
                    Formulaire='10-Q', Accession='0001628280-26-052462',
                    Source_URL='https://data.sec.gov/api/xbrl/companyfacts/CIK0001337013.json')
        idn = dict(base, ID_position='1', Ticker='IDN', CIK_piste='0001040896')
        bad = dict(base, Ticker='BAD', CIK_piste='0000000001')
        write(facts, list(base), [idn, base, base, bad])
        run(facts, [a, b], out)
        with out.open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2, f'Expected 2 unique rows, got {len(rows)}'
        assert {r['Ticker'] for r in rows} == {'IDN', 'INFU'}
        assert all(r['Statut_preuve'] == 'IDENTITE_CIK_CONFIRMEE_FAIT_NON_AUDITE' for r in rows)
        print('PASS: 2 accepted, duplicate and unverified identity rejected')

if __name__ == '__main__':
    test()

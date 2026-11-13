#!/usr/bin/env python3
"""Raccordement conservateur des faits SEC aux identités vérifiées, sans notation."""
import argparse
import csv
from pathlib import Path

FIELDS = ['ID_position','Ticker','CIK','Concept','Unite','Valeur','Date_debut','Date_fin','Date_depot','Formulaire','Accession','Source_URL','Statut_preuve']

def run(facts, identities, output):
    proofs = {}
    for identity_path in identities:
        with open(identity_path, newline='', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                if row['Statut_identite'].startswith('CIK_CONFIRME'):
                    key = (row['Ticker'],row['CIK'].zfill(10))
                    proofs[key] = row
    # The complement has no ID_position; CIK and ticker are matched together.
    # Keep original source rows and never promote financial facts to audited.
    seen = set()
    rows = []
    with open(facts, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            key = (row['Ticker'],row['CIK_piste'].zfill(10))
            if key not in proofs:
                continue
            if not row['Source_URL'].startswith('https://data.sec.gov/') or not row['Date_depot'] or not row['Accession']:
                continue
            fingerprint = tuple(row.get(k,'') for k in ['ID_position','Ticker','Concept','Unite','Valeur','Date_debut','Date_fin','Date_depot','Accession'])
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            rows.append(dict(zip(FIELDS,[row['ID_position'],row['Ticker'],key[1],row['Concept'],row['Unite'],row['Valeur'],row['Date_debut'],row['Date_fin'],row['Date_depot'],row['Formulaire'],row['Accession'],row['Source_URL'],'IDENTITE_CIK_CONFIRMEE_FAIT_NON_AUDITE'])))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'faits_raccordes={len(rows)} titulaires={len(set(r["Ticker"] for r in rows))} sortie={output}')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--facts',default='DONNEES/FAITS_SEC_TITULAIRES_US.csv')
    parser.add_argument('--identities', nargs='+', default=['DONNEES/PREUVES_IDENTITE_SEC_20261112.csv', 'DONNEES/PREUVES_IDENTITE_SEC_20261113_COMPLEMENT.csv'])
    parser.add_argument('--output',default='DONNEES/FAITS_SEC_RAPPROCHES_NON_CERTIFIES.csv')
    args=parser.parse_args()
    run(args.facts,args.identities,args.output)

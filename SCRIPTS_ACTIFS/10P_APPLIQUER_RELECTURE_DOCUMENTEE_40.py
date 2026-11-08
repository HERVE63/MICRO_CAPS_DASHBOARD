#!/usr/bin/env python3
"""Apply reviewed evidence without erasing earlier observations or certifying scores.

No network, no orders, no modification of frozen references. An unchanged evidence
record is a no-op. Each replacement retains its previous complete cell.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply(root, records):
    paths = sorted((root / 'DOSSIERS_MCPA_IPS_40').glob('*.json'))
    docs = {json.loads(p.read_text())['ticker']: (p, json.loads(p.read_text())) for p in paths}
    if len(docs) != 40:
        raise ValueError('La cohorte doit contenir exactement 40 fiches uniques')
    changes = []
    for record in records:
        path, doc = docs[record['ticker']]
        block, key = record['champ'].split('.', 1)
        old = doc['blocs'][block][key]
        evidence_id = record['id']
        required = ('valeur', 'unite', 'periode', 'date_source', 'source_url', 'statut', 'commentaire')
        cell = {k: record[k] for k in required}
        cell.update(date_collecte='2026-11-09', preuve_relecture_id=evidence_id)
        if old == cell:
            continue
        if old.get('valeur') is not None and old.get('preuve_relecture_id') != evidence_id and not record.get('remplacer', False):
            continue
        doc.setdefault('historique_relectures', []).append({
            'preuve_id': evidence_id, 'champ': record['champ'], 'ancienne_cellule': old,
            'motif': record['commentaire'], 'date_relecture': '2026-11-09',
        })
        doc['blocs'][block][key] = cell
        doc['arbitrage_autorise'] = False
        changes.append({'ticker': record['ticker'], 'champ': record['champ'], 'preuve_id': evidence_id})
    for path, doc in docs.values():
        if any(c['ticker'] == doc['ticker'] for c in changes):
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('records', type=Path)
    args = parser.parse_args()
    changes = apply(ROOT, json.loads(args.records.read_text()))
    print(json.dumps({'champs_modifies': len(changes), 'fiches_modifiees': len({c['ticker'] for c in changes}), 'arbitrages': 0}))

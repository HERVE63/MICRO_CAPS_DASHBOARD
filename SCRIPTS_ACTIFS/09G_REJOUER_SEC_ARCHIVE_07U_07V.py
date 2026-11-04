#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay hors réseau des captures 09F par les modules historiques 07U et 07V.

Deux horizons : T0 2026-10-01 et date de collecte. Chaque fait reste une piste
non certifiée. Ne touche jamais à DONNEES, aux historiques ni à 07R.
"""
import csv
import hashlib
import importlib.util
import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'SCRIPTS_ACTIFS'
T0 = '2026-10-01'


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def module_historique(nom, scripts):
    spec = importlib.util.spec_from_file_location(nom.replace('.py', ''), scripts / nom)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def charger_archive(dossier):
    manifeste = json.loads((dossier / 'MANIFESTE.json').read_text(encoding='utf-8'))
    if manifeste.get('Statut') != 'PILOTE_DIAGNOSTIQUE_NON_CERTIFIANT':
        raise ValueError('STATUT_PILOTE_INATTENDU')
    date_collecte = datetime.fromisoformat(manifeste['Date_collecte_UTC']).date().isoformat()
    if date_collecte < T0:
        raise ValueError('ARCHIVE_ANTERIEURE_T0')
    for relatif, attendu in manifeste['Fichiers_SHA256'].items():
        cible = (dossier / relatif).resolve()
        if not cible.is_relative_to(dossier.resolve()) or not cible.is_file() or sha256(cible) != attendu:
            raise ValueError('SHA256_ARCHIVE_INVALIDE: ' + relatif)
    sources = {}
    for source in manifeste['Sources']:
        url = source['URL']
        if not url.startswith('https://data.sec.gov/api/xbrl/companyfacts/CIK'):
            continue
        cible = (dossier / source['Fichier_brut']).resolve()
        if not cible.is_relative_to(dossier.resolve()) or not cible.is_file():
            raise ValueError('SOURCE_HORS_ARCHIVE')
        if sha256(cible) != source['SHA256']:
            raise ValueError('SOURCE_SHA256_INVALIDE')
        if url in sources and sources[url]['SHA256'] != source['SHA256']:
            raise ValueError('SOURCES_SEC_CONTRADICTOIRES')
        sources[url] = dict(source, _chemin=cible)
    with (dossier / 'DIAGNOSTIC_SEC_US_5.csv').open(encoding='utf-8', newline='') as f:
        lignes = list(csv.DictReader(f))
    if len(lignes) != 5 or len({r['Ticker'] for r in lignes}) != 5:
        raise ValueError('DIAGNOSTIC_COHORTE_INVALIDE')
    return manifeste, date_collecte, lignes, sources


def executer(dossier, scripts=SCRIPTS):
    dossier = Path(dossier).resolve()
    scripts = Path(scripts).resolve()
    manifeste, date_collecte, lignes, sources = charger_archive(dossier)
    sortie = dossier / 'NORMALISATION_07U_07V'
    if sortie.exists():
        raise FileExistsError('REPLAY_DEJA_PRESENT_NE_PAS_ECRASER')
    sortie.mkdir()
    liens = {}
    statuts = {}
    for r in lignes:
        ticker, cik = r['Ticker'], r['CIK']
        url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + cik + '.json'
        ok = r['Statut'] == 'XBRL_BRUT_A_VERIFIER' and cik.isdigit() and len(cik) == 10 and url in sources
        if ok:
            obj = json.loads(sources[url]['_chemin'].read_bytes())
            ok = str(obj.get('cik', '')).zfill(10) == cik
        if ok:
            liens[(ticker, cik)] = (url, sources[url])
            statuts[ticker] = 'PISTE_SEC_SHA256_OK_IDENTITE_NON_CERTIFIEE'
        else:
            statuts[ticker] = 'EN_ATTENTE_DATA_IDENTITE_OU_SOURCE'
    # Même jeu de sources, deux dates de connaissance : jamais de look-ahead T0.
    for label, limite in [('T0', T0), ('COURANT', date_collecte)]:
        travail = sortie / label
        travail.mkdir()
        with (travail / 'PREUVES_SEC_EDGAR_SSI.csv').open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['Ticker', 'CIK', 'Statut_SEC'])
            w.writeheader()
            for r in lignes:
                w.writerow({'Ticker': r['Ticker'], 'CIK': r['CIK'],
                            'Statut_SEC': ('A_VERIFIER_IDENTITE_ET_CONTENU'
                                           if (r['Ticker'], r['CIK']) in liens else 'EN_ATTENTE_DATA')})
        u = module_historique('07U_COLLECTE_COMPANYFACTS_SEC.py', scripts)
        u.SRC = travail / 'PREUVES_SEC_EDGAR_SSI.csv'
        u.OUT = travail / 'FAITS_FINANCIERS_SEC_SSI.csv'
        u.AUD = travail / 'AUDIT_FAITS_FINANCIERS_SEC_SSI.csv'
        u.DATES_SOURCES = {url: s['Date_collecte_UTC'] for url, s in liens.values()}
        def local(url, agent):
            if url not in sources:
                raise ValueError('RESEAU_INTERDIT_SOURCE_ABSENTE')
            return json.loads(sources[url]['_chemin'].read_bytes())
        u.lire_json = local
        # Contact fictif strictement local ; aucune requête réseau n'est possible.
        with patch.dict(os.environ, {'MICRO_CAPS_AS_OF': limite,
                                     'SEC_USER_AGENT': 'Replay hors reseau@local.invalid'}):
            u.executer()
            v = module_historique('07V_NORMALISER_FAITS_SEC.py', scripts)
            v.SRC = u.OUT
            v.OUT = travail / 'FAITS_SEC_COMPARABLES_SSI.csv'
            v.AUD = travail / 'AUDIT_COMPARABILITE_SEC_SSI.csv'
            v.executer()
        # Rattacher SHA256 à chaque observation sans promouvoir les preuves.
        for p in [u.OUT, v.OUT]:
            with p.open(encoding='utf-8', newline='') as f:
                lecteur = csv.DictReader(f)
                colonnes = list(lecteur.fieldnames or [])
                faits = list(lecteur)
            if 'SHA256_brut_SEC' not in colonnes:
                colonnes.append('SHA256_brut_SEC')
            for fait in faits:
                cle = (fait['Ticker'], fait['CIK'])
                if cle not in liens:
                    raise ValueError('FAIT_SANS_PROVENANCE_CERTIFIABLE')
                fait['SHA256_brut_SEC'] = liens[cle][1]['SHA256']
                if fait['Date_depot'] > limite:
                    raise ValueError('FUITE_TEMPORELLE_' + label)
                if fait['Statut_preuve'] != 'A_VERIFIER_IDENTITE_ET_PERIODE':
                    raise ValueError('PROMOTION_INATTENDUE_PREUVE')
            with p.open('w', encoding='utf-8', newline='') as f:
                w = csv.DictWriter(f, fieldnames=colonnes)
                w.writeheader()
                w.writerows(faits)
    bilan = {'Statut': 'REPLAY_SEC_NON_CERTIFIANT', 'T0': T0,
             'Date_collecte': date_collecte, 'Statuts': statuts,
             'Notes_SSI': 0, 'Notes_MCPA': 0, 'Arbitrages': 0,
             'Sources_reutilisees': {t: {'URL': url, 'SHA256': s['SHA256']}
                                    for (t, _), (url, s) in liens.items()},
             'Fichiers_SHA256': {str(p.relative_to(sortie)): sha256(p)
                                for p in sorted(sortie.rglob('*')) if p.is_file()}}
    (sortie / 'MANIFESTE_REPLAY.json').write_text(
        json.dumps(bilan, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print('09G replay hors réseau 07U/07V:', len(liens), 'sources, deux horizons, zéro score')
    return bilan


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        raise SystemExit('Usage: 09G_REJOUER_SEC_ARCHIVE_07U_07V.py DOSSIER_09F')
    executer(sys.argv[1])

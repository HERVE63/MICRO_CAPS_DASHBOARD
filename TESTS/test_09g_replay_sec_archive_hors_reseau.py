"""09G : replay SEC historique 07U/07V, PIT T0 et SHA256 sans reseau."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('replay_09g', ROOT / 'SCRIPTS_ACTIFS/09G_REJOUER_SEC_ARCHIVE_07U_07V.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture(base):
    d = Path(base) / 'AUDITS/SEC_PILOTE_US_5/20261102T080000000000Z'
    (d / 'BRUTS').mkdir(parents=True)
    captures = []
    for ticker, cik in [('IDN', '0000001001'), ('OSS', '0000001003')]:
        facts = {'cik': int(cik), 'facts': {'us-gaap': {
            'RevenueFromContractWithCustomerExcludingAssessedTax': {'units': {'USD': [
                {'val': 100, 'start': '2025-01-01', 'end': '2025-12-31', 'filed': '2026-02-20', 'form': '10-K', 'accn': 'a'},
                {'val': 40, 'start': '2026-04-01', 'end': '2026-06-30', 'filed': '2026-08-10', 'form': '10-Q', 'accn': 'b'},
                {'val': 50, 'start': '2026-07-01', 'end': '2026-09-30', 'filed': '2026-10-28', 'form': '10-Q', 'accn': 'c'},
            ]}},
            'Assets': {'units': {'USD': [
                {'val': 120, 'end': '2026-06-30', 'filed': '2026-08-10', 'form': '10-Q', 'accn': 'b'}]}}
        }}}
        raw = json.dumps(facts, sort_keys=True).encode()
        digest = hashlib.sha256(raw).hexdigest()
        (d / 'BRUTS' / (digest + '.json')).write_bytes(raw)
        captures.append({'URL': 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + cik + '.json',
                         'Fichier_brut': 'BRUTS/' + digest + '.json', 'SHA256': digest,
                         'Date_collecte_UTC': '2026-11-02T08:00:00+00:00'})
    with (d / 'DIAGNOSTIC_SEC_US_5.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['Ticker', 'CIK', 'Statut'])
        w.writeheader()
        for ticker, cik in [('IDN', '0000001001'), ('INFU', ''), ('OSS', '0000001003'),
                            ('CXDO', ''), ('LWAY', '')]:
            w.writerow({'Ticker': ticker, 'CIK': cik,
                        'Statut': 'XBRL_BRUT_A_VERIFIER' if cik else 'EN_ATTENTE_DATA'})
    files = {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in d.rglob('*') if p.is_file()}
    (d / 'MANIFESTE.json').write_text(json.dumps({
        'Statut': 'PILOTE_DIAGNOSTIQUE_NON_CERTIFIANT',
        'Date_collecte_UTC': '2026-11-02T08:00:00+00:00',
        'Sources': captures, 'Fichiers_SHA256': files,
    }))
    return d


def lire(p):
    with p.open(newline='') as f:
        return list(csv.DictReader(f))


def test_replay_deux_horizons():
    with TemporaryDirectory() as tmp:
        d = fixture(tmp)
        bilan = mod.executer(d)
        assert bilan['Statut'] == 'REPLAY_SEC_NON_CERTIFIANT'
        assert len(bilan['Sources_reutilisees']) == 2
        assert bilan['Notes_SSI'] == bilan['Notes_MCPA'] == bilan['Arbitrages'] == 0
        t0 = lire(d / 'NORMALISATION_07U_07V/T0/FAITS_SEC_COMPARABLES_SSI.csv')
        courant = lire(d / 'NORMALISATION_07U_07V/COURANT/FAITS_SEC_COMPARABLES_SSI.csv')
        assert len(t0) > 0 and len(courant) > len(t0)
        assert all(r['Date_depot'] <= '2026-10-01' for r in t0)
        assert any(r['Date_depot'] == '2026-10-28' for r in courant)
        assert all(r['Statut_preuve'] == 'A_VERIFIER_IDENTITE_ET_PERIODE' for r in courant)
        assert all(len(r['SHA256_brut_SEC']) == 64 for r in courant)
        for relatif, sha in bilan['Fichiers_SHA256'].items():
            p = d / 'NORMALISATION_07U_07V' / relatif
            assert hashlib.sha256(p.read_bytes()).hexdigest() == sha
        assert not (Path(tmp) / 'DONNEES').exists()


def test_archive_corrompue_refusee():
    with TemporaryDirectory() as tmp:
        d = fixture(tmp)
        raw = next((d / 'BRUTS').glob('*.json'))
        raw.write_bytes(raw.read_bytes() + b'\n')
        try:
            mod.executer(d)
        except ValueError as e:
            assert 'SHA256' in str(e)
        else:
            raise AssertionError('Une source primaire corrompue doit etre refusee')
        assert not (d / 'NORMALISATION_07U_07V').exists()


if __name__ == '__main__':
    test_replay_deux_horizons()
    test_archive_corrompue_refusee()
    print('TEST 09G OK : SHA256, T0 PIT, deux horizons, pas de score, aucun reseau')

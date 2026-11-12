"""Synthetic provider failures and intraday bars, never production trades."""
import csv
import importlib.util
from datetime import datetime, timezone, timedelta
from pathlib import Path


def prepare(tmp_path, monkeypatch):
    path = Path(__file__).parents[1] / 'SCRIPTS_ACTIFS/09N_COLLECTE_HISTORIQUES_YAHOO_40.py'
    spec = importlib.util.spec_from_file_location('history_cache_test', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    d = tmp_path / 'DONNEES'
    d.mkdir()
    with (d / 'ETAT_INITIAL_PORTEFEUILLE_GERE.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=['ID_position', 'Ticker'])
        w.writeheader()
        w.writerows({'ID_position': i, 'Ticker': f'TEST{i}'} for i in range(1, 41))
    monkeypatch.setattr(m, 'D', d)
    monkeypatch.setattr(m.time, 'sleep', lambda _: None)
    return m, d


def test_failure_preserves_complete_cache_and_exposes_failure(tmp_path, monkeypatch):
    m, d = prepare(tmp_path, monkeypatch)
    today = datetime.now(timezone.utc).date()
    monkeypatch.setattr(m, 'fetch', lambda symbol: ({'timestamp': [int(datetime.combine(today-timedelta(days=i), datetime.min.time(), timezone.utc).timestamp()) for i in (2,1)], 'indicators': {'quote': [{'close': [10,11], 'volume': [100,200]}], 'adjclose': [{'adjclose': [9,10]}]}}, 'https://example.invalid/synthetic'))
    m.main()
    before = (d/'HISTORIQUES_YAHOO_40.csv').read_bytes()
    def fail(symbol):
        raise TimeoutError('SYNTHETIC_FAILURE')
    monkeypatch.setattr(m, 'fetch', fail)
    m.main()
    assert (d/'HISTORIQUES_YAHOO_40.csv').read_bytes() == before
    rows = list(csv.DictReader((d/'COUVERTURE_HISTORIQUES_YAHOO_40.csv').open()))
    assert len(rows) == 40
    assert all(r['Statut'] == 'CACHE_PRESERVE_APRES_FAILED_TimeoutError' and r['Collecte_fraiche'] == 'NON' for r in rows)


def test_intraday_close_is_excluded(tmp_path, monkeypatch):
    m, d = prepare(tmp_path, monkeypatch)
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(m, 'fetch', lambda symbol: ({'meta': {'symbol': symbol, 'exchangeTimezoneName': 'UTC', 'currentTradingPeriod': {'regular': {'end': int(now.timestamp())+3600}}}, 'timestamp': [int((now-timedelta(days=1)).timestamp()),int(now.timestamp())], 'indicators': {'quote': [{'close': [10,999], 'volume': [100,200]}], 'adjclose': [{'adjclose': [10,999]}]}}, 'https://example.invalid/synthetic'))
    m.main()
    rows = list(csv.DictReader((d/'HISTORIQUES_YAHOO_40.csv').open()))
    assert len(rows) == 40 and all(float(r['Close']) == 10 for r in rows)


def test_wrong_symbol_is_rejected(tmp_path, monkeypatch):
    m, d = prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(m,'fetch',lambda symbol: ({'meta': {'symbol': 'WRONG'}},'https://example.invalid/synthetic'))
    m.main()
    rows = list(csv.DictReader((d/'HISTORIQUES_YAHOO_40.csv').open()))
    assert not rows

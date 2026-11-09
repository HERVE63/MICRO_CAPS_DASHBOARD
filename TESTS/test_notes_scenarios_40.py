"""Financial calculation invariants, independent of admission or order execution."""
import importlib.util
import math
import unittest
from datetime import date, timedelta
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('notes40', Path(__file__).resolve().parents[1] / 'SCRIPTS_ACTIFS/10Q_PREPARER_NOTES_SCENARIOS_40.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

def bars(start=date(2025, 10, 1)):
    out=[]
    while start <= date(2026, 11, 6):
        if start.weekday() < 5:
            out.append(dict(Date_UTC=start.isoformat(), Close='100', AdjClose='100', Volume='1000', Source='fixture'))
        start += timedelta(days=1)
    return out

class CalculationTests(unittest.TestCase):
    def test_anchors_do_not_look_forward(self):
        result=M.calculate(bars())
        self.assertEqual(result['ancrages']['6']['date'], '2026-05-06')
        self.assertEqual(result['ancrages']['12']['date'], '2025-11-06')
        self.assertEqual(result['M'], 0)
        self.assertEqual(result['points_non_observables'], 0)

    def test_drawdown_is_peak_to_trough_even_after_recovery(self):
        rows=bars()
        rows[-3]['AdjClose']='50'
        self.assertEqual(M.calculate(rows)['indicateurs']['drawdown_12m_pct'], -50)

    def test_conflicting_duplicate_rejected(self):
        rows=bars()
        rows.append(dict(rows[-1], AdjClose='99'))
        with self.assertRaisesRegex(ValueError, 'contradictoires'):
            M.calculate(rows)

    def test_short_listing_is_unknown_not_bearish_evidence(self):
        result=M.calculate(bars(date(2026, 9, 1)))
        self.assertIsNone(result['indicateurs']['momentum_12m_pct'])
        self.assertGreater(result['points_non_observables'], 0)
        self.assertIsNone(result['indicateurs']['drawdown_12m_pct'])

    def test_nonfinite_quote_and_missing_close_rejected(self):
        rows=bars()
        rows[-1]['AdjClose']='nan'
        with self.assertRaises(ValueError): M.calculate(rows)
        with self.assertRaises(ValueError): M.calculate(bars()[:-1])

if __name__=='__main__': unittest.main()

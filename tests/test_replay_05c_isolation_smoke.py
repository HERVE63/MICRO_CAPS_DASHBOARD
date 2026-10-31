from pathlib import Path
import pandas as pd

def test_initial_portfolio_40_positions():
    root = Path(__file__).resolve().parents[1]
    df = pd.read_csv(root / 'DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv')
    assert len(df) == 40
    assert df['ID_position'].nunique() == 40
    assert abs(df['Capital_initial_EUR'].sum() - 4000) < 0.01

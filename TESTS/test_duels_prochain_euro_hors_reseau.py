"""Réception existante du duel du prochain euro."""
from pathlib import Path
import runpy
if __name__=='__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/TEST_RECEPTION_09B.py'),run_name='__main__')

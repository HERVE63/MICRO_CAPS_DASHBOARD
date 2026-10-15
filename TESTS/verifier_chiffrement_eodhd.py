"""Contrôle dédié au workflow EODHD, qui installe cryptography."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('eodhd_crypto',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AH_RECENSER_MICROCAPS_US_EODHD.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
raw=b'FIXTURE_EODHD_DONNEE_PRIVEE';key='CLE_DE_TEST_NON_REELLE'
p=m.paquet_chiffre(raw,key)
assert raw.decode() not in json.dumps(p) and key not in json.dumps(p)
assert m.dechiffrer(p,key)==raw
try:m.dechiffrer(p,'MAUVAISE_CLE')
except Exception:pass
else:raise AssertionError('Archive déchiffrée avec mauvaise clé')
print('Chiffrement EODHD : aller-retour et refus de mauvaise clé OK')

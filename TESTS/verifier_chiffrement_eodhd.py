"""Contrôle dédié au workflow EODHD, qui installe cryptography."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('eodhd_crypto',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AH_RECENSER_MICROCAPS_US_EODHD.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
raw=b'FIXTURE_EODHD_DONNEE_PRIVEE';key='CLE_DE_TEST_NON_REELLE'
p=m.paquet_chiffre(raw,key)
assert raw.decode() not in json.dumps(p) and key not in json.dumps(p)
assert m.dechiffrer(p,key)==raw
assert p['compression']=='gzip'
# Les réponses archivées avant l'ajout de la compression restent déchiffrables.
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
nonce=m.os.urandom(12);cle=m.hashlib.sha256(b'MICRO_CAPS_EODHD_V1\0'+key.encode()).digest()
legacy={'version':1,'nonce':m.base64.b64encode(nonce).decode(),'ciphertext':m.base64.b64encode(AESGCM(cle).encrypt(nonce,raw,b'MICRO_CAPS_EODHD_V1')).decode(),'SHA256_brut':m.hashlib.sha256(raw).hexdigest()}
assert m.dechiffrer(legacy,key)==raw
try:m.dechiffrer(p,'MAUVAISE_CLE')
except Exception:pass
else:raise AssertionError('Archive déchiffrée avec mauvaise clé')
print('Chiffrement EODHD : aller-retour et refus de mauvaise clé OK')

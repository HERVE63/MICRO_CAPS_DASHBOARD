"""Les métriques fournisseur ne sont lisibles qu'avec la clé de revue."""
from pathlib import Path
import importlib.util,base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,PublicFormat,NoEncryption
s=importlib.util.spec_from_file_location('prive',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AQ_PREPARER_REVUE_PRIVEE_US.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 key=X25519PrivateKey.generate();raw=key.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption());pub=base64.b64encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode();data={'EXEMPLE_TEST':'METRIQUE_PRIVEE_123456'};p=m.chiffrer(data,pub)
 assert 'METRIQUE_PRIVEE' not in str(p) and m.dechiffrer(p,raw)==data
 for mauvais in [dict(p,SHA256_brut='0'*64),dict(p,nonce=base64.b64encode(bytes(12)).decode())]:
  try:m.dechiffrer(mauvais,raw)
  except Exception:pass
  else:raise AssertionError('Paquet falsifié accepté')
 autre=X25519PrivateKey.generate().private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())
 try:m.dechiffrer(p,autre)
 except Exception:pass
 else:raise AssertionError('Mauvaise clé acceptée')
 print('Revue privée : chiffrement authentifié, altération et mauvaise clé refusées')
if __name__=='__main__':test()

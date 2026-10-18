"""Prépare une revue privée des archives EODHD existantes, sans requête ni note.
La clé de l'abonnement reste dans Actions. Seule une enveloppe chiffrée pour
la clé publique de la session de revue quitte ce contexte.
"""
from pathlib import Path
from datetime import datetime,timezone
import base64,gzip,hashlib,importlib.util,json,os
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey,X25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
BASE=Path(__file__).resolve().parents[1]
AAD=b'MICRO_CAPS_REVUE_PRIVEE_US_V1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def charger(n):
 s=importlib.util.spec_from_file_location(n[:-3],BASE/'SCRIPTS_ACTIFS'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def chiffrer(data,public):
 dest=X25519PublicKey.from_public_bytes(base64.b64decode(public,validate=True));ephem=X25519PrivateKey.generate()
 cle=HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=AAD).derive(ephem.exchange(dest));nonce=os.urandom(12)
 brut=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode();enc=AESGCM(cle).encrypt(nonce,gzip.compress(brut,mtime=0),AAD)
 return {'version':1,'algorithme':'X25519-HKDF-SHA256-AES256GCM','public_ephemere':base64.b64encode(ephem.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode(),'nonce':base64.b64encode(nonce).decode(),'ciphertext':base64.b64encode(enc).decode(),'SHA256_brut':hashlib.sha256(brut).hexdigest()}
def dechiffrer(paquet,privee):
 p=X25519PrivateKey.from_private_bytes(privee);public=X25519PublicKey.from_public_bytes(base64.b64decode(paquet['public_ephemere'],validate=True))
 cle=HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=AAD).derive(p.exchange(public));data=gzip.decompress(AESGCM(cle).decrypt(base64.b64decode(paquet['nonce']),base64.b64decode(paquet['ciphertext']),AAD))
 if hashlib.sha256(data).hexdigest()!=paquet['SHA256_brut']:raise ValueError('REVUE_PRIVEE_EMPREINTE_DIVERGENTE')
 return json.loads(data)
def dernier(dossier):
 files=sorted((BASE/'AUDITS'/dossier).glob('*/MANIFESTE.json'))
 if not files:raise RuntimeError('SOURCE_REVUE_ABSENTE:'+dossier)
 p=files[-1];return p,json.loads(p.read_text())
def executer():
 config=BASE/'CONFIG/CLE_PUBLIQUE_REVUE_PRIVEE_US.json';pub=json.loads(config.read_text())['cle_publique_X25519_base64']
 cle=os.getenv('EODHD_API_KEY','').strip()
 if not cle:raise RuntimeError('CLE_DECHIFFREMENT_ARCHIVES_ABSENTE')
 ah=charger('07AH_RECENSER_MICROCAPS_US_EODHD.py');ai=charger('07AI_RACCORDER_COMPTES_US_SSI.py')
 cp,cm=dernier('RECENSEMENT_US_EODHD');mp,mm=dernier('MARCHE_US_EODHD')
 if not cm.get('recensement_termine') or not mm.get('volumes_monetaires_corriges_splits'):raise RuntimeError('ARCHIVES_REVUE_INCOMPLETES')
 c=ai.verifier_fichier(cp.parent,cm,'DOSSIERS_EODHD_A_VERIFIER.enc.json');m=ai.verifier_fichier(mp.parent,mm,'METRIQUES_MARCHE_US.enc.json')
 catalogue=json.loads(ah.dechiffrer(json.loads(c.read_text()),cle));marche=json.loads(ah.dechiffrer(json.loads(m.read_text()),cle))
 if len({r['Ticker_US'] for r in catalogue})!=len(catalogue) or len({r['Ticker'] for r in marche})!=len(marche):raise RuntimeError('REVUE_IDENTITES_DUPLIQUEES')
 if not {r['Ticker'] for r in marche}<={r['Ticker_US'] for r in catalogue}:raise RuntimeError('REVUE_MARCHE_HORS_CATALOGUE')
 now=datetime.now(timezone.utc);out=BASE/'AUDITS/REVUE_PRIVEE_US'/now.strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
 sources={str(p.relative_to(BASE)):sha(p) for p in (cp,mp,c,m)}
 import pandas as pd
 lotpath=BASE/'AUDITS/RECHERCHE_COMPLEMENTS_US/2026-10-18_LOT_ORDRE_SCE/LOT_PRIORISATION.csv'
 lot=pd.read_csv(lotpath,dtype=str,keep_default_na=False);couverture_path=ai.verifier_fichier(mp.parent,mm,'COUVERTURE_MARCHE_US.csv')
 couverture=pd.read_csv(couverture_path,dtype=str,keep_default_na=False).set_index('Ticker');historiques={}
 for ticker in lot.Ticker:
  name=couverture.loc[ticker,'Archive_historique_chiffree']
  if name:
   archive=ai.verifier_fichier(mp.parent,mm,name);historiques[ticker]=json.loads(ah.dechiffrer(json.loads(archive.read_text()),cle));sources[str(archive.relative_to(BASE))]=sha(archive)
 sources[str(lotpath.relative_to(BASE))]=sha(lotpath)
 payload={'date_preparation_UTC':now.isoformat(),'date_reference_marche':mm['date_reference'],'sources_SHA256':sources,'catalogue':catalogue,'marche':marche,'historiques_lot':historiques,'limites':{'SSI':'AUCUNE_NOTE_GENEREE','force_relative':'HYBRIDE_ACTION_AJUSTEE_DIVIDENDES_VS_INDICE_PRIX','date_T0':'PAS_ARCHIVE_POINT_IN_TIME_T0'}}
 packet=out/'DOSSIER_REVUE.enc.json';packet.write_text(json.dumps(chiffrer(payload,pub))+'\n')
 bilan={'date_UTC':now.isoformat(),'source_script_SHA256':sha(Path(__file__)),'cle_publique_SHA256':sha(config),'cotations_catalogue':len(catalogue),'metriques_marche':len(marche),'historiques_lot':len(historiques),'date_reference_marche':mm['date_reference'],'sources':sources,'requetes_fournisseur':0,'notes_attribuees':0,'licence_diffusion':'DONNEES_ET_METRIQUES_FOURNISSEUR_CHIFFREES_AUCUN_COURS_DANS_LES_LOGS','fichiers':{packet.name:sha(packet)}}
 (out/'MANIFESTE.json').write_text(json.dumps(bilan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(bilan,ensure_ascii=False));return bilan
if __name__=='__main__':executer()

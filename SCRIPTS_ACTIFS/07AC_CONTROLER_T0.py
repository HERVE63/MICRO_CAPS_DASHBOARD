"""Verrou SHA256 des références T0 ; ne les modifie jamais."""
from pathlib import Path
import hashlib,json
BASE=Path(__file__).resolve().parents[1]
def executer():
    ref=json.loads((BASE/'CONFIG/EMPREINTES_T0.json').read_text())
    erreurs=[]
    for nom,digest in ref['fichiers'].items():
        p=BASE/nom
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:erreurs.append(nom)
    if erreurs:raise RuntimeError('T0 modifié/absent : '+', '.join(erreurs))
    print('Intégrité T0 SHA256 : OK');return ref
if __name__=='__main__':executer()

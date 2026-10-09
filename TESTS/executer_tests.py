"""Réception hors réseau : tous les tests, syntaxe et intégrité des entrées."""
from pathlib import Path
import ast, hashlib, json, os, subprocess, sys
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
def empreintes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('DONNEES', 'SAUVEGARDES') for p in (ROOT/folder).rglob('*') if p.is_file()}
def executer():
    avant = empreintes(); rows = []
    for p in sorted((ROOT/'SCRIPTS_ACTIFS').glob('*.py')):
        try:
            ast.parse(p.read_text(encoding='utf-8')); statut = 'OK'; detail = ''
        except SyntaxError as exc:
            statut = 'ECHEC'; detail = str(exc)
        rows.append({'controle': 'syntaxe/'+p.name, 'statut': statut, 'detail': detail})
    for p in sorted((ROOT/'TESTS').glob('test_*.py')):
        wrapper="import runpy,socket,sys;\ndef interdit(*a,**k):raise RuntimeError('NETWORK_INTERDIT_TEST_HORS_RESEAU')\nsocket.socket.connect=interdit;socket.create_connection=interdit;runpy.run_path(sys.argv[1],run_name='__main__')"
        r = subprocess.run([sys.executable, '-B', '-c', wrapper, str(p)], cwd=ROOT, text=True, capture_output=True,
                           timeout=120, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONOPTIMIZE=''))
        rows.append({'controle': p.name, 'statut': 'OK' if r.returncode == 0 else 'ECHEC',
                     'code_retour': r.returncode, 'detail': r.stdout+r.stderr})
        print(p.name, rows[-1]['statut'], flush=True)
    apres = empreintes()
    changes = sorted(k for k in set(avant)|set(apres) if avant.get(k) != apres.get(k))
    rows.append({'controle': 'integrite_entrees', 'statut': 'ECHEC' if changes else 'OK', 'detail': changes})
    out = ROOT/'AUDITS/TESTS'; out.mkdir(parents=True, exist_ok=True)
    report = {'date_utc': datetime.now(timezone.utc).isoformat(), 'commit': subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), 'empreintes_sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('SCRIPTS_ACTIFS','TESTS','CONFIG') for p in (ROOT/folder).glob('*') if p.is_file() and p.suffix in ('.py','.csv','.json')}, 'controles': rows,
        'statut': 'OK' if all(x['statut']=='OK' for x in rows) else 'ECHEC'}
    (out/'RESULTATS_TESTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Réception:', report['statut'])
    return 0 if report['statut']=='OK' else 1
if __name__=='__main__': sys.exit(executer())

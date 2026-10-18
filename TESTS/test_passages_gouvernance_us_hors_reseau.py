"""Ne pas convertir propriété bénéficiaire/options en détention personnelle."""
from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('passages',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AO_PASSAGES_GOUVERNANCE_US.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 raw=b'<html><style>All directors and officers as a group FAKE</style><script>FAKE</script><table><tr><td>All directors and executive officers as a group (13 persons)</td><td>1,381,722</td><td>2.8%</td></tr></table><p>Includes shares exercisable within 60 days: 358,288.</p></html>'
 text=m.texte_brut(raw);p=m.extraire(text)
 assert 'FAKE' not in text
 assert any(r['Nature']=='DETENTION_GROUPE' and '1,381,722' in r['Passage'] and '358,288' in r['Passage'] for r in p)
 assert any(r['Nature']=='DROITS_A_60_JOURS' for r in p)
 assert all(text[r['Debut_texte_normalise']:r['Fin_texte_normalise']]==r['Passage'] for r in p)
 assert all(r['Note_SSI']=='NON_ATTRIBUEE' and 'Titres_reels' not in r for r in p)
 assert m.extraire('Company has no table of this type')==[]
 assert any(r['Nature']=='DETENTION_GROUPE' for r in m.extraire('All current officers and directors as a group (5 persons)'))
 assert len([r for r in m.extraire(('All directors and officers as a group. ')*10) if r['Nature']=='DETENTION_GROUPE'])==1
 try:m.texte_brut(b'%PDF-1.7')
 except ValueError:pass
 else:raise AssertionError('PDF traité comme HTML')
 print('Passages gouvernance : groupe et droits conservés avec contexte, ancrages reproductibles, aucun score ni détention personnelle inventée')
if __name__=='__main__':test()

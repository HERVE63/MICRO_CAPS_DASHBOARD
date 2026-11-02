"""07Q2 : prioriser les paires de sources archivées sans certifier ni noter.

Fixtures fictives hors réseau. Le calcul ne fait aucune écriture dans DONNEES.
"""
from pathlib import Path
import importlib.util
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"SCRIPTS_ACTIFS"))
spec=importlib.util.spec_from_file_location("audit_07q2_paires",ROOT/"SCRIPTS_ACTIFS/07Q2_AUDIT_PREUVES_SSI.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def capture(id_doc,url,sha,ident="ISIN:FR0011271600",date="2026-10-01",
            type_source="PUBLICATION_EMETTEUR",isin="OUI",symbole="NON_APPLICABLE"):
    return (ident,url,sha,date=="INCONNUE",date,"2026-10-02T00:00:00Z",
            id_doc,"AUDITS/SOURCES_OFFICIELLES/fixture.bin",type_source,
            "text/html",isin,symbole)

def tester():
    a=capture("DOC_A","https://www.emetteur.fr/a","a"*64)
    b=capture("DOC_B","https://live.marche.fr/b","b"*64)
    assert len(m.paires_documentaires_a_revoir([a,b]))==1
    assert set(m.paires_documentaires_a_revoir([a,b])[0])=={"DOC_A","DOC_B"}
    # Meme organisation, deux sous-domaines : ce n'est PAS l'independance.
    same=capture("DOC_C","https://investors.emetteur.fr/c","c"*64)
    assert m.paires_documentaires_a_revoir([a,same])==[]
    # La duplication exacte d'un document ne cree pas une deuxieme preuve.
    assert m.paires_documentaires_a_revoir([a,a])==[]
    assert m.paires_documentaires_a_revoir([a,capture("DOC_D",b[1],a[2])])==[]
    # Une accession documentaire ID identique n'est pas deux pieces independantes.
    assert m.paires_documentaires_a_revoir([a,capture("DOC_A",b[1],b[2])])==[]
    # Repetitions contradictoires (meme URL/SHA, date differente) : quarantaine.
    contradictoire=capture("DOC_B",b[1],b[2],date="2026-09-30")
    assert m.paires_documentaires_a_revoir([a,b,contradictoire])==[]
    # Publication inconnue, identite divergente ou ISIN absent du brut.
    assert m.paires_documentaires_a_revoir([a,capture("DOC_E",b[1],b[2],date="INCONNUE")])==[]
    assert m.paires_documentaires_a_revoir([a,capture("DOC_F",b[1],b[2],ident="ISIN:FR001400A3Q3")])==[]
    assert m.paires_documentaires_a_revoir([a,capture("DOC_G",b[1],b[2],isin="NON")])==[]
    # Une fiche marche doit aussi afficher explicitement le symbole observe.
    marche=capture("DOC_H",b[1],b[2],type_source="DONNEE_MARCHE_IDENTITE",symbole="NON")
    assert m.paires_documentaires_a_revoir([a,marche])==[]
    marche_valide=capture("DOC_H",b[1],b[2],type_source="DONNEE_MARCHE_IDENTITE",symbole="OUI")
    assert len(m.paires_documentaires_a_revoir([a,marche_valide]))==1
    # Suffixes publics composes : deux organisations sous co.uk sont distinctes.
    x=capture("X","https://alpha.co.uk/a","d"*64)
    y=capture("Y","https://beta.co.uk/b","e"*64)
    assert len(m.paires_documentaires_a_revoir([x,y]))==1
    print("07Q2 PAIRES : controles de provenance, dates, identite, SHA256, organisations ; 0 note et 0 certification")

if __name__=="__main__":
    tester()

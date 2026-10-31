"""Régression hors réseau : SSI accepte ISIN/LEI uniquement sur preuves concordantes.
Toutes les sociétés, documents et notes ci-dessous sont des fixtures fictives.
Aucun score économique ni admission réelle ne provient de ce test.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import importlib.util
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"SCRIPTS_ACTIFS"))
from preuves_ssi import CHAMPS, valider_dossier, identifiant_dossier

def test():
    script=ROOT/"SCRIPTS_ACTIFS/07R_VALIDER_NOTES_SSI.py"
    spec=importlib.util.spec_from_file_location("ssi_reglementaire_fixture",script)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    with TemporaryDirectory() as tmp:
        base=Path(tmp)
        d=base/"DONNEES"
        d.mkdir()
        brut=base/"preuve_fictive.bin"
        brut.write_bytes(b"FIXTURE NON REGLEMENTAIRE - TEST HORS RESEAU")
        sha=hashlib.sha256(brut.read_bytes()).hexdigest()
        ident="ISIN:US0378331005"  # exemple de checksum, pas une attribution d'emetteur
        dossier=dict(Ticker="EXEMPLE.F",CIK="",Identifiant_emetteur_verifie=ident,
                     Conflit_identite_CIK="NON",SCE_valide="OUI",
                     Preuves_identite_SCE="SCE1|SCE2",
                     Decision_eliminatoire="NON",Motif_eliminatoire="EX1")
        preuves=[]
        for i,(pid,bloc) in enumerate([("SCE1","IDENTITE_SCE"),("SCE2","IDENTITE_SCE"),
                                       ("EX1","EXCLUSIONS")]+[("P"+str(n),"B"+str(n)) for n in range(1,8)]):
            r=dict.fromkeys(CHAMPS,"")
            r.update(ID_preuve=pid,Ticker="EXEMPLE.F",Bloc=bloc,
                     Identifiant_emetteur=ident,Source_URL="https://example.org/fixture/"+pid,
                     Type_source="DEPOT_REGLEMENTAIRE",Date_publication="2026-01-01",
                     Fichier_brut="preuve_fictive.bin",SHA256=sha,
                     Statut_identite="VERIFIEE",Statut_verification="VERIFIEE",
                     Verificateur="FIXTURE_INDEPENDANTE",Date_verification_UTC="2026-01-02T00:00:00Z",
                     Justification="FICTION POUR TEST",Note="10" if bloc.startswith("B") else "")
            preuves.append(r)
        for n in range(1,8):
            dossier["Note_B"+str(n)]="10"
            dossier["Preuve_B"+str(n)]="P"+str(n)
        reg=pd.DataFrame(preuves)
        reg.to_csv(d/"REGISTRE_PREUVES_SSI.csv",index=False)
        pd.DataFrame([dossier]).to_csv(d/"DOSSIERS_SSI_A_QUALIFIER.csv",index=False)
        assert identifiant_dossier(pd.Series(dossier))==ident
        notes,errors=valider_dossier(pd.Series(dossier),reg,base)
        assert not errors and sum(notes)==70,(notes,errors)
        m.D,m.SRC,m.OUT,m.AUD=d,d/"DOSSIERS_SSI_A_QUALIFIER.csv",d/"RESULTATS_SSI.csv",d/"AUDIT_SSI.csv"
        result=m.executer()
        assert result.iloc[0].Statut_SSI=="ADMIS_SSI" and result.iloc[0].SSI=="70"
        # Un identifiant auto-déclaré ne suffit pas : vérification des deux preuves.
        for invalide in ("ISIN:US0378331006","ISIN:MANQUANTE","LEI:5493001KJTIIGC8Y1R13"):
            autre=pd.Series({**dossier,"Identifiant_emetteur_verifie":invalide})
            assert identifiant_dossier(autre)==""
            assert valider_dossier(autre,reg,base)[1]
        autre=pd.Series({**dossier,"CIK":"123"})
        assert identifiant_dossier(autre)=="", "Un CIK malformé ne peut être masqué par un ISIN"
        autre=pd.Series({**dossier,"CIK":"0000001234"})
        assert identifiant_dossier(autre)=="", "Un CIK présent divergent ne peut être masqué par un ISIN"
        autre=pd.Series({**dossier,"Conflit_identite_CIK":"OUI"})
        assert valider_dossier(autre,reg,base)[1]
        autre_reg=reg.copy()
        autre_reg.loc[autre_reg.ID_preuve.eq("SCE2"),"Identifiant_emetteur"]="ISIN:US0378331006"
        assert valider_dossier(pd.Series(dossier),autre_reg,base)[1]
        autre_reg=reg.copy()
        autre_reg.loc[autre_reg.ID_preuve.eq("P1"),"Identifiant_emetteur"]="CIK:0000001234"
        assert valider_dossier(pd.Series(dossier),autre_reg,base)[1]
        brut.write_bytes(b"DOCUMENT ALTERE")
        assert valider_dossier(pd.Series(dossier),reg,base)[1]
    print("SSI identité réglementaire : checksum, preuves, collision, SHA256 et cohorte fictive OK")

if __name__=="__main__":
    test()

import importlib.util
import tempfile
import shutil
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def test_05c_sale_then_purchase():
    with tempfile.TemporaryDirectory() as t:
        b=Path(t)
        for d in ("SCRIPTS_ACTIFS","DONNEES","CONFIG"): (b/d).mkdir()
        for p in ("SCRIPTS_ACTIFS/05C_REPLAY_PORTEFEUILLE_GERE.py","DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv","CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv"):
            shutil.copy2(ROOT/p,b/p)
        source=pd.read_csv(ROOT/"DONNEES/ETAT_INITIAL_PORTEFEUILLE_GERE.csv")
        cols=pd.read_csv(ROOT/"DONNEES/JOURNAL_ARBITRAGES_GERE.csv",nrows=0).columns
        qty=float(source.iloc[0]["Quantite"])
        gross=qty*10
        proceeds=gross*.975
        fee=proceeds*.025/1.025
        rows=[]
        sale=dict(ID_operation="SIM_S",Date_execution="2026-10-30",Sequence_execution=1,Type_operation="SORTIE",ID_ligne_sortante=1,Cours_execution_sortie=10,FX_sortie_vers_EUR=1,Frais_sortie_EUR=gross*.025,Statut_operation="EXECUTEE")
        buy=dict(ID_operation="SIM_B",Date_execution="2026-10-30",Sequence_execution=2,Type_operation="ENTREE",Societe_entrante="Simulation",Ticker_entrant="SIM",Devise_entrante="EUR",Montant_EUR=proceeds,Cours_execution_entree=20,FX_entree_vers_EUR=1,Frais_entree_EUR=fee,Statut_operation="EXECUTEE")
        pd.DataFrame([sale,buy],columns=cols).to_csv(b/"DONNEES/JOURNAL_ARBITRAGES_GERE.csv",index=False)
        spec=importlib.util.spec_from_file_location("isolated_replay",b/"SCRIPTS_ACTIFS/05C_REPLAY_PORTEFEUILLE_GERE.py")
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        result=m.executer()
        assert result["nb_actives"]==40
        assert result["nb_sorties"]==1
        assert abs(result["cash"])<1e-8
        positions=result["positions"]
        assert positions.loc[positions["ID_position"].astype(str)=="1","Statut"].iloc[0]=="SORTI"
        q=float(positions.loc[positions["ID_position"].astype(str)=="NEW_SIM_B","Quantite"].iloc[0])
        assert abs(q-(proceeds-fee)/20)<1e-8
        assert pd.read_csv(ROOT/"DONNEES/JOURNAL_ARBITRAGES_GERE.csv").empty

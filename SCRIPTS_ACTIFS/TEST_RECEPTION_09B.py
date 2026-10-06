# -*- coding: utf-8 -*-
from pathlib import Path
import importlib.util
import pandas as pd
BASE=Path(__file__).resolve().parent.parent
P=BASE/"SCRIPTS_ACTIFS"/"09B_DUEL_PROCHAIN_EURO.py"
spec=importlib.util.spec_from_file_location("duel",P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def l(t,i,n,s,d): return {"Type":t,"ID_position":i,"Societe":n,"MCPA":s,"Decision":d,"Challengers_compares":"TEST"}
x=pd.DataFrame([l("TITULAIRE","1","SOURCE",80,"VENDRE"),l("CHALLENGER","C1","CHAL",80,"SONDE")])
r=m.calculer_duels(x); assert len(r)==1 and r.iloc[0]["Statut_duel"]=="CONSERVER"
x=pd.DataFrame([l("TITULAIRE","1","SOURCE",70,"VENDRE"),l("TITULAIRE","2","A",90,"RENFORCER"),l("TITULAIRE","3","B",90,"RENFORCER"),l("CHALLENGER","C1","C",85,"SONDE")])
r=m.calculer_duels(x); assert len(r)==2 and set(r["Societe_destination"])=={"A","B"} and all(abs(float(v)-.5)<1e-12 for v in r["Part_allocation"])
x=pd.DataFrame([l("TITULAIRE","1","SOURCE",70,"VENDRE"),l("TITULAIRE","2","A",85,"RENFORCER"),l("CHALLENGER","C1","C",90,"SONDE")])
r=m.calculer_duels(x); assert len(r)==1 and r.iloc[0]["Societe_destination"]=="C" and abs(float(r.iloc[0]["Part_allocation"])-1)<1e-12
print("RECEPTION 09B OK")

# déclenchement réception CI

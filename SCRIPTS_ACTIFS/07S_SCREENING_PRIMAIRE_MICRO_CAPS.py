# -*- coding: utf-8 -*-
"""Screening primaire MICRO CAPS reconstruit selon l'architecture maître.
Aucun score économique n'est calculé ici : actions cotées USA/Canada/Europe,
capitalisation 50-300 MEUR, puis transmission aux briques SSI/MCPA/IPS.
"""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import pandas as pd
import yfinance as yf
from yfinance import EquityQuery

BASE=Path(__file__).resolve().parent.parent
OUT=BASE/"DONNEES"/"SORTIE_CHASSEUR_EXISTANT.csv"
PARAMS=BASE/"CONFIG"/"PARAMETRES_SCE_MICRO_CAPS.csv"
FXPATH=BASE/"SCRIPTS_ACTIFS"/"03B_MOTEUR_FX_V3.py"

REGIONS={
 "us":("USD","USA"),"ca":("CAD","Canada"),
 "gb":("GBP","Royaume-Uni"),"fr":("EUR","France"),"de":("EUR","Allemagne"),
 "nl":("EUR","Pays-Bas"),"be":("EUR","Belgique"),"es":("EUR","Espagne"),
 "pt":("EUR","Portugal"),"it":("EUR","Italie"),"fi":("EUR","Finlande"),
 "se":("SEK","Suède"),"dk":("DKK","Danemark"),"no":("NOK","Norvège"),
 "ch":("CHF","Suisse")
}

def charger_fx():
    spec=importlib.util.spec_from_file_location("fx_screen",FXPATH)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def bornes():
    p=pd.read_csv(PARAMS).set_index("Parametre")
    return float(p.loc["Capitalisation_min","Valeur"])*1e6,float(p.loc["Capitalisation_max","Valeur"])*1e6

def executer():
    mini,maxi=bornes()
    fxm=charger_fx()
    # Devises supplémentaires nécessaires au périmètre européen du chasseur.
    paires_extra={"DKK":"EURDKK=X","NOK":"EURNOK=X","CHF":"EURCHF=X"}
    fx=dict(fxm.tous_les_fx(datetime.now(timezone.utc)))
    anciennes=dict(fxm.PAIRES)
    try:
        fxm.PAIRES.update(paires_extra)
        for d in paires_extra:
            fx[d]=fxm.dernier_fx_termine(d,datetime.now(timezone.utc))
    finally:
        fxm.PAIRES.clear(); fxm.PAIRES.update(anciennes)

    date=datetime.now(timezone.utc).date().isoformat()
    lignes=[]
    for region,(devise,pays) in REGIONS.items():
        taux=float(fx[devise]["fx_vers_eur"])
        lo,hi=mini/taux,maxi/taux
        q=EquityQuery("and",[
            EquityQuery("eq",["region",region]),
            EquityQuery("btwn",["intradaymarketcap",lo,hi])
        ])
        offset=0
        vus=set()
        while True:
            rep=yf.screen(q,offset=offset,size=250,sortField="intradaymarketcap",sortAsc=True)
            quotes=rep.get("quotes",[]) if isinstance(rep,dict) else []
            if not quotes: break
            nouveaux=0
            for x in quotes:
                ticker=str(x.get("symbol","")).strip()
                if not ticker or ticker in vus: continue
                vus.add(ticker); nouveaux+=1
                cap=x.get("marketCap",x.get("intradaymarketcap"))
                try: cap=float(cap)
                except Exception: continue
                cap_eur=cap*taux
                if not (mini <= cap_eur <= maxi): continue
                nom=str(x.get("shortName") or x.get("longName") or ticker).strip()
                lignes.append({
                    "Date_detection":date,"Societe":nom,"Ticker":ticker,
                    "Devise":devise,"Pays":pays,"Capitalisation_EUR":round(cap_eur,2),
                    "Source_detection":"Yahoo Finance / yfinance EquityQuery",
                    "Date_source":date,
                    "These_initiale":"Détection mécanique 50-300 MEUR ; qualification SSI requise.",
                    "Statut_chasse":"DETECTE"
                })
            if len(quotes)<250 or nouveaux==0: break
            offset+=250
            if offset>=5000: raise RuntimeError(f"Pagination incomplète pour {region}.")
    df=pd.DataFrame(lignes)
    if df.empty: raise RuntimeError("Chasseur : aucun candidat détecté.")
    df=df.drop_duplicates(subset=["Ticker"]).sort_values(["Pays","Capitalisation_EUR","Ticker"])
    tmp=OUT.with_suffix(".tmp"); df.to_csv(tmp,index=False); tmp.replace(OUT)
    print(f"Chasseur primaire : {len(df)} candidats 50-300 MEUR.")
    return df

if __name__=="__main__":
    executer()

# réception CI

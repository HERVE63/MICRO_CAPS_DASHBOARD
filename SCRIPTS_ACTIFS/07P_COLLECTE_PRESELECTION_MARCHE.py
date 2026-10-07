# -*- coding: utf-8 -*-
"""07P - collecte marche homogene pour la preselection MICRO CAPS.
Ce module ne calcule ni SSI ni MCPA et ne rejette aucune societe.
Il produit uniquement des variables observables calculees avec la meme
methode pour tous les tickers detectes. Toute absence reste MANQUANTE.
"""
from pathlib import Path
from datetime import date
import time
import pandas as pd
import yfinance as yf

BASE=Path(__file__).resolve().parents[1]
SRC=BASE/"DONNEES"/"CHASSE_CANDIDATS.csv"
OUT=BASE/"DONNEES"/"PRESELECTION_VARIABLES_MARCHE.csv"

def _series(frame, field, ticker):
    if frame is None or frame.empty: return pd.Series(dtype=float)
    try:
        s=frame[field][ticker] if isinstance(frame.columns,pd.MultiIndex) else frame[field]
        return pd.to_numeric(s,errors="coerce").dropna()
    except Exception:
        return pd.Series(dtype=float)

def executer():
    if not SRC.exists(): raise RuntimeError("CHASSE_CANDIDATS absent.")
    u=pd.read_csv(SRC)
    if u.empty: raise RuntimeError("CHASSE_CANDIDATS vide.")
    if "Ticker" not in u.columns: raise RuntimeError("Ticker absent.")
    tickers=u["Ticker"].dropna().astype(str).str.strip()
    tickers=list(dict.fromkeys([x for x in tickers if x]))
    rows=[]
    # Lots limites: meme source, meme fenetre, meme formule pour tout l'univers.
    for debut in range(0,len(tickers),100):
        lot=tickers[debut:debut+100]
        try:
            h=yf.download(lot,period="1y",interval="1d",auto_adjust=False,
                          progress=False,threads=True,group_by="column")
        except Exception:
            h=pd.DataFrame()
        for t in lot:
            close=_series(h,"Close",t)
            vol=_series(h,"Volume",t)
            commun=close.index.intersection(vol.index)
            close=close.loc[commun]; vol=vol.loc[commun]
            n=len(close)
            statut="OK" if n>=126 else "MANQUANTE"
            last=float(close.iloc[-1]) if n else None
            # Volume monetaire median en devise locale, comparable comme mesure
            # de praticabilite seulement apres conversion FX ulterieure.
            dv=(close*vol).tail(63)
            med=float(dv.median()) if len(dv) else None
            def mom(k):
                return (float(last/close.iloc[-k]-1)*100) if n>=k and close.iloc[-k]>0 else None
            ma200=float(close.tail(200).mean()) if n>=200 else None
            rows.append({
                "Date_scan":date.today().isoformat(),"Ticker":t,
                "Nb_seances_1a":n,"Dernier_cours_local":last,
                "Volume_monetaire_median_63s_local":med,
                "Momentum_3m_pct":mom(63),"Momentum_6m_pct":mom(126),
                "MM200":ma200,
                "Au_dessus_MM200":(bool(last>ma200) if last is not None and ma200 is not None else None),
                "Source_marche":"Yahoo Finance / yfinance - historique quotidien 1 an",
                "Statut_donnees_marche":statut
            })
        time.sleep(0.2)
    out=pd.DataFrame(rows)
    tmp=OUT.with_suffix(".tmp"); out.to_csv(tmp,index=False); tmp.replace(OUT)
    print(f"Variables marche: {len(out)} tickers; OK={(out['Statut_donnees_marche']=='OK').sum()}; MANQUANTE={(out['Statut_donnees_marche']!='OK').sum()}")
    return out

if __name__=="__main__":
    executer()

# reception HEAD controlee 2026-10-07 - tentative 3

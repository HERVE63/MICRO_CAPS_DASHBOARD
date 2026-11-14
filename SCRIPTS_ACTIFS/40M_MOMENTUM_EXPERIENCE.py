#!/usr/bin/env python3
"""Experience virtuelle: classement momentum; aucune validation MCPA ni ordre.
Cours historiques déjà archivés acceptés comme historique, sans nouvelle collecte hors Zonebourse.
"""
import csv,json,math
from pathlib import Path
from datetime import date,timedelta
ROOT=Path(__file__).resolve().parents[1];D=ROOT/"DONNEES"
def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def number(v):
    try:
        n=float(v)
        return n if math.isfinite(n) else None
    except (ValueError,TypeError):return None
def main():
    holdings=read(D/"ETAT_INITIAL_PORTEFEUILLE_GERE.csv")
    assert len(holdings)==40
    history_file=D/"HISTORIQUES_YAHOO_40.csv"
    bars={}
    if history_file.exists():
        for row in read(history_file):
            value=number(row.get("AdjClose"))
            if value is not None and value>0:
                bars.setdefault(row["Ticker"],[]).append((date.fromisoformat(row["Date_UTC"]),value,number(row.get("Volume"))))
    out=[]
    for h in holdings:
        ticker=h["Ticker"]
        matches=list((ROOT/"DOSSIERS_MCPA_IPS_40").glob("*_"+ticker+".json"))
        assert len(matches)==1,(ticker,matches)
        x=json.loads(matches[0].read_text(encoding="utf-8"))
        m=x["blocs"]["momentum"]
        history=sorted(bars.get(ticker,[]))
        end=history[-1][0] if history else None
        def period_return(days):
            if not history:return None
            target=end-timedelta(days=days)
            candidates=[(d,p) for d,p,_ in history if target-timedelta(days=10)<=d<=target+timedelta(days=3)]
            if not candidates:return None
            prev=min(candidates,key=lambda row:abs((row[0]-target).days))[1]
            return 100*(history[-1][1]/prev-1)
        vals={key:period_return(days) for key,days in (("1m",30),("2m",61),("3m",91))}
        # Un cours Zonebourse date prime sur l'historique uniquement si le point de depart
        # du meme horizon est connu; pas de combinaison artificielle de deux fournisseurs.
        for key in ("1m","3m"):
            item=m.get("momentum_"+key+"_pct",{})
            v=number(item.get("valeur"))
            if v is not None and "zonebourse.com" in (item.get("source_url") or ""):
                vals[key]=v
        vol=number(sum(v for _,_,v in history[-20:] if v is not None)/20) if len(history)>=20 and all(v is not None for _,_,v in history[-20:]) else None
        valid=all(vals[k] is not None for k in ("1m","2m","3m")) and vol is not None
        # Score simple equipondere; poids ajustables apres validation du protocole.
        score=sum(vals.values())/3 if valid else None
        out.append({"Ticker":ticker,"Date_historique":end.isoformat() if end else "","Momentum_1m_pct":vals["1m"],"Momentum_2m_pct":vals["2m"],"Momentum_3m_pct":vals["3m"],"Score_momentum_moyenne_pct":score,"Volume_moyen_20j":vol,"Statut":"CALCULABLE_HISTORIQUE_A_ACTUALISER_ZONEBOURSE" if valid else "INCOMPLET_SANS_SIGNAL","Signal":"OBSERVATION" if valid else "AUCUN","Source":"Zonebourse pour les champs deja raccordes; archives historiques existantes pour les autres","Arbitrage_autorise":"NON"})
    ranked=sorted([x for x in out if x["Score_momentum_moyenne_pct"] is not None],key=lambda x:x["Score_momentum_moyenne_pct"],reverse=True)
    for i,row in enumerate(ranked,1):row["Rang_momentum"]=i
    for row in out:row.setdefault("Rang_momentum","")
    target=D/"EXPERIENCE_MOMENTUM_40.csv"
    with target.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print(json.dumps({"fiches":len(out),"signaux_calculables":sum(x["Statut"].startswith("CALCULABLE") for x in out),"fiches_incompletes":sum(x["Statut"].startswith("INCOMPLET") for x in out),"sortie":str(target)},ensure_ascii=False))
if __name__=="__main__":main()

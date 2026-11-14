#!/usr/bin/env python3
"""Experience virtuelle: classement momentum; aucune validation MCPA ni ordre.
Cours historiques déjà archivés acceptés comme historique, sans nouvelle collecte hors Zonebourse.
"""
import csv,json,math
from pathlib import Path
from datetime import date
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
    source=D/"INDICATEURS_YAHOO_40.csv"
    historic={r["Ticker"]:r for r in read(source)} if source.exists() else {}
    out=[]
    for h in holdings:
        ticker=h["Ticker"];p=ROOT/"DOSSIERS_MCPA_IPS_40"/(h["ID_position"].zfill(2)+"_"+ticker+".json")
        # Find by ticker rather than presuming a filename convention.
        matches=list((ROOT/"DOSSIERS_MCPA_IPS_40").glob("*_"+ticker+".json"))
        assert len(matches)==1,(ticker,matches)
        x=json.loads(matches[0].read_text(encoding="utf-8"))
        m=x["blocs"]["momentum"];hist=historic.get(ticker,{})
        vals={}
        for key,field in (("1m","Momentum_1m"),("3m","Momentum_3m"),("6m","Momentum_6m"),("12m","Momentum_12m")):
            item=m.get("momentum_"+key+"_pct",{})
            v=number(item.get("valeur"))
            # Priorité aux observations Zonebourse déjà raccordées, sinon historique ancien.
            if v is not None and "zonebourse.com" in (item.get("source_url") or ""):
                vals[key]=v;continue
            old=number(hist.get(field))
            vals[key]=100*old if old is not None else v
        mm=number(hist.get("Ratio_prix_MM200"))
        vol=number(hist.get("Volume_moyen_20j"))
        age=hist.get("Date_fin","")
        # 6-1: 12m hors dernier mois, approximation par facteurs de rendement.
        r12,r1=vals["12m"],vals["1m"]
        m61=((1+r12/100)/(1+r1/100)-1)*100 if r12 is not None and r1 is not None and r1>-100 else None
        valid=all(vals[k] is not None for k in ("1m","3m","6m","12m")) and mm is not None and vol is not None and m61 is not None
        out.append({"Ticker":ticker,"Date_historique":age,"Momentum_1m_pct":vals["1m"],"Momentum_3m_pct":vals["3m"],"Momentum_6m_pct":vals["6m"],"Momentum_12m_pct":vals["12m"],"Momentum_6_1_pct":m61,"Ratio_MM200":mm,"Volume_moyen_20j":vol,"Statut":"CALCULABLE_HISTORIQUE_A_ACTUALISER_ZONEBOURSE" if valid else "INCOMPLET_SANS_SIGNAL","Signal":"A_ETUDIER" if valid and mm>1 and m61>0 else ("FAIBLE" if valid else "AUCUN"),"Source":"Zonebourse (momentum raccordé) + archives historiques existantes; pas de nouvelle collecte","Arbitrage_autorise":"NON"})
    ranked=sorted([x for x in out if x["Momentum_6_1_pct"] is not None],key=lambda x:x["Momentum_6_1_pct"],reverse=True)
    for i,r in enumerate(ranked,1):r["Rang_momentum"]=i
    for r in out:r.setdefault("Rang_momentum","")
    target=D/"EXPERIENCE_MOMENTUM_40.csv"
    with target.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print(json.dumps({"fiches":len(out),"signaux_calculables":sum(x["Statut"].startswith("CALCULABLE") for x in out),"fiches_incompletes":sum(x["Statut"].startswith("INCOMPLET") for x in out),"sortie":str(target)},ensure_ascii=False))
if __name__=="__main__":main()

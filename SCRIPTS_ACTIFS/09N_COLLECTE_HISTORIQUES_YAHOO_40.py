#!/usr/bin/env python3
"""Collect public Yahoo chart daily bars for 40 incumbents; no API key.
Unverified or missing series remain missing. No scores or trades.
"""
import csv,json,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone,date,timedelta
from statistics import mean
BASE=Path(__file__).resolve().parents[1]; D=BASE/"DONNEES"
SYMBOL_FIX={"ALSTI.PA":"ALSTI.PA","CEMX.TO":"CEMX.TO"}
HEAD=["ID_position","Ticker","Yahoo_symbol","Date_UTC","Close","AdjClose","Volume","Status","Source"]
def fetch(symbol):
    """Retry the same official Yahoo chart resource on the alternate host.

    A provider/transport failure is not evidence of an absent quotation.
    Never substitute another ticker or silently invent adjusted prices.
    """
    errors=[]
    for host in ("query1.finance.yahoo.com","query2.finance.yahoo.com"):
        url="https://"+host+"/v8/finance/chart/"+urllib.parse.quote(symbol,safe="") + "?range=5y&interval=1d&events=div%2Csplits"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 MicroCapsResearch/1.0","Accept":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=18) as response: obj=json.load(response)
            result=obj.get("chart",{}).get("result") or []
            if not result or not isinstance(result[0],dict):
                raise ValueError("YAHOO_CHART_RESULT_ABSENT")
            return result[0],url
        except (urllib.error.URLError,ValueError,KeyError,TypeError,IndexError) as exc:
            errors.append(type(exc).__name__)
    raise RuntimeError("YAHOO_HOSTS_FAILED:"+",".join(errors))
INDICATOR_HEAD=["ID_position","Ticker","Date_fin","Seances_ajustees","MM200","Ratio_prix_MM200","Momentum_1m","Momentum_3m","Momentum_6m","Momentum_12m","Volume_moyen_20j","Statut_indicateurs","Source"]
def compute_indicators(position, ticker, bars, source):
    """Price-only indicators; missing windows remain empty, never extrapolated."""
    clean=sorted([(date.fromisoformat(r[3]),float(r[5]),float(r[6]) if r[6]!="" else None) for r in bars if r[5]!="" and float(r[5])>0],key=lambda x:x[0])
    if not clean:return [position,ticker,"",0,"","","","","","","","MISSING_ADJUSTED",source]
    end,latest,_=clean[-1]
    mm=mean(x[1] for x in clean[-200:]) if len(clean)>=200 else None
    def momentum(days):
        target=end-timedelta(days=days)
        candidates=[x for x in clean if target-timedelta(days=10)<=x[0]<=target+timedelta(days=3)]
        if not candidates:return ""
        previous=min(candidates,key=lambda x:abs((x[0]-target).days))
        return latest/previous[1]-1
    vals=[momentum(d) for d in (30,91,182,365)]
    vols=[x[2] for x in clean[-20:] if x[2] is not None]
    v20=mean(vols) if len(vols)==20 else ""
    status="OK" if mm is not None and all(v!="" for v in vals) and v20!="" else "PARTIAL_INDICATORS"
    return [position,ticker,end.isoformat(),len(clean),mm if mm is not None else "",latest/mm if mm else "",*vals,v20,status,source]
def main():
    with (D/"ETAT_INITIAL_PORTEFEUILLE_GERE.csv").open(encoding="utf-8-sig",newline="") as f: holdings=list(csv.DictReader(f))
    if len(holdings)!=40:raise RuntimeError("40 positions required")
    rows=[]; summary=[]; indicators=[]
    for p in holdings:
        symbol=SYMBOL_FIX.get(p["Ticker"],p["Ticker"]); n=0; status="OK"; missing_adjusted=0; missing_volume=0; position_rows=[]; url=""
        try:
            obj,url=fetch(symbol)
            quote=obj["indicators"]["quote"][0]
            adjusted=obj["indicators"].get("adjclose",[{}])[0].get("adjclose",[])
            for i,ts in enumerate(obj.get("timestamp",[])):
                close=quote["close"][i]
                if close is None:continue
                adj=adjusted[i] if i<len(adjusted) else None
                if adj is None: missing_adjusted+=1
                vol=quote.get("volume") or []
                volume=vol[i] if i<len(vol) else None
                if volume is None: missing_volume+=1
                bar=[p["ID_position"],p["Ticker"],symbol,datetime.fromtimestamp(ts,timezone.utc).strftime("%Y-%m-%d"),close,adj if adj is not None else "",volume if volume is not None else "", "MISSING_ADJUSTED" if adj is None else "OK",url];rows.append(bar);position_rows.append(bar);n+=1
            if n<2:status="INSUFFICIENT_HISTORY"
            elif missing_adjusted:status="MISSING_ADJUSTED"
            elif missing_volume:status="MISSING_VOLUME"
        except Exception as e:status="FAILED_"+type(e).__name__
        indicators.append(compute_indicators(p["ID_position"],p["Ticker"],position_rows,url))
        summary.append([p["ID_position"],p["Ticker"],symbol,n,status,n-missing_adjusted,n-missing_volume, "OUI" if n>=200 and missing_adjusted==0 else "NON", "OUI" if n>=252 and missing_adjusted==0 else "NON"])
        time.sleep(0.35)
    for filename,headers,data in [("HISTORIQUES_YAHOO_40.csv",HEAD,rows),("COUVERTURE_HISTORIQUES_YAHOO_40.csv",["ID_position","Ticker","Yahoo_symbol","Nb_seances","Statut","Seances_ajustees","Seances_volume","MM200_eligible","Momentum_12m_eligible"],summary),("INDICATEURS_YAHOO_40.csv",INDICATOR_HEAD,indicators)]:
        target=D/filename;tmp=target.with_suffix(".tmp")
        with tmp.open("w",encoding="utf-8",newline="") as f:w=csv.writer(f);w.writerow(headers);w.writerows(data)
        tmp.replace(target)
    print(json.dumps({"titulaires":len(summary),"avec_historique":sum(int(x[3])>=2 for x in summary),"barres":len(rows),"erreurs":[x for x in summary if x[4]!="OK"]},ensure_ascii=False))
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Collect public Yahoo chart daily bars for 40 incumbents; no API key.
Unverified or missing series remain missing. No scores or trades.
"""
import csv,json,time,urllib.parse,urllib.request
from pathlib import Path
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parents[1]; D=BASE/"DONNEES"
SYMBOL_FIX={"ALSTI.PA":"ALSTI.PA","CEMX.TO":"CEMX.TO"}
HEAD=["ID_position","Ticker","Yahoo_symbol","Date_UTC","Close","AdjClose","Volume","Status","Source"]
def fetch(symbol):
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="") + "?range=5y&interval=1d&events=div%2Csplits"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 MicroCapsResearch/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=18) as response: obj=json.load(response)
    return obj["chart"]["result"][0],url
def main():
    with (D/"ETAT_INITIAL_PORTEFEUILLE_GERE.csv").open(encoding="utf-8-sig",newline="") as f: holdings=list(csv.DictReader(f))
    if len(holdings)!=40:raise RuntimeError("40 positions required")
    rows=[]; summary=[]
    for p in holdings:
        symbol=SYMBOL_FIX.get(p["Ticker"],p["Ticker"]); n=0; status="OK"; missing_adjusted=0
        try:
            obj,url=fetch(symbol)
            quote=obj["indicators"]["quote"][0]
            adjusted=obj["indicators"].get("adjclose",[{}])[0].get("adjclose",[])
            for i,ts in enumerate(obj.get("timestamp",[])):
                close=quote["close"][i]
                if close is None:continue
                adj=adjusted[i] if i<len(adjusted) else None
                if adj is None: missing_adjusted+=1
                rows.append([p["ID_position"],p["Ticker"],symbol,datetime.fromtimestamp(ts,timezone.utc).strftime("%Y-%m-%d"),close,adj if adj is not None else "",quote["volume"][i],"OK",url]);n+=1
            if n<2:status="INSUFFICIENT_HISTORY"
            elif missing_adjusted:status="MISSING_ADJUSTED"
        except Exception as e:status="FAILED_"+type(e).__name__
        summary.append([p["ID_position"],p["Ticker"],symbol,n,status])
        time.sleep(0.35)
    for filename,headers,data in [("HISTORIQUES_YAHOO_40.csv",HEAD,rows),("COUVERTURE_HISTORIQUES_YAHOO_40.csv",["ID_position","Ticker","Yahoo_symbol","Nb_seances","Statut"],summary)]:
        target=D/filename;tmp=target.with_suffix(".tmp")
        with tmp.open("w",encoding="utf-8",newline="") as f:w=csv.writer(f);w.writerow(headers);w.writerows(data)
        tmp.replace(target)
    print(json.dumps({"titulaires":len(summary),"avec_historique":sum(int(x[3])>=2 for x in summary),"barres":len(rows),"erreurs":[x for x in summary if x[4]!="OK"]},ensure_ascii=False))
if __name__=="__main__":main()

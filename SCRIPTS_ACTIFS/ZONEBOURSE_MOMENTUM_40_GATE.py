#!/usr/bin/env python3
"""Independent Zonebourse-only momentum gate for the 40 virtual holdings.
No MCPA/SSI/WWWS requirement. Fail closed on missing/stale evidence.
Input CSV: ticker,date,close,volume,source_url (one row per trading session).
"""
import argparse,csv,datetime as dt,math
from collections import defaultdict
from pathlib import Path

def evaluate(path, asof=None):
    asof=asof or dt.date.today()
    groups=defaultdict(dict)
    with open(path,encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            ticker=r["ticker"].strip().upper()
            day=dt.date.fromisoformat(r["date"])
            url=r["source_url"].strip().lower()
            if "zonebourse.com/" not in url and "marketscreener.com/" not in url:
                raise ValueError("SOURCE_NON_ZONEBOURSE:"+ticker)
            close=float(r["close"]); volume=float(r["volume"])
            if not (math.isfinite(close) and close>0 and math.isfinite(volume) and volume>=0):
                raise ValueError("COURS_VOLUME_INVALIDE:"+ticker)
            if day>asof: raise ValueError("DATE_FUTURE:"+ticker)
            if day in groups[ticker]: raise ValueError("DOUBLON_DATE:"+ticker)
            groups[ticker][day]=(close,volume,r["source_url"])
    result=[]
    for ticker,observations in sorted(groups.items()):
        days=sorted(observations)
        last=days[-1]
        row={"ticker":ticker,"last_date":last.isoformat(),"last_close":observations[last][0],
             "last_volume":observations[last][1],"source_url":observations[last][2],
             "status":"OK" if (asof-last).days<=5 else "STALE"}
        for label,days_back in (("1m",30),("2m",61),("3m",92)):
            target=last-dt.timedelta(days=days_back)
            eligible=[d for d in days if d<=target]
            row["momentum_"+label]=round((observations[last][0]/observations[eligible[-1]][0]-1)*100,4) if eligible else None
            if not eligible:row["status"]="INSUFFICIENT_HISTORY"
        if len(days)>=6:
            row["change_5_sessions"]=round((observations[last][0]/observations[days[-6]][0]-1)*100,4)
        else:
            row["change_5_sessions"]=None
            row["status"]="INSUFFICIENT_HISTORY"
        result.append(row)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input_csv")
    p.add_argument("--asof",default=dt.date.today().isoformat())
    p.add_argument("--expected",type=int,default=40)
    args=p.parse_args()
    rows=evaluate(args.input_csv,dt.date.fromisoformat(args.asof))
    ok=sum(r["status"]=="OK" for r in rows)
    print("TITULAIRES",len(rows),"MOMENTUM_VALIDES",ok,"BLOQUES",len(rows)-ok)
    for r in rows:print(r)
    if len(rows)!=args.expected or ok!=args.expected:raise SystemExit(2)

if __name__=="__main__":main()

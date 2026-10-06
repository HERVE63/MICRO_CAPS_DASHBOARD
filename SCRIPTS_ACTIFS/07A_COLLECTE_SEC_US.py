from pathlib import Path
import json, urllib.request
from datetime import date
import pandas as pd

BASE=Path(__file__).resolve().parent.parent
MAP=BASE/"DONNEES"/"UNIVERS_US_CIK.csv"
OUT=BASE/"DONNEES"/"FONDAMENTAUX_US_SEC.csv"

UA="MicroCapsResearch/1.0 contact-required"

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"gzip, deflate"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.load(r)

def dernier(facts,names):
    for name in names:
        node=facts.get("us-gaap",{}).get(name,{})
        for unit, vals in node.get("units",{}).items():
            vals=[v for v in vals if v.get("val") is not None and v.get("filed")]
            if vals:
                v=max(vals,key=lambda x:x["filed"])
                return v["val"],v.get("filed")
    return None,None

def executer():
    if not MAP.exists():
        raise RuntimeError("Mapping US CIK absent.")
    u=pd.read_csv(MAP,dtype={"CIK":str})
    requis={"Societe","Ticker","CIK"}
    if not requis.issubset(u.columns):
        raise RuntimeError("Mapping US incomplet.")
    rows=[]
    for _,r in u.iterrows():
        cik=str(r["CIK"]).split(".")[0].zfill(10)
        data=get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        facts=data.get("facts",{})
        revenue,fd1=dernier(facts,["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet"])
        cash,fd2=dernier(facts,["CashAndCashEquivalentsAtCarryingValue","CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"])
        debt,fd3=dernier(facts,["LongTermDebtAndFinanceLeaseObligationsCurrent","LongTermDebtCurrent","LongTermDebt"])
        fcf_op,fd4=dernier(facts,["NetCashProvidedByUsedInOperatingActivities"])
        capex,fd5=dernier(facts,["PaymentsToAcquirePropertyPlantAndEquipment"])
        fcf=(fcf_op-capex) if fcf_op is not None and capex is not None else None
        filed=max([x for x in [fd1,fd2,fd3,fd4,fd5] if x],default=None)
        rows.append({
            "Date_scan":date.today().isoformat(),"Societe":r["Societe"],"Ticker":r["Ticker"],
            "Devise":"USD","Pays":"USA","CA_TTM":revenue,"FCF":fcf,"Cash":cash,
            "Dette_nette":None if debt is None or cash is None else debt-cash,
            "Source_fondamentaux":f"SEC companyfacts CIK {cik}","Date_source":filed,
            "Statut_SEC":"OK" if filed else "INCOMPLET"
        })
    pd.DataFrame(rows).to_csv(OUT,index=False)
    print("SEC US collectes:",len(rows))
    return pd.DataFrame(rows)

if __name__=="__main__":
    executer()

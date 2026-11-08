#!/usr/bin/env python3
"""Scenarios descriptifs 3/6 mois, frequences historiques NON predictives.
Ne modifie ni fiches certifiees ni revue officielle; aucun ordre.
"""
import csv,collections,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'DONNEES'
SRC=D/'HISTORIQUES_YAHOO_40.csv'
OUT=D/'SCENARIOS_EMPIRIQUES_NON_CERTIFIES_40.csv'
HEAD=['ID_position','Ticker','Horizon','Date_fin_historique','Observations_dependantes','Regime','Seuil_bear_pct','Seuil_bull_pct','Scenario_median_pct','Probabilite_historique_pct','Statut','Methode','Source']
def main():
    groups=collections.defaultdict(list)
    with SRC.open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            if r['AdjClose']:
                try:
                    p=float(r['AdjClose'])
                    if p>0:groups[(r['ID_position'],r['Ticker'])].append((r['Date_UTC'],p,r['Source']))
                except ValueError:pass
    with (D/'ETAT_INITIAL_PORTEFEUILLE_GERE.csv').open(encoding='utf-8-sig',newline='') as f:positions=list(csv.DictReader(f))
    assert len(positions)==40
    result=[]
    for pos in positions:
        key=(pos['ID_position'],pos['Ticker'])
        series=sorted(set(groups.get(key,[])),key=lambda x:x[0])
        for horizon,steps in [('3m',63),('6m',126)]:
            returns=[100*(series[i+steps][1]/series[i][1]-1) for i in range(max(0,len(series)-steps))]
            buckets={'bear':[x for x in returns if x<=-10],
                     'central':[x for x in returns if -10<x<10],
                     'bull':[x for x in returns if x>=10]}
            status='DESCRIPTIF_NON_PREDICTIF' if len(returns)>=126 and all(buckets.values()) else 'INSUFFISANT_OU_REGIME_ABSENT'
            for name,values in buckets.items():
                result.append([*key,horizon,series[-1][0] if series else '',len(returns),name,-10,10,
                               round(statistics.median(values),4) if values else '',
                               round(100*len(values)/len(returns),4) if returns else '',
                               status,'Rendements glissants ajustes, seuils fixes -10/+10%; frequences historiques dependantes, PAS probabilites prospectives',
                               series[-1][2] if series else ''])
    with OUT.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(HEAD);w.writerows(result)
    assert len(result)==240
    print(json.dumps({'titulaires':40,'lignes_scenarios':len(result),'horizons':2,'certifications':0,'transactions':0,'statuts':dict(collections.Counter(r[10] for r in result))}))
if __name__=='__main__':main()

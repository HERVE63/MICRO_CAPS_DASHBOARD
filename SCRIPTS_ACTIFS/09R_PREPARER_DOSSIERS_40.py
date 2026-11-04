#!/usr/bin/env python3
"""Prepare evidence inventory for 40 incumbents; no synthetic scores."""
import csv
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'DONNEES'
def read(name):
 p=D/name
 if not p.exists(): return []
 with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def main():
 positions=read('ETAT_INITIAL_PORTEFEUILLE_GERE.csv')
 if len(positions)!=40: raise RuntimeError('Expected 40 incumbents')
 indicators={r['Ticker']:r for r in read('INDICATEURS_YAHOO_40.csv')}
 public=read('PREUVES_FONDAMENTALES_PUBLIQUES_20261104.csv')
 out=[]
 for p in positions:
  t=p['Ticker']; i=indicators.get(t,{})
  sources=[r for r in public if r.get('Ticker')==t]
  out.append({'ID_position':p['ID_position'],'Ticker':t,'Momentum_3m':i.get('Momentum_3m',''),'Momentum_6m':i.get('Momentum_6m',''),'MM200':i.get('MM200',''),'Preuves_publiques':len(sources),'Sources':' | '.join(dict.fromkeys(r.get('Source_URL','') for r in sources)),'Statut_MCPA':'A_VALIDER','Arbitrage_autorise':'NON'})
 with (D/'DOSSIERS_PREPARATOIRES_40.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
 print('Dossiers preparatoires:',len(out))
if __name__=='__main__': main()

# -*- coding: utf-8 -*-
"""MICRO CAPS — génération du tableau de bord depuis les sorties V3 validées.
Couche d'affichage uniquement : aucun calcul moteur, T0 ou règle de gestion n'est modifié.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd, html

BASE=Path(__file__).resolve().parents[1]
D=BASE/"DONNEES"; APP=BASE/"APPLICATION"; APP.mkdir(exist_ok=True)
P=pd.read_csv(D/"TEST_PORTEFEUILLES_V3.csv")
Q=pd.read_csv(D/"TEST_CONTROLE_QUALITE_V3.csv")
B=pd.read_csv(D/"TEST_BENCHMARKS_V3.csv")
CHASSE=D/"CHASSE_CANDIDATS.csv"; REVUE=D/"REVUE_HEBDOMADAIRE_MCPA_IPS.csv"
C=pd.read_csv(CHASSE) if CHASSE.exists() and CHASSE.stat().st_size>1 else pd.DataFrame()
H=pd.read_csv(REVUE) if REVUE.exists() and REVUE.stat().st_size>1 else pd.DataFrame()
chall=H[H["Type"].astype(str).str.upper()=="CHALLENGER"].copy() if (not H.empty and "Type" in H.columns) else pd.DataFrame()
if not chall.empty:
    chall["MCPA_num"]=pd.to_numeric(chall["MCPA"],errors="coerce")
    chall["SSI_num"]=pd.to_numeric(chall["SSI"],errors="coerce")
    chall=chall[chall["SSI_num"]>=65].sort_values(["MCPA_num","SSI_num"],ascending=False).head(20)
detected=len(C)
qualif_attente=max(detected-len(chall),0)
bad=Q[Q["Statut_qualite"]!="OK"].copy()
valid=len(bad)==0
r=P.iloc[0]
vg=float(r["Total_Gere_EUR"]); vt=float(r["Total_Temoin_EUR"])
pg=float(r["Perf_Gere_Portefeuille_pct"]); pt=float(r["Perf_Temoin_Portefeuille_pct"])
alpha=float(r["Alpha_Gestion_points"])
date=str(P["Date_cloture"].max())
def pc(x): return f"{x:+.2f}%"
def cls(x): return "positive" if x>0 else ("negative" if x<0 else "neutral")
match=f"""<tr class="managed"><td><strong>🟢 PORTEFEUILLE GÉRÉ</strong><div class="sub">arbitrages autorisés</div></td><td>{100+pg:.2f}</td><td class="{cls(pg)}">{pc(pg)}</td><td>—</td></tr>
<tr><td><strong>⚪ JUMEAU SANS ARBITRAGES</strong><div class="sub">40 positions T0 figées</div></td><td>{100+pt:.2f}</td><td class="{cls(pt)}">{pc(pt)}</td><td>{pc(pt-pg)}</td></tr>"""
for _,x in B.iterrows():
    p=float(x["Performance_pct"]); match+=f"""<tr><td><strong>{html.escape(str(x["Benchmark"]))}</strong><div class="sub">clôt. {x["Date_cloture"]}</div></td><td>{float(x["Base_100"]):.2f}</td><td class="{cls(p)}">{pc(p)}</td><td>{pc(p-pg)}</td></tr>"""
rows=""
S=P.sort_values("Performance_resolue_pct",ascending=False).reset_index(drop=True)
for i,x in S.iterrows():
    p=float(x["Performance_resolue_pct"]); v=float(x["Valeur_Gere_EUR"]); c=float(x["Contribution_resolue_EUR"])
    flag="▲" if p>0 else ("▼" if p<0 else "•")
    rows+=f"""<tr><td class="rank">{i+1}</td><td><strong>{html.escape(str(x["Societe"]))}</strong><div class="sub">{html.escape(str(x["Ticker_cotation"]))} · clôt. {x["Date_cloture"]}</div></td><td class="value">{v:.2f} €</td><td class="{cls(p)}">{flag} {pc(p)}<div class="sub">contribution {c:+.2f} €</div></td></tr>"""
alerts='<div class="validated">🟢 DONNÉES VALIDÉES · 40/40</div>' if valid else f'<div class="alert">⚠️ CONTRÔLE QUALITÉ · {len(bad)} anomalie(s)</div>'
if chall.empty:
    challenger_html=f'<div class="challenger-head"><div><span class="big2">{detected}</span><div class="sub">candidats détectés</div></div><div><span class="big2">0</span><div class="sub">challengers qualifiés</div></div></div><div class="waiting">🔎 Détection active · qualification SSI/MCPA en attente. Aucun score inventé.</div>'
else:
    cards=""
    medals=["🥇","🥈","🥉"]
    for i,(_,x) in enumerate(chall.iterrows()):
        medal=medals[i] if i<3 else f"#{i+1}"
        def val(k,default="—"):
            v=x.get(k,default)
            return default if pd.isna(v) or str(v).strip()=="" else html.escape(str(v))
        cards+=f'<div class="chall-card"><div class="medal">{medal}</div><div class="chall-main"><strong>{val("Societe")}</strong><div class="sub">{val("Ticker")} · {val("Devise")} · Δ {val("Delta")}</div><div class="duel">Duel : {val("Challengers_compares")}</div></div><div class="scores"><strong>MCPA {val("MCPA")}</strong><div class="sub">SSI {val("SSI")} · IC {val("IC")} · CX {val("CX")}</div><span class="pill">{val("Decision","SURVEILLER")}</span></div></div>'
    challenger_html=f'<div class="challenger-head"><div><span class="big2">{detected}</span><div class="sub">candidats détectés</div></div><div><span class="big2">{len(chall)}</span><div class="sub">Top challengers SSI ≥65</div></div></div><div class="chall-list">{cards}</div>'
now=datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
page=f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="apple-mobile-web-app-capable" content="yes"><title>MICRO CAPS</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0b0f14;color:#f4f6f8;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.container{{max-width:850px;margin:auto;padding:18px 10px 60px}}h1{{margin:4px 0 2px;font-size:28px}}.subtitle,.sub{{color:#7e8997;font-size:11px}}.subtitle{{font-size:14px;margin-bottom:18px}}.section{{margin:24px 0 9px;font-size:18px;font-weight:800}}table{{width:100%;border-collapse:collapse;background:#151b23;border-radius:15px;overflow:hidden}}th{{color:#8792a1;font-size:11px;padding:9px 6px;text-align:right}}th:first-child,td:first-child{{text-align:left}}td{{padding:11px 7px;border-top:1px solid #242c36;text-align:right}}.managed{{background:#14251b}}.positive{{color:#57d67c;font-weight:800}}.negative{{color:#ff6d6d;font-weight:800}}.neutral{{color:#f4f6f8}}.alpha{{margin-top:12px;padding:17px;border-radius:15px;text-align:center;background:#181e26}}.alpha .big{{font-size:27px;font-weight:850}}.validated{{margin-top:13px;padding:13px;background:#14271b;border-radius:13px;font-weight:800}}.alert{{margin-top:13px;padding:13px;background:#322617;border-radius:13px}}.rank{{width:30px;text-align:center;color:#75808f}}.value{{white-space:nowrap;color:#c6ccd4}}.footer{{margin-top:20px;color:#687382;font-size:11px;text-align:center}}.challenger-head{{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-bottom:9px}}.challenger-head>div{{background:#151b23;border-radius:15px;padding:13px;text-align:center}}.big2{{font-size:23px;font-weight:850}}.waiting{{background:#151b23;border-radius:15px;padding:18px;color:#aab3bf;text-align:center}}.chall-list{{display:grid;gap:7px}}.chall-card{{display:grid;grid-template-columns:42px 1fr auto;gap:8px;align-items:center;background:#151b23;border-radius:13px;padding:11px}}.medal{{font-size:21px;text-align:center}}.chall-main strong{{font-size:14px}}.duel{{font-size:11px;color:#aeb8c5;margin-top:4px}}.scores{{text-align:right;font-size:12px}}.pill{{display:inline-block;margin-top:5px;padding:3px 7px;border-radius:9px;background:#203047;color:#c8d9ef;font-size:9px;font-weight:800}}@media(max-width:550px){{td{{font-size:12px;padding:10px 5px}}.chall-card{{grid-template-columns:34px 1fr}}.scores{{grid-column:2;text-align:left}}}}
</style></head><body><div class="container"><h1>MICRO CAPS</h1><div class="subtitle">Expérience prospective · T0 01/10/2026 · dernière séance {date}</div>
<div class="section">🏁 MATCH DEPUIS LE T0</div><table><tr><th>Stratégie</th><th>Base 100</th><th>Perf.</th><th>Écart vs géré</th></tr>{match}</table>
<div class="alpha"><div class="sub">ALPHA DE GESTION</div><div class="big">{alpha:+.2f} pt</div><div class="sub">Géré − Jumeau sans arbitrages</div></div>{alerts}
<div class="section">🏆 CANDIDATS CONCURRENTS</div>{challenger_html}
<div class="section">40 VALEURS · COHORTE T0</div><table>{rows}</table>
<div class="footer">Portefeuille géré {vg:,.2f} € · Jumeau {vt:,.2f} € · construction {now}</div></div></body></html>"""
(APP/"index.html").write_text(page,encoding="utf-8")
(BASE/"index.html").write_text(page,encoding="utf-8")
print("✅ TABLEAU DE BORD MICRO CAPS V3 PUBLIE")
print("Séance :",date,"| lignes :",len(P),"| anomalies :",len(bad))

# publication challengers mobile

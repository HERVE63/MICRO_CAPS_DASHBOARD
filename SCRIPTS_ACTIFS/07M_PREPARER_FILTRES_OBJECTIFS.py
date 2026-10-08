from pathlib import Path
import pandas as pd
B=Path(__file__).resolve().parent.parent
D=B/'DONNEES'
SRC=D/'UNIVERS_INVESTISSABLE_MICRO_CAPS.csv'
MARCHE=D/'PRESELECTION_VARIABLES_MARCHE.csv'
OUT=D/'UNIVERS_PRET_FILTRES_OBJECTIFS.csv'
AUD=D/'AUDIT_PREPARATION_FILTRES.csv'
def executer():
    df=pd.read_csv(SRC)
    m=pd.read_csv(MARCHE)
    if df['Ticker'].duplicated().any() or m['Ticker'].duplicated().any(): raise RuntimeError('Ticker duplique')
    champs=['Momentum_3m_pct','Momentum_6m_pct','MM200','Au_dessus_MM200','Volume_monetaire_median_63s_local','Statut_donnees_marche']
    df=df.drop(columns=[v for v in champs if v in df.columns]).merge(m[['Ticker']+champs],on='Ticker',how='left',validate='one_to_one')
    if df.empty: raise RuntimeError('Univers nettoye vide')
    req=['Momentum_3m_pct','Momentum_6m_pct','MM200','Au_dessus_MM200','Volume_monetaire_median_63s_local','Statut_donnees_marche']
    miss=[c for c in req if c not in df.columns]
    if miss: raise RuntimeError('Variables absentes: '+', '.join(miss))
    ok=df['Statut_donnees_marche'].astype(str).str.upper().eq('OK')
    df['Admissible_filtre_marche']=ok.map({True:'OUI',False:'NON_DONNEE_MANQUANTE'})
    if 'Etat_registre' in df:
        incertain=df['Etat_registre'].fillna('').astype(str).eq('NOUVEAU_A_QUALIFIER')
        df.loc[incertain,'Admissible_filtre_marche']='NON_IDENTITE_A_QUALIFIER'
    df.to_csv(OUT,index=False)
    pd.DataFrame([{'Nb_univers_nettoye':len(df),'Nb_marche_OK':int(ok.sum()),'Nb_marche_manquantes':int((~ok).sum()),'Seuils_nouveaux_appliques':'NON'}]).to_csv(AUD,index=False)
    print(len(df),int(ok.sum()),int((~ok).sum()))
    return df
if __name__=='__main__': executer()

# production

"""SSI V1.0 — sept notes sur preuves vérifiées, sans imputation."""
from pathlib import Path
from datetime import datetime, timezone
import sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from preuves_ssi import MAX, registre, valider_dossier, bilan_blocs_documentes, verifier_identite_sce
D=Path(__file__).resolve().parents[1]/'DONNEES'
SRC=D/'DOSSIERS_SSI_A_QUALIFIER.csv';OUT=D/'RESULTATS_SSI.csv';AUD=D/'AUDIT_SSI.csv'
def executer():
    if not SRC.exists():raise RuntimeError('Dossiers SSI absents')
    df=pd.read_csv(SRC,dtype=str,keep_default_na=False)
    if df.Ticker.duplicated().any():raise RuntimeError('Tickers SSI dupliqués')
    if df.empty:
        df['Motif_decision_SSI']=pd.Series(dtype=str)
        df.to_csv(OUT,index=False)
        pd.DataFrame([{'Date_validation_UTC':datetime.now(timezone.utc).isoformat(),'Dossiers':0,'Admis':0,'Refuses':0,'Refuses_plafond_sans_score_total':0,'Elimines':0,'Preuves_incompletes':0}]).to_csv(AUD,index=False)
        print('SSI: aucun nouveau dossier qualifiable')
        return df
    if not {'Decision_eliminatoire','Motif_eliminatoire',*[p+b for b in MAX for p in ['Note_','Preuve_']]}.issubset(df.columns):
        raise RuntimeError('Schéma dossier SSI incomplet')
    limite=datetime.now(timezone.utc);preuves=registre(D.parent,limite)
    scores=[];statuts=[];motifs=[];partiels=[]
    for _,r in df.iterrows():
        partiels.append(bilan_blocs_documentes(r,preuves,D.parent,limite))
        # 07Q isole une collision CIK. 07R ne doit jamais transformer cette
        # quarantaine en admission, meme si d'anciennes notes et preuves sont
        # reintroduites par erreur ou si leur verification individuelle reussit.
        # Le controle est independant de la qualite des autres dossiers.
        if str(r.get('Conflit_identite_CIK','NON')).strip().upper()=='OUI':
            scores.append('MANQUANTE')
            statuts.append('EN_ATTENTE_DATA_IDENTITE_CIK')
            motifs.append('Collision CIK non levee par verification independante : notation et admission interdites')
            continue
        notes,erreurs=valider_dossier(r,preuves,D.parent,limite)
        # Une exclusion elle aussi doit avoir une référence vérifiée avant publication.
        if r.Decision_eliminatoire=='OUI':
            from preuves_ssi import verifier
            z=preuves[preuves.ID_preuve.eq(r.Motif_eliminatoire)]
            if len(z)==1 and not verifier(z.iloc[0],r.Ticker,'EXCLUSIONS',D.parent,limite):
                scores.append('MANQUANTE');statuts.append('ELIMINE');motifs.append(r.Motif_eliminatoire);continue
        if erreurs and r.get('SCE_valide','NON')=='OUI' and r.Decision_eliminatoire=='NON' and partiels[-1]['Plafond_SSI_si_blocs_restants_maximaux']<65:
            from preuves_ssi import verifier
            ids=str(r.Motif_eliminatoire).split('|');ex=preuves[preuves.ID_preuve.isin(ids)]
            cik=str(r.get('CIK',''))
            if not verifier_identite_sce(r,preuves,D.parent,limite) and cik and len(ex)==len(ids) and len(set(ids))==len(ids) and all(not verifier(p,r.Ticker,'EXCLUSIONS',D.parent,limite) and p.Identifiant_emetteur=='CIK:'+cik for _,p in ex.iterrows()):
                scores.append('MANQUANTE');statuts.append('REFUSE_SSI_PLAFOND_VERIFIE')
                motifs.append('Même au maximum des blocs non documentés, plafond '+str(partiels[-1]['Plafond_SSI_si_blocs_restants_maximaux'])+' < 65 ; aucune note manquante imputée. Nouvelle preuve/révision impose recalcul.')
                continue
        if erreurs:
            scores.append('MANQUANTE');statuts.append('A_COMPLETER_PREUVES_SSI');motifs.append(' | '.join(erreurs))
        else:
            total=sum(notes);scores.append(str(total));statuts.append('ADMIS_SSI' if total>=65 else 'REFUSE_SSI')
            motifs.append('Sept blocs et exclusions vérifiés dans le registre de preuves')
    df['SSI']=scores;df['Statut_SSI']=statuts;df['Motif_decision_SSI']=motifs
    for champ in partiels[0]:df[champ]=[p[champ] for p in partiels]
    tmp=OUT.with_suffix('.tmp');df.to_csv(tmp,index=False);tmp.replace(OUT)
    pd.DataFrame([{'Date_validation_UTC':limite.isoformat(),'Dossiers':len(df),
        'Admis':statuts.count('ADMIS_SSI'),'Refuses':statuts.count('REFUSE_SSI'),
        'Refuses_plafond_sans_score_total':statuts.count('REFUSE_SSI_PLAFOND_VERIFIE'),'Elimines':statuts.count('ELIMINE'),'Preuves_incompletes':statuts.count('A_COMPLETER_PREUVES_SSI')}]).to_csv(AUD,index=False)
    print('SSI:',pd.Series(statuts).value_counts().to_dict());return df
if __name__=='__main__':executer()

"""SSI V1.0 — sept notes sur preuves vérifiées, sans imputation."""
from pathlib import Path
from datetime import datetime, timezone
import sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from preuves_ssi import MAX, registre, valider_dossier
D=Path(__file__).resolve().parents[1]/'DONNEES'
SRC=D/'DOSSIERS_SSI_A_QUALIFIER.csv';OUT=D/'RESULTATS_SSI.csv';AUD=D/'AUDIT_SSI.csv'
def executer():
    if not SRC.exists():raise RuntimeError('Dossiers SSI absents')
    df=pd.read_csv(SRC,dtype=str,keep_default_na=False)
    if df.empty or df.Ticker.duplicated().any():raise RuntimeError('Dossiers SSI vides/tickers dupliqués')
    if not {'Decision_eliminatoire','Motif_eliminatoire',*[p+b for b in MAX for p in ['Note_','Preuve_']]}.issubset(df.columns):
        raise RuntimeError('Schéma dossier SSI incomplet')
    limite=datetime.now(timezone.utc);preuves=registre(D.parent,limite)
    scores=[];statuts=[];motifs=[]
    for _,r in df.iterrows():
        notes,erreurs=valider_dossier(r,preuves,D.parent,limite)
        # Une exclusion elle aussi doit avoir une référence vérifiée avant publication.
        if r.Decision_eliminatoire=='OUI':
            from preuves_ssi import verifier
            z=preuves[preuves.ID_preuve.eq(r.Motif_eliminatoire)]
            if len(z)==1 and not verifier(z.iloc[0],r.Ticker,'EXCLUSIONS',D.parent,limite):
                scores.append('MANQUANTE');statuts.append('ELIMINE');motifs.append(r.Motif_eliminatoire);continue
        if erreurs:
            scores.append('MANQUANTE');statuts.append('A_COMPLETER_PREUVES_SSI');motifs.append(' | '.join(erreurs))
        else:
            total=sum(notes);scores.append(str(total));statuts.append('ADMIS_SSI' if total>=65 else 'REFUSE_SSI')
            motifs.append('Sept blocs et exclusions vérifiés dans le registre de preuves')
    df['SSI']=scores;df['Statut_SSI']=statuts;df['Motif_decision_SSI']=motifs
    tmp=OUT.with_suffix('.tmp');df.to_csv(tmp,index=False);tmp.replace(OUT)
    pd.DataFrame([{'Date_validation_UTC':limite.isoformat(),'Dossiers':len(df),
        'Admis':statuts.count('ADMIS_SSI'),'Refuses':statuts.count('REFUSE_SSI'),
        'Elimines':statuts.count('ELIMINE'),'Preuves_incompletes':statuts.count('A_COMPLETER_PREUVES_SSI')}]).to_csv(AUD,index=False)
    print('SSI:',pd.Series(statuts).value_counts().to_dict());return df
if __name__=='__main__':executer()

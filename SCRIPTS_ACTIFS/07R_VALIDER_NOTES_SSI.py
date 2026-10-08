"""SSI V1.0 — validation de sept notes documentées, sans notation inventée."""
from pathlib import Path
import pandas as pd

D = Path(__file__).resolve().parent.parent / "DONNEES"
SRC = D / "DOSSIERS_SSI_A_QUALIFIER.csv"
OUT = D / "RESULTATS_SSI.csv"
AUD = D / "AUDIT_SSI.csv"
MAX = {"B1":20,"B2":15,"B3":15,"B4":20,"B5":10,"B6":10,"B7":10}
VALIDES = {"NON","OUI","A_VERIFIER"}

def executer():
    if not SRC.exists():
        raise RuntimeError("Dossiers SSI absents")
    df = pd.read_csv(SRC, dtype=str, keep_default_na=False)
    if df.empty:
        raise RuntimeError("Dossiers SSI vides")
    if df["Ticker"].duplicated().any():
        raise RuntimeError("Doublons ticker SSI : verifier identite")
    for b in MAX:
        for col in ("Note_"+b, "Preuve_"+b):
            if col not in df.columns:
                raise RuntimeError("Champ SSI manquant : "+col)
    if "Decision_eliminatoire" not in df or "Motif_eliminatoire" not in df:
        raise RuntimeError("Controle eliminatoire absent")
    scores=[]; statuts=[]; motifs=[]
    for _,r in df.iterrows():
        elim=str(r["Decision_eliminatoire"]).strip().upper()
        if elim not in VALIDES:
            raise RuntimeError("Decision eliminatoire invalide : "+str(r["Ticker"]))
        if elim=="OUI":
            if str(r["Motif_eliminatoire"]).strip().upper() in ("","MANQUANTE"):
                raise RuntimeError("Elimination sans motif : "+str(r["Ticker"]))
            scores.append("MANQUANTE");statuts.append("ELIMINE");motifs.append(r["Motif_eliminatoire"]);continue
        notes=[]; erreurs=[]
        for b,maximum in MAX.items():
            val=str(r["Note_"+b]).strip()
            preuve=str(r["Preuve_"+b]).strip()
            if val.upper() in ("","MANQUANTE") or preuve.upper() in ("","MANQUANTE","A_COMPLETER","NON_VERIFIE","N/A"):
                erreurs.append(b+": preuve ou note manquante");continue
            try:
                note=float(val)
                if not note.is_integer() or not 0<=note<=maximum:
                    raise ValueError()
                notes.append(int(note))
            except ValueError:
                raise RuntimeError("Note SSI hors bareme "+b+" : "+str(r["Ticker"]))
        if elim=="NON" and str(r["Motif_eliminatoire"]).strip().upper() in ("","MANQUANTE"):
            erreurs.append("preuve de verification des exclusions manquante")
        if elim=="A_VERIFIER":
            erreurs.append("filtre eliminatoire non verifie")
        if erreurs:
            scores.append("MANQUANTE");statuts.append("A_COMPLETER_PREUVES_SSI");motifs.append(" | ".join(erreurs))
        else:
            total=sum(notes)
            scores.append(str(total))
            statuts.append("ADMIS_SSI" if total>=65 else "REFUSE_SSI")
            motifs.append("Barème V1.0 vérifié")
    df["SSI"]=scores;df["Statut_SSI"]=statuts;df["Motif_decision_SSI"]=motifs
    df.to_csv(OUT,index=False)
    pd.DataFrame([{"Dossiers":len(df),"Admis":sum(s=="ADMIS_SSI" for s in statuts),
      "Refuses":sum(s=="REFUSE_SSI" for s in statuts),
      "Elimines":sum(s=="ELIMINE" for s in statuts),
      "Preuves_incompletes":sum(s=="A_COMPLETER_PREUVES_SSI" for s in statuts)}]).to_csv(AUD,index=False)
    print("SSI:",pd.Series(statuts).value_counts().to_dict())
    return df

if __name__=="__main__":
    executer()

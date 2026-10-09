# -*- coding: utf-8 -*-
"""Exécution mensuelle MICRO CAPS.
Fenêtre normale : dernière revue du mardi du mois.
Le mardi hebdomadaire prépare ; ce module seul peut journaliser une rotation normale.
Frais validés : 2,5 % vente et 2,5 % achat.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import importlib.util, os
import pandas as pd

BASE=Path(__file__).resolve().parent.parent
SRC=BASE/"SCRIPTS_ACTIFS"
JOURNAL=BASE/"DONNEES/JOURNAL_ARBITRAGES_GERE.csv"
DUELS=BASE/"DONNEES/DUELS_PROCHAIN_EURO.csv"
REVUE=BASE/"DONNEES/REVUE_HEBDOMADAIRE_MCPA_IPS.csv"
PARAMS=BASE/"CONFIG/PARAMETRES_ARBITRAGE_MICRO_CAPS.csv"

def charger(nom):
    p=SRC/nom; s=importlib.util.spec_from_file_location(nom.replace(".py",""),p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def dernier_mardi(d):
    return d.weekday()==1 and (d.replace(day=d.day)+__import__("datetime").timedelta(days=7)).month!=d.month

def taux():
    p=pd.read_csv(PARAMS).set_index("Parametre")
    return float(p.loc["Frais_achat","Valeur"])/100,float(p.loc["Frais_vente","Valeur"])/100

def executer(dry_run=False):
    charger("07AC_CONTROLER_T0.py").executer()
    maintenant=datetime.now(ZoneInfo("Europe/Paris"))
    force=os.getenv("MICRO_CAPS_FORCE_MENSUEL","0")=="1"
    if force and not (dry_run or os.getenv("MICRO_CAPS_DRY_RUN","0")=="1"):
        raise RuntimeError("Forçage hors fenêtre interdit sans exception grave documentée")
    if not force and not dernier_mardi(maintenant.date()):
        print("Hors fenêtre mensuelle : aucune opération.")
        return pd.DataFrame()

    # Recalcule les contrôles/duels sur la revue courante.
    duels=charger("09B_DUEL_PROCHAIN_EURO.py").executer()
    if duels.empty:
        print("Aucune sortie VENDRE : aucun arbitrage.")
        return pd.DataFrame()

    revue=pd.read_csv(REVUE)
    journal=pd.read_csv(JOURNAL)
    replay=charger("05C_REPLAY_PORTEFEUILLE_GERE.py").executer()
    positions=replay["positions"]
    if float(replay["cash"])>0.01:
        raise RuntimeError("Cash antérieur non alloué : exécution mensuelle bloquée.")

    px=charger("03A_MOTEUR_CLOTURES_V3.py")
    fxm=charger("03B_MOTEUR_FX_V3.py")
    fx=fxm.tous_les_fx(datetime.now(ZoneInfo("UTC")))
    ta,tv=taux()
    date_exec=maintenant.date().isoformat()
    existants=set(journal["ID_operation"].astype(str)) if len(journal) else set()
    lignes=[]; seq=1

    def pos_active(idp):
        z=positions[(positions["ID_position"].astype(str)==str(idp)) & (positions["Statut"].astype(str).str.upper()=="ACTIF")]
        if len(z)!=1: raise RuntimeError(f"Position source active introuvable/non unique : {idp}")
        return z.iloc[0]

    def prix_fx(ticker,devise):
        p=px.derniere_cloture_validee(str(ticker),datetime.now(ZoneInfo("UTC")))
        if devise not in fx: raise RuntimeError(f"FX absent : {devise}")
        return float(p["cours_cloture"]),float(fx[devise]["fx_vers_eur"])

    def base_row(opid,typ):
        return {c:"" for c in journal.columns} | {
            "ID_operation":opid,"Date_decision":date_exec,"Date_execution":date_exec,
            "Sequence_execution":seq,"Type_operation":typ,"Statut_operation":"EXECUTEE"
        }

    for source,grp in duels.groupby("ID_position_source",sort=False):
        if (grp["Statut_duel"]=="CONSERVER").all():
            continue
        if not (grp["Statut_duel"]=="ALLOCATION_DETERMINEE").all():
            raise RuntimeError(f"Duel non exécutable pour {source}.")
        ps=pos_active(source)
        cours_s,fx_s=prix_fx(ps["Ticker"],str(ps["Devise"]).upper())
        q=float(ps["Quantite"]); brut=q*cours_s*fx_s; frais_s=brut*tv; net=brut-frais_s
        opid=f"MC_{date_exec.replace('-','')}_{str(source)}_SORTIE"
        if opid in existants: raise RuntimeError(f"Opération déjà journalisée : {opid}")
        row=base_row(opid,"SORTIE")
        row.update({"ID_ligne_sortante":source,"Societe_sortante":ps["Societe"],"Ticker_sortant":ps["Ticker"],
          "Devise_sortante":ps["Devise"],"Cours_execution_sortie":cours_s,"FX_sortie_vers_EUR":fx_s,
          "Frais_sortie_EUR":frais_s,"Quantite_vendue":q,"Capital_realise_EUR":net,
          "Motif":"Arbitrage mensuel après revues hebdomadaires","Decision_comite":"VENDRE"})
        lignes.append(row); seq+=1

        for k,(_,d) in enumerate(grp.iterrows(),1):
            montant=net*float(d["Part_allocation"])
            iddst=str(d["ID_position_destination"])
            typdst=str(d["Type_destination"]).upper()
            if typdst=="TITULAIRE":
                pdst=pos_active(iddst); soc=pdst["Societe"]; ticker=pdst["Ticker"]; devise=str(pdst["Devise"]).upper()
                typop="RENFORCEMENT"
            elif typdst=="CHALLENGER":
                z=revue[revue["ID_position"].astype(str)==iddst]
                if len(z)!=1: raise RuntimeError(f"Challenger introuvable/non unique : {iddst}")
                z=z.iloc[0]; soc=z["Societe"]; ticker=z["Ticker"]; devise=str(z["Devise"]).upper()
                typop="ENTREE"
            else:
                raise RuntimeError(f"Destination non exécutable : {typdst}")
            cours_e,fx_e=prix_fx(ticker,devise)
            frais_e=montant*ta/(1+ta)
            opid2=f"MC_{date_exec.replace('-','')}_{str(source)}_{k}"
            if opid2 in existants: raise RuntimeError(f"Opération déjà journalisée : {opid2}")
            row=base_row(opid2,typop); row["Sequence_execution"]=seq
            row.update({"ID_ligne_entrante":iddst if typop=="RENFORCEMENT" else "",
              "Societe_entrante":soc,"Ticker_entrant":ticker,"Devise_entrante":devise,
              "Montant_EUR":montant,"Cours_execution_entree":cours_e,"FX_entree_vers_EUR":fx_e,
              "Frais_entree_EUR":frais_e,"Quantite_achetee":(montant-frais_e)/(cours_e*fx_e),
              "Motif":"Allocation du capital libéré après frais","Decision_comite":typop})
            lignes.append(row); seq+=1

    ajout=pd.DataFrame(lignes,columns=journal.columns)
    if ajout.empty: return ajout
    if dry_run or os.getenv("MICRO_CAPS_DRY_RUN","0")=="1":
        print(f"DRY RUN : {len(ajout)} opération(s), journal inchangé.")
        return ajout
    nouveau=pd.concat([journal,ajout],ignore_index=True)
    # Vérifier le journal candidat AVANT publication : un échec n'altère jamais le journal.
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as temp:
        candidate=Path(temp)/"JOURNAL.csv";nouveau.to_csv(candidate,index=False)
        recep=charger("05C_REPLAY_PORTEFEUILLE_GERE.py")
        recep.JOURNAL=candidate;recep.OUTPUT=Path(temp)/"REPLAY.csv"
        recep.executer()
    tmp=JOURNAL.with_suffix(".tmp");nouveau.to_csv(tmp,index=False);tmp.replace(JOURNAL)
    print(f"Arbitrage mensuel journalisé : {len(ajout)} opération(s).")
    return ajout

if __name__=="__main__":
    executer()

# réception syntaxique

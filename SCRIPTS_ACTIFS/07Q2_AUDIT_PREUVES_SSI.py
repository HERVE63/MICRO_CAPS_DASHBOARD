"""Plan SSI de collecte documentaire : 7 blocs, identite et exclusions.
Les observations fournisseur ne sont jamais des preuves primaires certifiees.
Le pays de cotation ne prouve pas le domicile juridique de l'emetteur.
"""
from pathlib import Path
import hashlib
import re
import json
import csv
from datetime import datetime, timezone
import pandas as pd
from preuves_ssi import identifiant_reglementaire_formel_valide
from preuves_ssi import identifiant_dossier

D=Path(__file__).resolve().parent.parent/"DONNEES"
SRC=D/"DOSSIERS_SSI_A_QUALIFIER.csv"
OUT=D/"PLAN_COLLECTE_PREUVES_SSI.csv"
AUD=D/"AUDIT_COLLECTE_PREUVES_SSI.csv"
ANOMALIES=D/"ANOMALIES_CAPTURES_SSI.csv"
ARCHIVE_IDENTITE=D/"IDENTITE_COTATIONS_MULTIPLES.csv"
CHAMPS={
 "B1":("B1_bilan_cash","B1_bilan_dette"),
 "B2":("B2_rentabilite_EBITDA","B2_rentabilite_FCF"),
 "B3":("B3_croissance_CA","B3_marge_brute"),
 "B4":("B4_skin_in_game",),
 "B5":("B5_actions_en_circulation",),
 "B6":("B6_source","B6_date"),
 "B7":("B7_volume_local",),
}
COMPLEMENTS={
 "B1":"Echeances de dette, besoins de financement et runway",
 "B2":"Historique EBITDA/EBIT, resultat, FCF et inflexion",
 "B3":"Historique CA, commandes, recurrence, clients",
 "B4":"Actions detenues directement, achats/ventes, options et gouvernance",
 "B5":"Historique emissions, dilution, options, remuneration, auditeur",
 "B6":"Comptes reglementes audites, dates et coherence",
 "B7":"Place de cotation, turnover et spread si disponible",
}
COLONNES=["Ticker","Societe","Bloc_SSI","Variables_absentes","Preuve_validee",
          "Note_presente","Preuves_complementaires_requises","Source_actuelle",
          "Date_source_actuelle","Statut","Identifiant_emetteur_source",
          "Pays_cotation_declare","Pays_emetteur_verifie",
          "ISIN_piste_non_certifiee","Societe_archive_ISIN","Statut_piste_ISIN",
          "Provenance_archive_ISIN","SHA256_archive_ISIN","Date_archive_ISIN",
          "Captures_primaires_SHA256_OK_pistes","URLs_primaires_distinctes_pistes",
          "Identifiants_captures_non_certifies","Captures_publication_inconnue",
          "Statut_captures_non_certifiees",
          "Captures_sources_URL_pistes","Captures_SHA256_pistes",
          "Captures_dates_publication_pistes","Captures_dates_collecte_UTC_pistes"]
def manquant(v):
 return pd.isna(v) or str(v).strip().upper() in ("","MANQUANTE","NAN","NONE","N/A")


def isin_checksum_valide(v):
 """Controle formel ISO 6166 (Luhn), JAMAIS une preuve d'identite."""
 if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]",v):return False
 chiffres="".join(str(ord(c)-55) if "A"<=c<="Z" else c for c in v)
 total=0
 for position,c in enumerate(reversed(chiffres)):
  n=int(c)
  if position%2:
   n*=2
   n=n//10+n%10
  total+=n
 return total%10==0

def lire_pistes_archive():
 """Reutilisation strictement indicative de 07D ; aucune promotion en preuve SSI."""
 if not ARCHIVE_IDENTITE.exists():return {}, "MANQUANTE"
 brut=ARCHIVE_IDENTITE.read_bytes()
 empreinte=hashlib.sha256(brut).hexdigest()
 d=pd.read_csv(ARCHIVE_IDENTITE,dtype=str,keep_default_na=False)
 requis={"Ticker","Societe","ISIN"}
 if not requis.issubset(d.columns):
  raise RuntimeError("Schema archive ISIN historique incomplet : "+", ".join(sorted(requis-set(d.columns))))
 if d["Ticker"].astype(str).str.strip().eq("").any():
  raise RuntimeError("Ticker vide dans archive ISIN historique")
 pistes={}
 for ticker,g in d.groupby("Ticker",sort=False):
  if len(g)!=1:
   pistes[ticker]=("MANQUANTE","MANQUANTE","TICKER_AMBIGU_ARCHIVE")
   continue
  r=g.iloc[0]
  isin=str(r["ISIN"]).strip().upper()
  statut=("PISTE_ISIN_CHECKSUM_OK_NON_CERTIFIEE" if isin_checksum_valide(isin)
          else "ISIN_ABSENT_ARCHIVE" if isin in {"","-","MANQUANTE"}
          else "ISIN_INVALIDE_ARCHIVE")
  pistes[ticker]=(isin if isin_checksum_valide(isin) else "MANQUANTE",
                  str(r["Societe"]).strip(),statut)
 return pistes,empreinte


def indexer_captures_primaires():
 """Indexer les captures 07AA, en publiant les causes de chaque rejet.

 Le diagnostic est une sortie de contrôle, pas un registre de preuves SCE.
 Le contrat de retour historique (captures, invalides, bloquees) est conserve.
 Un document invalide ne bloque pas les autres dossiers.
 """
 racine=D.parent.resolve()
 archives=racine/"AUDITS"/"SOURCES_OFFICIELLES"
 captures={}
 invalides=0
 bloquees=0
 anomalies=[]
 colonnes=["Archive","ID_document","Ticker","Source_URL","Statut_original","Code_anomalie","Motif_07AA"]
 def tracer(audit,ligne,code,motif=""):
  anomalies.append({"Archive":str(audit.relative_to(racine)),
                   "ID_document":str(ligne.get("ID_document","")),
                   "Ticker":str(ligne.get("Ticker","")),
                   "Source_URL":str(ligne.get("Source_URL","")),
                   "Statut_original":str(ligne.get("Statut","")),
                   "Code_anomalie":code,
                   "Motif_07AA":str(motif)[:500]})
 def refuser(code):
  raise ValueError(code)
 for audit in sorted(archives.glob("*/AUDIT_DOCUMENTS.csv")):
  dossier=audit.parent.resolve()
  try:
   manifeste=json.loads((dossier/"MANIFESTE.json").read_text(encoding="utf-8"))
   if "fichiers" not in manifeste:
    refuser("MANIFESTE_HISTORIQUE_SANS_FICHIERS")
   fichiers=manifeste["fichiers"]
   if not isinstance(fichiers,dict) or fichiers.get("AUDIT_DOCUMENTS.csv")!=hashlib.sha256(audit.read_bytes()).hexdigest():
    refuser("SHA256_AUDIT_OU_MANIFESTE_DIVERGENT")
   with audit.open(encoding="utf-8-sig",newline="") as f:
    lignes=list(csv.DictReader(f))
  except (OSError,ValueError,KeyError,UnicodeError,TypeError,json.JSONDecodeError) as erreur:
   invalides+=1
   code=("MANIFESTE_HISTORIQUE_SANS_FICHIERS" if str(erreur)=="MANIFESTE_HISTORIQUE_SANS_FICHIERS" else "MANIFESTE_OU_AUDIT_INVALIDE")
   tracer(audit,{},code,type(erreur).__name__)
   continue
  for ligne in lignes:
   if ligne.get("Statut")!="DOCUMENT_COLLECTE_A_VERIFIER":
    if ligne.get("Statut")=="BLOQUE_SOURCE":
     bloquees+=1
     tracer(audit,ligne,"SOURCE_BLOQUEE_07AA",ligne.get("Motif",""))
    continue
   try:
    ticker=ligne["Ticker"].strip()
    ident=ligne["Identifiant_emetteur"].strip()
    url=ligne["Source_URL"].strip()
    sha=ligne["SHA256"].strip()
    date_capture=pd.to_datetime(ligne["Date_collecte_UTC"],utc=True,errors="coerce")
    date_pub=pd.to_datetime(ligne.get("Date_publication",""),utc=True,errors="coerce")
    if not ticker:refuser("TICKER_ABSENT")
    if not identifiant_reglementaire_formel_valide(ident):refuser("IDENTIFIANT_REGLEMENTAIRE_INVALIDE")
    if not url.startswith("https://"):refuser("URL_NON_HTTPS")
    if ligne.get("Type_source") not in {"PUBLICATION_EMETTEUR","DEPOT_REGLEMENTAIRE","DONNEE_MARCHE_IDENTITE"}:
     refuser("TYPE_SOURCE_NON_PRIMAIRE")
    if pd.isna(date_capture):refuser("DATE_COLLECTE_INVALIDE")
    if date_capture>pd.Timestamp(datetime.now(timezone.utc)):refuser("DATE_COLLECTE_FUTURE")
    if ligne.get("Date_publication","").strip() and pd.isna(date_pub):refuser("DATE_PUBLICATION_INVALIDE")
    if not pd.isna(date_pub) and date_pub>date_capture:refuser("DATE_PUBLICATION_APRES_COLLECTE")
    if not re.fullmatch(r"[0-9a-f]{64}",sha):refuser("SHA256_MALFORME")
    chemin=(racine/ligne["Fichier_brut"]).resolve()
    if chemin.parent!=dossier or chemin.name not in {sha+".bin",sha+".pdf"}:
     refuser("CHEMIN_HORS_ARCHIVE")
    if fichiers.get(chemin.name)!=sha:refuser("SHA256_MANIFESTE_BRUT_DIVERGENT")
    octets=chemin.read_bytes()
    if hashlib.sha256(octets).hexdigest()!=sha:refuser("SHA256_BRUT_DIVERGENT")
    if not ligne.get("Date_publication","").strip() and ligne.get("Statut_date_publication","").startswith("DATE_"):
     refuser("STATUT_DATE_PUBLICATION_INCOHERENT")
    # Concordance purement textuelle dans les OCTETS archives et hashes.
    # Ni le libelle de l'audit ni le nom du fichier ne prouvent l'identite.
    type_contenu=str(ligne.get("Type_contenu","")).lower()
    isin_observe="NON_ANALYSE_BINAIRE"
    symbole_observe="NON_APPLICABLE"
    if type_contenu.startswith(("text/html","text/plain")):
     texte=octets.decode("utf-8",errors="replace")
     if ident.startswith("ISIN:"):
      isin_observe=("OUI" if re.search(r"(?<![A-Z0-9])"+re.escape(ident[5:])+r"(?![A-Z0-9])",texte,re.I) else "NON")
     else:
      isin_observe="NON_APPLICABLE_IDENTIFIANT_NON_ISIN"
     if ligne.get("Type_source")=="DONNEE_MARCHE_IDENTITE":
      symbole=ticker.split(".")[0]
      symbole_observe=("OUI" if re.search(r"\bSymbol:\s*"+re.escape(symbole)+r"\\b",texte,re.I) else "NON")
    captures.setdefault(ticker,[]).append((ident,url,sha,pd.isna(date_pub),
                                           str(ligne.get("Date_publication","")).strip() or "INCONNUE",
                                           str(ligne["Date_collecte_UTC"]).strip(),
                                           str(ligne.get("ID_document","")),
                                           str(chemin.relative_to(racine)),
                                           str(ligne.get("Type_source","")),
                                           type_contenu,isin_observe,symbole_observe))
   except (OSError,ValueError,KeyError,TypeError) as erreur:
    invalides+=1
    code=(str(erreur) if isinstance(erreur,ValueError) and str(erreur) in {
      "TICKER_ABSENT","IDENTIFIANT_REGLEMENTAIRE_INVALIDE","URL_NON_HTTPS",
      "TYPE_SOURCE_NON_PRIMAIRE","DATE_COLLECTE_INVALIDE","DATE_COLLECTE_FUTURE",
      "DATE_PUBLICATION_INVALIDE","DATE_PUBLICATION_APRES_COLLECTE",
      "SHA256_MALFORME","CHEMIN_HORS_ARCHIVE","SHA256_MANIFESTE_BRUT_DIVERGENT",
      "SHA256_BRUT_DIVERGENT","STATUT_DATE_PUBLICATION_INCOHERENT"}
      else "ERREUR_LECTURE_OU_SCHEMA")
    tracer(audit,ligne,code,type(erreur).__name__ if code=="ERREUR_LECTURE_OU_SCHEMA" else "")
 # Respecter le repertoire D injecte par les tests hors reseau : jamais
 # ecrire dans le depot quand un test utilise une cohorte temporaire.
 sortie_anomalies=D/"ANOMALIES_CAPTURES_SSI.csv"
 sortie_anomalies.parent.mkdir(parents=True,exist_ok=True)
 temporaire=sortie_anomalies.with_suffix(".tmp")
 with temporaire.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=colonnes)
  w.writeheader()
  w.writerows(anomalies)
 temporaire.replace(sortie_anomalies)
 assert invalides==sum(a["Code_anomalie"]!="SOURCE_BLOQUEE_07AA" for a in anomalies)
 assert bloquees==sum(a["Code_anomalie"]=="SOURCE_BLOQUEE_07AA" for a in anomalies)
 return captures,invalides,bloquees

def publier_concordances_brutes(captures):
 """Table de relecture des contenus HTML archives, sans certification SCE.

 La presence textuelle d'un ISIN ou symbole est un INDICE : la date de
 publication, l'independance editoriale et la cotation doivent etre revues.
 Les doublons exacts (URL, SHA256) ne comptent jamais deux fois.
 """
 destination=D/"CONCORDANCES_IDENTITE_BRUTS_NON_CERTIFIEES.csv"
 colonnes=["Ticker","ID_document","Identifiant_declare_non_certifie",
  "Type_source","Source_URL","Archive_brute","SHA256_brut_verifie",
  "Date_publication_declaree","Date_collecte_UTC","Type_contenu",
  "ISIN_observe_dans_brut","Symbole_marche_observe_dans_brut",
  "Identite_SCE_certifiee","Note_SSI","Statut"]
 lignes=[]
 deja=set()
 for ticker,documents in sorted(captures.items()):
  for d in documents:
   cle=(ticker,d[1],d[2])
   if cle in deja:continue
   deja.add(cle)
   lignes.append(dict(Ticker=ticker,ID_document=d[6],
    Identifiant_declare_non_certifie=d[0],Type_source=d[8],
    Source_URL=d[1],Archive_brute=d[7],SHA256_brut_verifie=d[2],
    Date_publication_declaree=d[4],Date_collecte_UTC=d[5],
    Type_contenu=d[9],ISIN_observe_dans_brut=d[10],
    Symbole_marche_observe_dans_brut=d[11],
    Identite_SCE_certifiee="NON",Note_SSI="MANQUANTE",
    Statut="INDICE_TEXTUEL_NON_CERTIFIE" if d[10]=="OUI" else "EN_ATTENTE_RELECTURE_PRIMAIRE"))
 sortie=pd.DataFrame(lignes,columns=colonnes).sort_values(
  ["Ticker","Source_URL","SHA256_brut_verifie"],kind="stable")
 tmp=destination.with_suffix(".tmp")
 sortie.to_csv(tmp,index=False)
 tmp.replace(destination)
 return sortie


def publier_file_certification(df, captures, pistes):
 """File de revue documentaire, jamais une certification SCE ou une note SSI.

 Reutilise UNIQUEMENT les captures deja controlees par indexer_captures_primaires()
 et les ISIN indicatifs de 07D. Deux domaines ne prouvent pas deux editeurs
 independants : la revue des documents et de leurs dates reste obligatoire.
 """
 from urllib.parse import urlsplit
 destination=D/"FILE_CERTIFICATION_IDENTITES_SSI.csv"
 colonnes=["Ticker","Societe","Priorite_revue_documentaire",
  "Identifiant_dossier_source","Identifiant_piste_unique_non_certifie",
  "ISIN_archive_piste_non_certifiee","Captures_SHA256_OK_pistes",
  "URLs_distinctes_pistes","SHA256_distincts_pistes",
  "Domaines_hebergement_distincts_pistes","Publications_date_inconnue",
  "Publications_date_connue_a_verifier","URLs_pistes","SHA256_pistes",
  "Dates_publication_pistes","Statut_certification","Qualification_economique"]
 lignes=[]
 for _,r in df.iterrows():
  ticker=str(r["Ticker"]).strip()
  brutes=captures.get(ticker,[])
  identifiants={x[0] for x in brutes}
  urls={x[1] for x in brutes}
  empreintes={x[2] for x in brutes}
  domaines={urlsplit(u).hostname for u in urls if urlsplit(u).hostname}
  inconnu=sum(bool(x[3]) for x in brutes)
  isin_piste,_,statut_archive=pistes.get(ticker,("MANQUANTE","MANQUANTE","AUCUNE_PISTE_ARCHIVE"))
  if len(identifiants)>1:
   priorite="P0_CONFLIT_IDENTIFIANTS_A_EXAMINER"
  elif len(urls)>=2 and len(empreintes)>=2 and len(domaines)>=2:
   priorite="P1_PISTES_MULTIDOMAINES_A_CERTIFIER"
  elif brutes:
   priorite="P2_PISTES_PRIMAIRES_A_COMPLETER"
  elif statut_archive=="PISTE_ISIN_CHECKSUM_OK_NON_CERTIFIEE":
   priorite="P3_ISIN_ARCHIVE_A_CORROBORER"
  else:
   priorite="P4_AUCUNE_PISTE_PRIMAIRE"
  lignes.append({
   "Ticker":ticker,"Societe":str(r.get("Societe","")),
   "Priorite_revue_documentaire":priorite,
   "Identifiant_dossier_source":identifiant_dossier(r) or "MANQUANTE",
   "Identifiant_piste_unique_non_certifie":next(iter(identifiants)) if len(identifiants)==1 else "MANQUANTE",
   "ISIN_archive_piste_non_certifiee":isin_piste,
   "Captures_SHA256_OK_pistes":len(brutes),
   "URLs_distinctes_pistes":len(urls),
   "SHA256_distincts_pistes":len(empreintes),
   "Domaines_hebergement_distincts_pistes":len(domaines),
   "Publications_date_inconnue":inconnu,
   "Publications_date_connue_a_verifier":len(brutes)-inconnu,
   "URLs_pistes":" | ".join(sorted(urls)) or "MANQUANTE",
   "SHA256_pistes":" | ".join(sorted(empreintes)) or "MANQUANTE",
   "Dates_publication_pistes":" | ".join(sorted({str(x[4]) for x in brutes})) or "MANQUANTE",
   "Statut_certification":"PISTES_NON_CERTIFIEES",
   "Qualification_economique":"NON_CALCULEE_PAR_CET_AUDIT"})
 sortie=pd.DataFrame(lignes,columns=colonnes).sort_values(
  ["Priorite_revue_documentaire","Ticker"],kind="stable")
 tmp=destination.with_suffix(".tmp")
 sortie.to_csv(tmp,index=False)
 tmp.replace(destination)
 return sortie

def executer():
 if not SRC.exists(): raise RuntimeError("Dossiers SSI absents")
 df=pd.read_csv(SRC,dtype=str,keep_default_na=False)
 if "Ticker" not in df:raise RuntimeError("Ticker absent des dossiers SSI")
 # Un ticker vide ou duplique ne doit jamais faire tomber le plan des autres
 # candidats. Comparaison normalisee : casse et espaces ne levent pas une
 # ambiguite d'emetteur. Aucune note/preuve n'est reprise de ces lignes.
 df["Ticker"]=df["Ticker"].astype(str).str.strip()
 cles=df["Ticker"].str.upper()
 ambigu=cles.eq("") | cles.duplicated(keep=False)
 quarantaines=[]
 for cle in sorted(set(cles[ambigu])):
  groupe=df.loc[cles.eq(cle)]
  quarantaines.append({"Ticker_normalise":cle,"Lignes":len(groupe),
                       "Motif":"TICKER_VIDE" if not cle else "TICKER_DUPLIQUE",
                       "Statut":"EN_ATTENTE_DATA_IDENTITE_AMBIGUE"})
 # Sortie isolee du registre de quarantaine 07Q, qui ne doit pas etre ecrase.
 quarantaine=D/"QUARANTAINE_PLAN_SSI.csv"
 temporaire=quarantaine.with_suffix(".tmp")
 pd.DataFrame(quarantaines,columns=["Ticker_normalise","Lignes","Motif","Statut"]).to_csv(temporaire,index=False)
 temporaire.replace(quarantaine)
 df=df.loc[~ambigu].copy()
 pistes,sha_archive=lire_pistes_archive()
 captures,invalides,bloquees=indexer_captures_primaires()
 rows=[]
 for _,r in df.iterrows():
  # Même résolution d’identité que 07R : CIK source ou ISIN/LEI déclaré,
  # formellement valide. Aucune déclaration ne vaut preuve SCE vérifiée.
  ident=identifiant_dossier(r) or "MANQUANTE"
  collision=str(r.get("Conflit_identite_CIK","NON")).strip().upper()=="OUI"
  isin_piste,societe_archive,statut_piste=pistes.get(r["Ticker"],("MANQUANTE","MANQUANTE","AUCUNE_PISTE_ARCHIVE"))
  brutes=captures.get(r["Ticker"],[])
  # Plusieurs captures de la meme URL ne valent jamais plusieurs sources.
  urls={x[1] for x in brutes}
  identifiants={x[0] for x in brutes}
  ident_dossier=identifiant_dossier(r)
  statut_captures=("AUCUNE_CAPTURE_SHA256_OK" if not brutes else
                   "CONFLIT_IDENTIFIANTS_CAPTURE_NON_CERTIFIE" if len(identifiants)>1 or
                   (ident_dossier and ident_dossier not in identifiants) else
                   "PISTES_CAPTUREES_NON_CERTIFIEES")
  base={"Ticker":r["Ticker"],"Societe":r.get("Societe",""),
        "Source_actuelle":r.get("B6_source",""),
        "Date_source_actuelle":r.get("B6_date",""),
        "Identifiant_emetteur_source":ident,
        "Pays_cotation_declare":r.get("Pays",""),
        "Pays_emetteur_verifie":"MANQUANTE",
        "ISIN_piste_non_certifiee":isin_piste,
        "Societe_archive_ISIN":societe_archive,
        "Statut_piste_ISIN":statut_piste,
        "Provenance_archive_ISIN":"DONNEES/"+ARCHIVE_IDENTITE.name if statut_piste!="AUCUNE_PISTE_ARCHIVE" else "MANQUANTE",
        "SHA256_archive_ISIN":sha_archive if statut_piste!="AUCUNE_PISTE_ARCHIVE" else "MANQUANTE",
        "Date_archive_ISIN":"MANQUANTE",
        "Captures_primaires_SHA256_OK_pistes":str(len(brutes)),
        "URLs_primaires_distinctes_pistes":str(len(urls)),
        "Identifiants_captures_non_certifies":"|".join(sorted(identifiants)) if brutes else "MANQUANTE",
        "Captures_publication_inconnue":str(sum(x[3] for x in brutes)),
        "Statut_captures_non_certifiees":statut_captures,
        "Captures_sources_URL_pistes":" | ".join(sorted(urls)) if brutes else "MANQUANTE",
        "Captures_SHA256_pistes":" | ".join(sorted({x[2] for x in brutes})) if brutes else "MANQUANTE",
        "Captures_dates_publication_pistes":" | ".join(sorted({x[4] for x in brutes})) if brutes else "MANQUANTE",
        "Captures_dates_collecte_UTC_pistes":" | ".join(sorted({x[5] for x in brutes})) if brutes else "MANQUANTE"}
  # Ces deux controles sont des prealables a la notation, non des notes.
  # Ne jamais utiliser Pays (place de cotation) comme domicile de l'emetteur.
  rows.append({**base,"Bloc_SSI":"IDENTITE_SCE",
    "Variables_absentes":("Collision identite CIK non levee" if collision else
                          "CIK ou identifiant reglementaire ISIN/LEI verifie" if ident=="MANQUANTE" else ""),
    "Preuve_validee":"A_CONTROLER" if not manquant(r.get("Preuves_identite_SCE","")) else "NON",
    "Note_presente":"NON",
    "Preuves_complementaires_requises":"Deux sources primaires independantes, concordance emetteur/ISIN/LEI/CIK, provenance, date et SHA256",
    "Statut":("EN_ATTENTE_DATA_IDENTITE_CIK" if collision else
              "EN_ATTENTE_DATA_IDENTITE" if ident=="MANQUANTE" else
              "A_VERIFIER_IDENTITE_SCE")})
  rows.append({**base,"Bloc_SSI":"EXCLUSIONS",
    "Variables_absentes":"Preuve primaire du controle des exclusions" if manquant(r.get("Motif_eliminatoire","")) else "",
    "Preuve_validee":"A_CONTROLER" if not manquant(r.get("Motif_eliminatoire","")) else "NON",
    "Note_presente":"NON",
    "Preuves_complementaires_requises":"Exclusions documentees sur le meme emetteur, date, fichier brut et SHA256",
    "Statut":"A_CONTROLER_EXCLUSIONS"})
  for bloc,fields in CHAMPS.items():
   absents=[f for f in fields if f not in df.columns or manquant(r.get(f,""))]
   preuve=r.get("Preuve_"+bloc,"MANQUANTE")
   note=r.get("Note_"+bloc,"MANQUANTE")
   rows.append({**base,"Bloc_SSI":bloc,
    "Variables_absentes":" | ".join(absents) if absents else "",
    "Preuve_validee":"NON" if manquant(preuve) else "A_CONTROLER",
    "Note_presente":"NON" if manquant(note) else "OUI",
    "Preuves_complementaires_requises":COMPLEMENTS[bloc],
    "Statut":"A_COMPLETER_PREUVES_SSI"})
 out=pd.DataFrame(rows,columns=COLONNES)
 out.to_csv(OUT,index=False)
 publier_concordances_brutes(captures)
 file_revue=publier_file_certification(df,captures,pistes)
 blocs=out[out.Bloc_SSI.isin(CHAMPS)]
 pd.DataFrame([{"Dossiers":len(df),"Dossiers_en_quarantaine":int(ambigu.sum()),"Blocs_a_auditer":len(blocs),
   "Blocs_avec_variables_absentes":int(blocs["Variables_absentes"].ne("").sum()),
   "Controles_identite_exclusions":len(out)-len(blocs),
   "Identites_CIK_source_absentes":sum(not bool(re.fullmatch(r"[0-9]{10}",str(x).strip())) for x in df["CIK"]) if "CIK" in df else len(df),
   "Lignes_plan":len(out),
   "Captures_primaires_SHA256_OK_pistes":sum(len(v) for v in captures.values()),
   "Captures_invalides_exclues":invalides,
   "Sources_bloquees":bloquees,
   "Dossiers_avec_pistes_capturees":sum(bool(captures.get(t)) for t in df["Ticker"]),
   "Dossiers_priorite_P1_pistes_multidomaines":int(file_revue["Priorite_revue_documentaire"].eq("P1_PISTES_MULTIDOMAINES_A_CERTIFIER").sum()),
   "Pistes_ISIN_checksum_OK_non_certifiees":int((out["Bloc_SSI"].eq("IDENTITE_SCE") & out["Statut_piste_ISIN"].eq("PISTE_ISIN_CHECKSUM_OK_NON_CERTIFIEE")).sum()),
   "Pistes_ISIN_ambigues_ou_invalides":int((out["Bloc_SSI"].eq("IDENTITE_SCE") & out["Statut_piste_ISIN"].isin(["TICKER_AMBIGU_ARCHIVE","ISIN_INVALIDE_ARCHIVE"])).sum()),
   "Statut":"EN_ATTENTE_DATA" if df.empty else "AUCUNE_NOTE_AUTOMATIQUE_SANS_PREUVE"}]).to_csv(AUD,index=False)
 print("Plan de collecte SSI",len(df),"dossiers",len(blocs),"blocs",len(out)-len(blocs),"controles")
 return out
if __name__=="__main__": executer()

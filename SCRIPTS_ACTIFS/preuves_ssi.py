"""Validation des preuves SSI : références vérifiées, fichiers bruts et dates.
La collecte ne valide jamais sa propre preuve. Le registre reçoit des revues indépendantes identifiées
append-only (humain ou assistant explicitement nommé) ; une correction référence l'ID remplacé et laisse l'historique intact.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, math, re
import pandas as pd
MAX={'B1':20,'B2':15,'B3':15,'B4':20,'B5':10,'B6':10,'B7':10}
CHAMPS=['ID_preuve','Remplace_ID','Ticker','Bloc','Identifiant_emetteur','Source_URL',
        'Type_source','Date_publication','Fichier_brut','SHA256','Statut_identite',
        'Statut_verification','Verificateur','Date_verification_UTC','Justification','Note']
MANQUANTS={'','MANQUANTE','A_COMPLETER','NON_VERIFIE','N/A','NAN','NONE'}
def manquant(v):return str(v).strip().upper() in MANQUANTS

def checksum_isin_valide(isin):
    """ISO 6166 / Luhn. Un checksum correct ne certifie PAS l'emetteur."""
    if not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}[0-9]', isin):
        return False
    chiffres=''.join(str(ord(c)-55) if 'A'<=c<='Z' else c for c in isin)
    total=0
    for pos,c in enumerate(reversed(chiffres)):
        n=int(c)
        if pos%2:
            n*=2
            n=n//10+n%10
        total+=n
    return total%10==0

def checksum_lei_valide(lei):
    """ISO 17442 / ISO 7064 mod 97-10, sans certification de l'identite."""
    if not re.fullmatch(r'[A-Z0-9]{20}', lei):
        return False
    chiffres=''.join(str(ord(c)-55) if 'A'<=c<='Z' else c for c in lei)
    # Calcul modulaire incrementiel pour ne pas dependre d'un entier geant.
    reste=0
    for c in chiffres:
        reste=(reste*10+int(c))%97
    return reste==1

def identifiant_reglementaire_formel_valide(ident):
    """CIK exact ou ISIN/LEI avec checksum; la preuve primaire reste obligatoire."""
    if re.fullmatch(r'CIK:[0-9]{10}', ident):
        return True
    if ident.startswith('ISIN:'):
        return checksum_isin_valide(ident[5:])
    if ident.startswith('LEI:'):
        return checksum_lei_valide(ident[4:])
    return False

def identifiant_dossier(r):
    """Identité attendue : CIK source valide OU ISIN/LEI explicitement vérifié.

    Un ISIN/LEI déclaré ne devient jamais une preuve : verifier_identite_sce
    exige deux documents primaires distincts concordants, puis chaque bloc
    et chaque exclusion doivent porter le même identifiant. Un CIK source
    présent mais malformé/divergent ne peut pas être contourné.
    """
    cik=str(r.get('CIK','')).strip()
    ident=str(r.get('Identifiant_emetteur_verifie','')).strip()
    if not manquant(cik):
        if not re.fullmatch(r'[0-9]{10}',cik):
            return ''
        attendu='CIK:'+cik
        return attendu if manquant(ident) or ident==attendu else ''
    if (not manquant(ident) and ident.startswith(('ISIN:','LEI:'))
            and identifiant_reglementaire_formel_valide(ident)):
        return ident
    return ''

def registre(base,limite=None):
    p=base/'DONNEES/REGISTRE_PREUVES_SSI.csv'
    if not p.exists():return pd.DataFrame(columns=CHAMPS)
    d=pd.read_csv(p,dtype=str,keep_default_na=False)
    if not set(CHAMPS).issubset(d.columns):raise RuntimeError('Schéma registre preuves incomplet')
    if d.ID_preuve.duplicated().any() or d.ID_preuve.map(manquant).any():raise RuntimeError('ID preuve invalide/dupliqué')
    if not d.empty:
        dates=pd.to_datetime(d.Date_verification_UTC,utc=True,errors='coerce')
        if dates.isna().any():raise RuntimeError('Date de vérification invalide')
        if limite is not None: d=d[dates<=pd.Timestamp(limite)].copy()
    # Seuls les remplacements validés peuvent retirer une preuve valide.
    valides=d[d.Statut_verification.eq('VERIFIEE')]
    for _,r in valides[~valides.Remplace_ID.map(manquant)].iterrows():
        old=d[d.ID_preuve.eq(r.Remplace_ID)]
        if len(old)!=1 or old.iloc[0].Ticker!=r.Ticker or old.iloc[0].Bloc!=r.Bloc:
            raise RuntimeError('Remplacement de preuve incohérent')
        if pd.Timestamp(r.Date_verification_UTC)<=pd.Timestamp(old.iloc[0].Date_verification_UTC):
            raise RuntimeError('Remplacement de preuve non postérieur')
        errors=verifier(r,r.Ticker,r.Bloc,base,limite)
        if not errors:d=d[~d.ID_preuve.eq(r.Remplace_ID)]
    return d

def verifier(r,ticker,bloc,base,limite=None):
    errors=[]
    if r.Ticker!=ticker or r.Bloc!=bloc:errors.append('preuve hors ticker/bloc')
    if r.Statut_verification!='VERIFIEE' or r.Statut_identite!='VERIFIEE':errors.append('identité/contenu non vérifié')
    for c in ['Identifiant_emetteur','Verificateur','Justification','SHA256']:
        if manquant(r[c]):errors.append(c+' manquant')
    if not identifiant_reglementaire_formel_valide(str(r.Identifiant_emetteur)):
        errors.append('identifiant émetteur invalide')
    if not r.Source_URL.startswith('https://'):errors.append('source sans URL HTTPS')
    types={'PUBLICATION_EMETTEUR','DEPOT_REGLEMENTAIRE'}
    if bloc=='B7':types.add('DONNEE_MARCHE')
    if r.Type_source not in types:errors.append('source non primaire pour ce bloc')
    pub=pd.to_datetime(r.Date_publication,utc=True,errors='coerce')
    ver=pd.to_datetime(r.Date_verification_UTC,utc=True,errors='coerce')
    cutoff=pd.Timestamp(limite or datetime.now(timezone.utc))
    if pd.isna(pub) or pd.isna(ver) or pub>ver or ver>cutoff:errors.append('dates futures/incohérentes')
    root=base.resolve();path=(base/r.Fichier_brut).resolve()
    if root not in path.parents or not path.is_file():errors.append('document brut absent/hors dépôt')
    elif hashlib.sha256(path.read_bytes()).hexdigest()!=r.SHA256:errors.append('empreinte document divergente')
    if bloc in MAX:
        try:
            note=float(r.Note)
            if not math.isfinite(note) or not note.is_integer() or not 0<=note<=MAX[bloc]:raise ValueError()
        except ValueError:errors.append('note invalide/hors barème')
    return errors

def verifier_identite_sce(r,d,base,limite=None):
    erreurs=[]
    # Protection aussi pour les appels directs hors 07R : une collision CIK
    # ou un statut absent/inconnu ne peut jamais etre leve par les notes.
    if str(r.get('Conflit_identite_CIK','')).strip().upper()!='NON':
        erreurs.append('collision CIK non levée ou contrôle CIK absent/invalide')
    if r.get('SCE_valide')!='OUI':return erreurs+['contrôles SCE non validés']
    ids=[x.strip() for x in str(r.get('Preuves_identite_SCE','')).split('|') if x.strip()]
    z=d[d.ID_preuve.isin(ids)];ident=identifiant_dossier(r)
    if not ident:erreurs.append('identifiant réglementaire du dossier absent, invalide ou contradictoire')
    if len(ids)<2 or len(ids)!=len(set(ids)) or len(z)!=len(ids) or z.Source_URL.nunique()<2:erreurs.append('deux preuves identité SCE requises')
    for _,p in z.iterrows():
        erreurs.extend(verifier(p,r.Ticker,'IDENTITE_SCE',base,limite))
        if not ident or p.Identifiant_emetteur!=ident:erreurs.append('identité SCE divergente du dossier')
    return erreurs

def valider_dossier(r,d,base,limite=None):
    errors=[];notes=[];identifiants=set()
    for bloc in MAX:
        ids=[x.strip() for x in str(r.get('Preuve_'+bloc,'')).split('|') if x.strip()]
        if not ids or any(manquant(x) for x in ids):errors.append(bloc+': référence de preuve absente');continue
        preuves=d[d.ID_preuve.isin(ids)]
        if len(preuves)!=len(ids):errors.append(bloc+': preuve absente ou remplacée');continue
        for _,preuve in preuves.iterrows():
            errors.extend(bloc+': '+x for x in verifier(preuve,r.Ticker,bloc,base,limite))
            identifiants.add(preuve.Identifiant_emetteur)
        try:
            n=float(r['Note_'+bloc])
            if not math.isfinite(n) or not n.is_integer() or not 0<=n<=MAX[bloc]:raise ValueError()
            if not all(float(x)==n for x in preuves.Note):raise ValueError()
            notes.append(int(n))
        except ValueError:errors.append(bloc+': note non concordante avec preuve vérifiée')
    if len(identifiants)>1:errors.append('identité émetteur divergente entre blocs')
    ident=identifiant_dossier(r)
    if not ident:errors.append('identifiant réglementaire du dossier absent, invalide ou contradictoire')
    if ident and any(x!=ident for x in identifiants):errors.append('identité des preuves différente de l\'identifiant du dossier')
    # Le controle d'identite SCE est obligatoire, meme pour les anciens
    # dossiers qui ne possedent pas encore la colonne SCE_valide.
    # Ne jamais traiter une colonne absente comme une validation implicite.
    errors.extend(verifier_identite_sce(r,d,base,limite))
    decision=str(r.get('Decision_eliminatoire','')).upper().strip()
    if decision!='NON':errors.append('exclusions non vérifiées')
    ids=str(r.get('Motif_eliminatoire','')).split('|')
    ex=d[d.ID_preuve.isin(ids)]
    if not ids or len(ex)!=len(ids):errors.append('preuve du contrôle des exclusions absente')
    else:
        for _,p in ex.iterrows():
            errors.extend('EXCLUSIONS: '+x for x in verifier(p,r.Ticker,'EXCLUSIONS',base,limite))
            if identifiants and p.Identifiant_emetteur not in identifiants:errors.append('identité exclusions divergente')
    return notes,errors

def bilan_blocs_documentes(r,d,base,limite=None):
    """Décompte partiel, jamais une note SSI imputée ni une admission.
    Le plafond ne remplace pas les contrôles d'identité/SCE ou les exclusions.
    """
    notes={}
    for bloc,maximum in MAX.items():
        ids=[v.strip() for v in str(r.get('Preuve_'+bloc,'')).split('|') if v.strip()]
        if not ids or len(ids)!=len(set(ids)) or any(manquant(v) for v in ids):continue
        preuves=d[d.ID_preuve.isin(ids)]
        if len(preuves)!=len(ids):continue
        if any(verifier(p,r.Ticker,bloc,base,limite) for _,p in preuves.iterrows()):continue
        ident=identifiant_dossier(r)
        if not ident or any(p.Identifiant_emetteur!=ident for _,p in preuves.iterrows()):continue
        try:
            n=float(r.get('Note_'+bloc,''))
            if not math.isfinite(n) or not n.is_integer() or not 0<=n<=maximum:continue
            if any(float(v)!=n for v in preuves.Note):continue
        except (ValueError,TypeError):continue
        notes[bloc]=int(n)
    points=sum(notes.values());maximum=sum(MAX[b] for b in notes)
    return {'Blocs_SSI_documentes':'|'.join(notes),'Nombre_blocs_SSI_documentes':len(notes),
            'Points_sur_blocs_documentes':points,'Maximum_blocs_documentes':maximum,
            'Plafond_SSI_si_blocs_restants_maximaux':points+100-maximum,
            'Portee_plafond':'ARITHMETIQUE_CONDITIONNELLE_AUX_NOTES_DOCUMENTEES_PAS_ADMISSION'}

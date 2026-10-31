# MICRO CAPS — ICAPE HOLDING : pistes primaires croisées (31/10/2026)

**État : EN_ATTENTE_CAPTURE_BRUTE / EN_ATTENTE_DATA.** Recherche officielle effectuée après inventaire des archives GitHub/Drive (PRICE02A, SEC_BRIDGE, DATA04_EODHD_FUNDAMENTALS). Ce fichier est un journal de recherche, pas une preuve SCE certifiée ni une admission SSI. Aucun document brut n'a pu être téléchargé et archivé dans ce passage ; aucune empreinte SHA256 du document primaire n'est disponible. Ne pas inscrire VERIFIEE dans REGISTRE_PREUVES_SSI.csv sur cette base.

## Rapprochement candidat / émetteur (pistes non certifiées)

- DONNEES/CANDIDATS_PRETS_SSI.csv : Z8J.SG (Stuttgart), Z8J.F (Francfort), deux cotations de ICAPE HOLDING ; chiffres Yahoo non primaires.
- DONNEES/IDENTITE_COTATIONS_MULTIPLES.csv : ALICA.PA et Z8J.SG partagent l'ISIN indicatif FR001400A3Q3 ; catalogue NON CERTIFIÉ.
- Émetteur : https://www.icape-group.com/fr/centre-des-investisseurs/ — ICAPE HOLDING, ISIN FR001400A3Q3, mnémonique ALICA, Euronext Growth Paris. Date de publication de cette page non précisée ; recherche du 31/10/2026.
- Marché primaire : https://live.euronext.com/en/ipo-showcase/icape-holding — ICAPE HOLDING, ISIN FR001400A3Q3, LEI 969500SMJNIR6M3A8D61, ALICA, Paris, IPO 11/07/2022 ; recherche du 31/10/2026.
- Stuttgart : https://www.boerse-stuttgart.de/de-de/produkte/aktien/stuttgart/a3dqa9 — ISIN FR001400A3Q3, WKN A3DQA9, symbole Z8J, Stuttgart ; page dynamique sans date fixe de publication.
- Francfort : https://live.deutsche-boerse.com/aktie/icape-holding-eo-40 — ISIN FR001400A3Q3, WKN A3DQA9, symbole Z8J, Francfort ; page dynamique sans date fixe de publication.

## Vérifications restant obligatoires

1. Télécharger les octets originaux d'au moins deux sources indépendantes ; enregistrer la date de capture UTC, URL finale, code HTTP, chemin brut et SHA256 calculé sur les octets. Les extraits du moteur de recherche ne sont pas des fichiers bruts.
2. Contrôler la concordance de l'ISIN/LEI avec l'émetteur, la place et le symbole, en distinguant Z8J.SG, Z8J.F et ALICA.PA. Ne pas traiter trois cotations comme trois sociétés ; désigner la place primaire selon le mandat.
3. Faire une revue SCE indépendante et consigner les preuves append-only, sans inventer de date ni de vérificateur.
4. Ensuite seulement alimenter 07Q/07R. Sept blocs SSI, exclusions et notes MCPA restent MANQUANTE jusqu'à leurs propres preuves.

**Résultat :** trois marchés pour un même ISIN potentiel, aucune certification, aucun score, aucun historique modifié.


## Mise à jour effective — 31/10/2026 09:39 UTC (capture brute, NON certification)

L'état « aucun document brut » ci-dessus décrit le **premier passage** et n'est plus l'état documentaire courant. Le collecteur historique `07AA_COLLECTE_DOCUMENTS_OFFICIELS.py` a été réutilisé sur la branche `repair/microcaps-chain-20261030`, avec le registre spécifique `CONFIG/DOCUMENTS_OFFICIELS_ICAPE_A_COLLECTER.csv` et le workflow isolé `collecte_icape_primaires_isolee.yml`.

- Exécution GitHub Actions **41189502515**, terminée `success` ; commit automatique **418693db66bfddb3af5b54c415109b66fa12d6e6**. Les deux pages HTTPS ont été effectivement capturées en octets HTML, sans notation.
- Émetteur : `AUDITS/SOURCES_OFFICIELLES/20261031T093904998805Z/edeafb246554d75e51b1f445e0ce34a19bd4ace8af8986d31dcf1c0726bc35b0.bin`, SHA256 `edeafb246554d75e51b1f445e0ce34a19bd4ace8af8986d31dcf1c0726bc35b0`, source `https://www.icape-group.com/fr/centre-des-investisseurs/`.
- Opérateur de marché Euronext : `AUDITS/SOURCES_OFFICIELLES/20261031T093904998805Z/32fbb3eb9ffa8eec72f92a90ded811eaf115d73668b27dc7853f3fee74307e07.bin`, SHA256 `32fbb3eb9ffa8eec72f92a90ded811eaf115d73668b27dc7853f3fee74307e07`, source `https://live.euronext.com/en/ipo-showcase/icape-holding`.
- Les deux fichiers contiennent visiblement `ICAPE` et `FR001400A3Q3` ; la page Euronext comporte également le LEI `969500SMJNIR6M3A8D61`. L'audit et le manifeste sont dans le même répertoire. Les dates de **capture** sont connues, les dates de **publication des pages** restent explicitement `INCONNUE_NE_PAS_UTILISER_RETROSPECTIVEMENT`.
- Aucune promotion dans `REGISTRE_PREUVES_SSI.csv` : `Statut_identite=A_VERIFIER_COTATION_Z8J_F`, `Notes_attribuees=0`. Une revue SCE indépendante, une vérification du lien `Z8J.F`/émetteur et les publications financières datées restent indispensables.
- Une seconde exécution a été déclenchée pour contrôler automatiquement les SHA256 et la présence de l'ISIN dans les octets ; son résultat doit être vérifié séparément avant de revendiquer une validation de cette nouvelle étape.

**Périmètre :** 2 documents sur 1 seul candidat configuré ; 1 360 dossiers restent sans source dans cette collecte spécifique. Aucune admission SSI, aucun challenger, aucun duel ni arbitrage n'est déduit de ces deux documents. `main`, le coffre maître et les historiques officiels restent exclus des écritures.

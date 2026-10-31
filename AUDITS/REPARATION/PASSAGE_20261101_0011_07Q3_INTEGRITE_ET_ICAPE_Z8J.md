# MICRO CAPS — passage isolé du 1er novembre 2026 (Europe/Paris)

## Périmètre et inventaire préalable
PR brouillon #1, branche `repair/microcaps-chain-20261030`, tête initiale `6a70244dce6412c2be81fd6d3ff0e16385171790`. Inventaire Google Drive avant modification : dossier PRICE02A (signaux mensuels et raw_prices), dossier SEC_BRIDGE (mapping SEC et fichiers companyfacts), FUND02E et FUND03A non retrouvés par recherche de nom. Réutilisation stricte de 07AA, 07Q/07Q2/07Q3/07R et des tests historiques. Aucun fichier du coffre maître, des historiques officiels, des portefeuilles réels ou de `main` édité.

## Modifications effectivement publiées
1. `e6e8a2bce63c6d8024bb46fffcdab10820e03921` : 07Q3 rejette les montants avec séparateurs de milliers ambigus (ex. `1,2,3`), exige un fuseau explicite sur les horodatages de provenance, rejette les lignes sans tableau/ligne source, déduplique les faits identiques pour la couverture et place toutes les variantes contradictoires d'un même fait/document/période en `EN_ATTENTE_DATA_CONFLIT_FACTUEL`. Aucun changement aux archives brutes et aucun score attribué.
2. `b3e5ac1fc9683f461fd2e8b69eec32f3b85e169d` : tests adverses hors réseau couvrant montants, dates, doublons, conflits, continuité des autres dossiers et absence de scores.
3. `d8307b103c1b2e371fbc3cbfcee63b23e97ead63` : réutilisation du collecteur historique 07AA ; ajout de la fiche officielle Deutsche Börse ICAPE, symbole `Z8J`, ISIN `FR001400A3Q3`, à la configuration existante (désormais 5 documents) ; adaptation atomique du workflow et des tests. `Z8J.F` reste un suffixe fournisseur non certifié par la seule fiche de marché.
4. `3165177ed2cfbe4a8b3f628f21c457e70f00b27a` : publication automatique des cinq captures ICAPE avec manifeste SHA256 dans `AUDITS/SOURCES_OFFICIELLES/20261031T231641051863Z/`.
5. `915e4d63dd4e93b2b34276e64e60bb46b24ed590` : publication automatique de la préparation SSI, audit actualisé (état constaté avant création de ce journal).

## Preuve primaire nouvellement collectée
Opérateur de marché : `https://live.deutsche-boerse.com/equity/icape-holding-eo-40`.
Capture UTC : `2026-10-31T23:16:41.051863+00:00`.
Identifiant document : `ICAPE_DEUTSCHE_BOERSE_FRANKFURT_Z8J`.
Empreinte du brut : `9fe2d9b02b8d42055e92f8d7159e4dee6bc083aa0b4567e5e7ee51068b2c8dcc`.
Statut : `DOCUMENT_COLLECTE_A_VERIFIER` ; date de publication inconnue ; identité SCE NON certifiée ; notes SSI/MCPA `MANQUANTE`. Les quatre autres documents ICAPE ont également été capturés, avec leurs empreintes individuelles dans le manifeste. Les cinq captures ne sont pas assimilées à cinq preuves indépendantes.

## Tests et exécutions vérifiés
- CI `41251621140` : SUCCESS sur `b3e5ac1` (07Q3 et tests).
- Replays isolés `41251621127` et `41251625574` : SUCCESS sur `b3e5ac1`.
- CI `41251759583` : SUCCESS sur `d8307b1` (configuration ICAPE et collecteur).
- Replays isolés `41251759593` et `41251763609` : SUCCESS sur `d8307b1`.
- Collecte ICAPE `41251759756` : SUCCESS ; 5/5 documents collectés, 0 source bloquée sur cette collecte, 0 note.
- Préparation SSI déclenchée automatiquement `41251855266` : SUCCESS. Audit : 1 361 dossiers, 12 249 lignes de plan, 49 captures intègres classées comme pistes (non nécessairement indépendantes), 6 anomalies historiques exclues, 1 source bloquée, 2 dossiers avec pistes ; 0 admission et 1 361 identités en quarantaine. Le registre de candidats n'est pas requalifié par ce seul succès CI.
- Les anciens replays `action_required` ne sont pas comptés comme validations.

## Risques résiduels et suite prioritaire
Certifier séparément la correspondance émetteur/ISIN/cotation secondaire `Z8J.F` et `1F6.F` au moyen de deux preuves primaires réellement indépendantes, dater les publications lorsque vérifiable et recontrôler les transcriptions financières ; continuer B4–B7 et les autres 1 359 dossiers en `EN_ATTENTE_DATA`. Puis seulement calculer SSI >=65 et MCPA/IPS >=80 sur preuves, confronter 09B aux 40 titulaires et valider replay mensuel avec témoin 4 000 EUR, géré 4 000 EUR et frais 2,5 %. Aucun ordre réel, aucune fusion `main`, aucune sauvegarde `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant validation intégrale.

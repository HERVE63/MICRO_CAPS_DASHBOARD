# MICRO CAPS — passage du 1er novembre 2026, vers 13:38–13:41 UTC

## Reprise et réutilisation avant écriture

- PR brouillon #1 : `repair/microcaps-chain-20261030`, tête initiale `a55478bb531ec22f7eb352198df19dceb8649ab6`. Comparaison avec le passage précédent : **identique, zéro commit nouveau**.
- Google Drive : dossier PRICE02A (`1_g42pXqd_XeYpzbh7eN5_7GyEuCSsFoD`) et SEC_BRIDGE (`1U8ua2MF0OhTRTYYx2uSemNpNWaG0nr8T`) retrouvés ; recherches exactes FUND02E/FUND03A sans résultat. Leur absence de résultat ne démontre pas une absence universelle.
- Réutilisation : collecteur existant `SCRIPTS_ACTIFS/07AA_COLLECTE_DOCUMENTS_OFFICIELS.py`, validation 07Q2/07R, archives `AUDITS/SOURCES_OFFICIELLES`, tests `TESTS/test_reprise_fermentalg_hors_reseau.py`. Aucun nouveau collecteur Python.
- Dernier audit SSI lu : 1 361 dossiers, zéro admis, 1 361 identités en quarantaine. Dernier raccordement financier : 18 observations sur deux dossiers, 18 en attente, zéro score.

## Nouvelle pièce primaire identifiée — changement historique du mnémonique

- **Source émetteur datée du 12 avril 2024** : communiqué Fermentalg « Transfert de la cotation des titres Fermentalg sur le marché Euronext Growth Paris effectif le 16 avril 2024 ». Source primaire : https://www.webdisclosure.fr/press-release/fermentalg-epa-falg-transfert-de-la-cotation-des-titres-fermentalg-sur-le-marche-euronext-growth-paris-effectif-le-16-avril-2024-jS9wwOZjG9n
- Le communiqué annonce que l'ISIN `FR0011271600` reste inchangé et que le mnémonique devient `ALGAE` à l'occasion du transfert du **16 avril 2024**. Le titre de la publication conserve l'ancien symbole `FALG`. Cela documente un **changement historique de symbole**, sans déduire la cotation allemande `1F6` ni le suffixe fournisseur `1F6.F`.
- Corroboration opérateur de marché : https://live.euronext.com/en/ipo-showcase/fermentalg-0 (ISIN, ALGAE, transfert daté du 16 avril 2024). **La date de transfert n'est pas la date de publication de cette fiche**, laquelle reste inconnue. Ce document figurait déjà dans les archives : ne pas le recapturer.
- Deux communiqués de l'émetteur, même hébergeur, ne deviennent jamais deux éditeurs indépendants par simple multiplication de captures.

## Écritures Git effectivement réalisées

1. `13ad7ce1936563e46c293a98a93eb6e749c46f0c` : nouveau **registre de source**, pas de note : `AUDITS/REPARATION/REGISTRE_FERMENTALG_TRANSFERT_2024.csv`. Date civile de publication déclarée `2024-04-12`, URL et domaine explicites, identité `A_VERIFIER`.
2. `f1fd31cc111620ea19bbe848d93177b76ad2dc9f` : workflow isolé `.github/workflows/collecte_transfert_fermentalg_2024_isolee.yml` utilisant **07AA existant**, contrôle de l'archive, SHA256, dates et contenu `FALG/ALGAE/FR0011271600`, puis publication exclusive dans `AUDITS/SOURCES_OFFICIELLES` sur la branche de réparation. Échec source : `BLOQUE_SOURCE`, sans empreinte inventée ; aucune certification automatique.
3. `3cebbf568e8bbcae75840f33c80365f8662f5cfe` : extension du test hors réseau **déjà existant** pour vérifier l'unicité du nouveau registre, la chronologie, les trois URL distinctes et l'absence de notes.

Les trois écritures ont été confirmées par les réponses de l'API GitHub ; la tête PR observée après ces écritures est `3cebbf568e8bbcae75840f33c80365f8662f5cfe`.

## Statut des tests et limites de preuve

- Le déclencheur `push` du nouveau workflow et celui de la CI principale sont configurés ; **aucun identifiant d'exécution ni résultat CI n'était disponible par le connecteur au moment de cette consignation**. Une configuration publiée n'est pas une exécution prouvée.
- **Capture SHA256 non encore confirmée** : ne pas inscrire d'empreinte de document, de réussite de collecte ou de nouveau décompte SSI tant que le manifeste et l'audit d'exécution ne sont pas relus.
- Aucun score SSI/MCPA, challenger, duel 09B, performance ou transaction virtuelle supplémentaire déclaré validé.
- Aucune modification intentionnelle de `main`, des historiques officiels, du coffre maître, de CPI, des ETF d'assurance-vie ni des portefeuilles réels. PR toujours brouillon, non fusionnée.

## Étape suivante reproductible

1. Contrôler le workflow `collecte_transfert_fermentalg_2024_isolee.yml` dans GitHub Actions, son statut, son audit `AUDIT_DOCUMENTS.csv`, son manifeste, le SHA256 du brut et les assertions `FALG/ALGAE/FR0011271600`.
2. Si la source est bloquée, conserver `BLOQUE_SOURCE` et poursuivre les autres dossiers. Si elle est capturée, vérifier la publication de l'archive et la relance 07Q/07Q2/07R, puis lire les nouveaux registres.
3. Certification SCE **uniquement** après deux preuves primaires réellement vérifiées et indépendantes, date/provenance/identité/ticker contrôlés ; ensuite vérifier les 18 observations financières et les blocs SSI manquants.
4. Ne pas créer `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant validation intégrale de la chaîne, de l'arbitrage virtuel, des benchmarks et du replay.

## Addendum après observation de la publication Git

- Archive **effectivement publiée** par le workflow : `AUDITS/SOURCES_OFFICIELLES/20261101T133947911965Z/`. Le registre d'audit indique `DOCUMENT_COLLECTE_A_VERIFIER`, `Date_collecte_UTC=2026-11-01T13:39:47.911965+00:00`, `Date_publication=2024-04-12` (déclarée à vérifier), `Notes_attribuees=0`.
- Manifeste relu : `documents_configures=1`, `documents_collectes=1`, `sources_bloquees=0`, `notes_attribuees=0`. SHA256 brut **déclaré et contrôlé par le workflow** : `0e7c2536c8a06701d554ec01aae241b1da9cd506fb928e472a2fc9e8b09c1875`. Le fichier `.bin`, l'audit et le manifeste sont présents dans la branche. Cette capture n'est **pas** une certification SCE.
- Incident : l'édition du test historique a également déclenché l'ancien workflow Q1 ; archive redondante `AUDITS/SOURCES_OFFICIELLES/20261101T134021888309Z/`, SHA256 `b1f9b7ea7553e9a2c21d125f17da49d272f2d411316369920d25f2c2a420f649` identique à la pièce Q1 antérieure. Correction `a64d893cc862d730f65e784af5f737496ca975b1` : retrait du chemin de test des déclencheurs de recapture Q1. **Ne pas compter ce doublon comme source indépendante.**
- Le dernier audit SSI encore visible lors de ce contrôle datait de `2026-11-01T12:37:22.473669+00:00` (1 361 dossiers, zéro admission). La régénération post-capture et les résultats CI restent à contrôler ; aucun succès non observé n'est affirmé.
- Journal de PR : commentaire `6558737425`.

## Vérification indépendante du binaire après publication

Le fichier `0e7c2536c8a06701d554ec01aae241b1da9cd506fb928e472a2fc9e8b09c1875.bin` a été relu directement dans GitHub, décodé depuis sa représentation base64 et haché indépendamment de la chaîne CI. L'implémentation SHA256 utilisée a d'abord été vérifiée sur le vecteur de référence `abc` → `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`. Résultat sur **42 704 octets** : `0e7c2536c8a06701d554ec01aae241b1da9cd506fb928e472a2fc9e8b09c1875`, identique à l'audit et au manifeste. Les octets contiennent textuellement `FERMENTALG`, `FR0011271600`, `FALG` et `ALGAE`. **Intégrité binaire démontrée ; identité SCE et cotation fournisseur non certifiées.** Compte rendu PR complémentaire : commentaire `6558746157`.

## Correction définitive du déclencheur Q1

Une seconde recapture redondante du document Q1 a été constatée dans `AUDITS/SOURCES_OFFICIELLES/20261101T134111418433Z/`, suite au déclencheur sur modification du fichier workflow Q1. Même SHA256 `b1f9b7ea7553e9a2c21d125f17da49d272f2d411316369920d25f2c2a420f649`. Commit `c9cafc93901163c98638d87812dfc0573397f586` : le filtre `push.paths` du workflow Q1 est désormais limité à **son propre registre de source** `AUDITS/REPARATION/REGISTRE_COMPLEMENT_FERMENTALG_IDENTITE_20261101.csv` ; modifications de tests, workflow ou configuration générale ne provoquent plus de recapture Q1. Les deux nouvelles captures Q1 ne sont pas des preuves indépendantes supplémentaires. Commentaire PR `6558754411`.

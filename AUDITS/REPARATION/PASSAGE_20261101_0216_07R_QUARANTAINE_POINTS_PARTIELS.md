# MICRO CAPS — contrôle 07R des points partiels en quarantaine — 1er novembre 2026

## État initial et réutilisation des archives
- PR brouillon #1, branche isolée `repair/microcaps-chain-20261030`, tête initiale `64d3a380c11baf0baf5078efad2a40c4da87a4ac`. Aucun changement constaté depuis le passage précédent avant cette intervention.
- Inventaire Google Drive avant toute édition : `PRICE02A` retrouvé (fichier `PRICE02A_MONTHLY_SIGNALS.parquet`, 9 558 146 octets, et dossier `raw_prices`) ; `SEC_BRIDGE` retrouvé (`ticker_cik_coverage.csv`, `sample_companyfacts_coverage.csv`, `sample_filings.csv` et autres fichiers). `FUND02E` et `FUND03A` non retrouvés par recherche de nom. Aucun de ces fichiers n'a été modifié ou réinventé.
- Réutilisation de `07R_VALIDER_NOTES_SSI.py`, `preuves_ssi.py` et des tests de quarantaine/exclusion déjà présents. Aucune nouvelle collecte de données ni attribution de notes.

## Anomalie réellement reproduite
Le validateur 07R calculait `bilan_blocs_documentes` **avant** de vérifier `Conflit_identite_CIK` et `identifiant_dossier`. Un dossier en quarantaine pouvait donc afficher des points partiels et un plafond chiffré, bien que son score total et son admission soient bloqués. Il s'agit d'une fuite de points conditionnels, pas d'une admission effectivement constatée.

## Corrections publiées
1. `3c9026b4bfdb81bbb71a6691b885dab543372a2f` : 07R reporte le calcul des points partiels après les contrôles de collision CIK et d'identifiant réglementaire. En cas de collision, CIK absent ou malformé, les points et maximums documentés valent 0, le plafond 100 est explicitement **non calculé** (`NON_CALCULE_IDENTITE_CIK`) ; `SSI=MANQUANTE`, sans admission. La quarantaine des tickers vides/dupliqués est conservée.
2. `c0f71089f13b6ed866499e1df0f26c1b8c44f742` : renforcement de `TESTS/test_07r_quarantaine_cik.py` ; vérifie que `bilan_blocs_documentes` n'est appelé que pour la fixture à identité CIK valide et que les trois fixtures en quarantaine ne publient aucun point partiel.
3. **Échec réel détecté** : CI `41260446433` a échoué dans `test_07r_exclusion_identite_cik.py` (KeyError `Blocs_SSI_documentes`). La fixture simulait un bilan partiel avec seulement deux champs ; la nouvelle quarantaine expose le schéma complet et a révélé cette incompatibilité du test. L'échec n'a pas été présenté comme un succès.
4. `f82560e889766d96c5e6c02469fef8189da8b5ba` : correction de la fixture de test pour fournir le schéma complet des six champs ; assertion supplémentaire : une exclusion en collision CIK ne publie pas de points.
5. `2e04b32d7b7da961e234069858fa41e94e3ad89b` : publication automatique SSI observée après les corrections ; diff limité à `DONNEES/AUDIT_SSI.csv` et `DONNEES/RESULTATS_SSI.csv`.

## Exécutions vérifiées
- CI complète `41260515957` : **SUCCESS** sur `f82560e8`, y compris tests 07R quarantaine/exclusion et contrôles de sécurité du dépôt.
- Replay isolé `41260515941` : **SUCCESS** sur `f82560e8`.
- Préparation SSI `41260443790` : **SUCCESS** (déclenchée sur `3c9026b4`, avant le correctif de fixture uniquement) ; publication du résultat sur la branche par le commit `2e04b32d`.
- Dernier audit SSI lu après publication : 1 361 dossiers, 0 admission, 0 refus, 1 361 identités CIK en quarantaine ; 18 observations financières pour 2 dossiers, toutes `EN_ATTENTE_DATA`, 0 score attribué. Un workflow vert ne prouve donc **pas** que la sélection économique est opérationnelle.

## Intégrité et étapes suivantes
- Comparaison Git entre l'état initial et `c0f71089` : exactement deux fichiers édités (07R et son test), avant la correction de la fixture et la publication automatique. Aucune mutation de `main`, des portefeuilles réels, des historiques officiels ou du coffre maître.
- Poursuivre la certification indépendante des identités réglementaires et cotations, la vérification primaire des 18 transcriptions, puis les blocs B4–B7. Les dossiers incomplets restent en attente individuellement.
- Aucun challenger SSI/MCPA ni duel 09B autorisé sans preuves ; aucune transaction financière réelle ; aucune fusion de PR. Ne pas créer `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant validation intégrale et manifeste SHA256 reconstructible.

# MICRO CAPS — passage du 31 octobre 2026 — plan d'identité SSI

## Périmètre et reprise vérifiés

- PR brouillon #1, branche `repair/microcaps-chain-20261030`, tête initiale `9029ba3f` ; comparaison GitHub avec le passage précédent : **0 commit nouveau** au début de cette intervention. `main` : `d86124b6`. Aucune fusion.
- Réutilisation avant édition : `SCRIPTS_ACTIFS/07Q2_AUDIT_PREUVES_SSI.py` existant et déjà appelé par les workflows de chasse et de préparation SSI ; aucun collecteur parallèle créé.
- Google Drive : dossier `PRICE02A` avec `PRICE02A_MONTHLY_SIGNALS.parquet` (9 558 146 octets) et `raw_prices` ; `SEC_BRIDGE` avec `ticker_cik_coverage.csv`, `original_transition_ticker_cik_coverage.csv`, `sample_filings.csv`, `sample_companyfacts_coverage.csv`. `DATA04_EODHD_FUNDAMENTALS` listé mais sans contenu retourné par le connecteur. Recherches exactes `FUND02E` et `FUND03A` : aucun résultat. Métadonnées uniquement ; **schémas et empreintes des archives non revalidés lors de ce passage**, donc aucun raccordement automatique.
- Cohorte actuelle : 1 361 dossiers SSI à cotation allemande et sans CIK dans les données de travail. `Pays` décrit ici la **place de cotation**, pas le domicile juridique. Aucune attribution automatique de CIK sur homonymie ou ticker.

## Changements effectués uniquement en branche isolée

1. `5ee68a48` : extension de **07Q2 existant**, sans changer le barème SSI : planification explicite de `IDENTITE_SCE` et `EXCLUSIONS` avant les sept blocs. Le plan conserve ses sept blocs financiers et les colonnes historiques, et ajoute des champs de diagnostic `Identifiant_emetteur_source`, `Pays_cotation_declare`, `Pays_emetteur_verifie`. Le dernier reste `MANQUANTE` sans preuve indépendante. Les CIK sont acceptés comme pistes uniquement s'ils comptent dix chiffres, zéros initiaux conservés.
2. `7982c88f` : nouveau test **sur fixtures fictives**, hors réseau et en répertoire temporaire : cotation allemande sans CIK, CIK américain correctement formaté, références SCE non certifiées, contrôles d'exclusions, préservation de la source et cohorte vide.
3. `943cdcf8` : raccordement du test à la CI existante.
4. Exécution CI n° 41151241266 : **échec réel** sur cohorte vide : `pandas.Series.sum()` sur une série vide d'objets renvoyait une chaîne vide, impossible à convertir en entier. Les tests antérieurs de la même exécution avaient réussi jusqu'à cette étape.
5. `e930e407` : correction ciblée avec `sum(... for ...)` Python, valeur 0 pour la cohorte vide. Aucun contrôle supprimé.
6. Replay 05C n° 41151241235 : **success** sur `943cdcf8`. La CI finale après `e930e407` doit être vérifiée avant de déclarer 07Q2 validé.

## Portée exacte

Le plan distingue les contrôles documentaires manquants ; il ne collecte pas de documents primaires, ne vérifie pas leur SHA256, ne valide pas l'identité SCE, n'attribue **aucune note SSI/MCPA** et ne modifie aucun portefeuille. Pour 1 361 dossiers, il devrait générer 9 lignes par dossier (2 contrôles + 7 blocs), soit 12 249 lignes **si exécuté sur la cohorte inchangée** ; ce total est une attente arithmétique, pas un résultat d'exécution réelle.

## Blocage et suite

La validation 07R impose encore un CIK à dix chiffres pour tous les dossiers, y compris les émetteurs non américains. Une évolution vers `ISIN`/`LEI` doit être précédée d'un schéma de preuves indépendantes par émetteur, de tests de collision ticker et d'une validation de la concordance de chaque preuve ; **ne pas lever la quarantaine par le seul pays de cotation**. Priorité suivante : rattacher les identités réglementaires aux dossiers réellement documentés, puis seulement qualifier SSI >=65 et MCPA/IPS >=80, confronter aux titulaires et tester les arbitrages virtuels.

Statut : **construction, non fusionnable, sauvegarde totale interdite**. Aucun changement sur `main`, coffres maîtres, historiques officiels, CPI, ETF Assurance-Vie ou transactions réelles.

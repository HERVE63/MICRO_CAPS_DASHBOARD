# Passage du 1er novembre 2026 — registre SSI : dates corrompues non bloquantes

## Inventaire préalable et périmètre

Branche de réparation isolée `repair/microcaps-chain-20261030`, PR brouillon #1 ; état de départ `2b106d7be95b85d55696dec31c49104b5b7e78f8`. Comparaison Git depuis cet état avant modification : aucun changement entrant. Aucun fichier de `main` visé.

Google Drive inspecté avant toute écriture : `PRICE02A` contient `PRICE02A_MONTHLY_SIGNALS.parquet` et le dossier `raw_prices` ; `SEC_BRIDGE` contient notamment `ticker_cik_coverage.csv`, `sample_filings.csv`, `sample_companyfacts_coverage.csv` et `original_transition_investable_entries.csv`. Le dossier `DATA04_EODHD_FUNDAMENTALS` existe mais ne contient aucun fichier à sa racine. Recherches `FUND02E` et `FUND03A` sans résultat. La présence des archives ne certifie pas leur contenu. Aucune archive historique n'a été réécrite, aucun collecteur dupliqué.

## Défaut reproductible

Le module existant `SCRIPTS_ACTIFS/preuves_ssi.py` levait une exception globale dans `registre()` lorsqu'une seule ligne avait `Date_verification_UTC` non interprétable. Cela interrompait le contrôle SSI de tous les dossiers, contrairement à la règle de quarantaine individuelle. Le traitement des remplacements appelait également `pd.Timestamp()` sur une date de remplacement invalide avant de vérifier la preuve, risquant le même blocage global.

## Correction

- Conserver les preuves à date invalide dans le registre pour audit et rejet individuel par `verifier()`, sans transformer une date absente en date valide.
- Écarter les preuves datées dans le futur lors de la lecture à date limite.
- Vérifier intégralement une preuve de remplacement **avant** de révoquer l'ancienne. Si la date historique est invalide, l'ordre chronologique ne peut être démontré : aucune révocation automatique.
- Préserver les contrôles d'identité, d'URL primaire, de SHA256, d'horodatage UTC explicite et de cohérence temporelle.

Les anomalies structurelles du registre (ID de preuve dupliqué, remplacement entre émetteurs différents) continuent à provoquer un arrêt de sécurité : elles ne sont pas silencieusement admises.

## Commits et tests

1. `b634987b61707f68dcd08871df87c70381c3d111` — correction ciblée de `preuves_ssi.py`.
2. `89a3377c81b37c3d241e7dd0531d54d7e7601356` — test fictif hors réseau `TESTS/test_registre_preuves_dates_invalides_non_bloquantes.py`.
3. `cca8c40fb8829921eaa61bb056d105c07693dbd0` — intégration du test dans `.github/workflows/test_reparation_microcaps.yml`.

Comparaison Git depuis le point de départ : trois commits et exactement trois fichiers modifiés ou ajoutés, aucun fichier portefeuille, aucun historique officiel.

CI complète sur `cca8c40f` : [run 41275946553](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41275946553) **success** ; l'étape `Ne pas bloquer les autres dossiers pour une date de preuve corrompue` est **success** (1er novembre 2026, 05:12 UTC). Les tests de la CI portent sur des fixtures et la non-régression, pas sur une qualification économique nouvelle.

Replays isolés déclenchés sur le même commit : [run 41275946574](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41275946574) et [run 41275951177](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41275951177). Leur conclusion doit être vérifiée avant d'être déclarée réussie.

## Limites et prochaine priorité

Dernier audit SSI disponible avant ce passage : 1 361 dossiers, zéro admission, 1 361 identités en quarantaine. Aucune preuve primaire supplémentaire, aucun score SSI/MCPA, aucun challenger ni arbitrage économique n'est déclaré validé par ce correctif. Les données historiques et la production `main` ne sont pas modifiées. La PR reste brouillon.

Étape suivante : certifier l'identité réglementaire et les deux preuves primaires SCE des candidats documentés, puis les transcriptions financières et les blocs SSI B4–B7 ; ne pas faire dépendre les autres dossiers des candidats `EN_ATTENTE_DATA`. Ne pas fusionner ni créer `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant validation complète.

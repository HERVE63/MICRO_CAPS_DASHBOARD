# Passage du 1er novembre 2026 — 07R, provenance temporelle des preuves SSI

## Périmètre et inventaire préalable

Branche isolée `repair/microcaps-chain-20261030`, PR brouillon #1. Base de comparaison : `205454cdfabab1917e2d230723889a96b6e5bd43` (dernier passage). `main` non ciblée.

Recherche Google Drive avant écriture : deux résultats nommés PRICE02A ; SEC_BRIDGE retrouvé avec les inventaires `ticker_cik_coverage.csv`, `sample_filings.csv`, `sample_companyfacts_coverage.csv`, `original_transition_investable_entries.csv` et autres archives ; recherches FUND02E et FUND03A sans résultat. L'indexation de ces dossiers n'est pas une certification de leur contenu ; aucune nouvelle collecte ou réécriture de ces archives n'a été entreprise. Réutilisation du module historique `SCRIPTS_ACTIFS/preuves_ssi.py` et de la CI existante.

## Défaut identifié et correctif

Le validateur de preuves `verifier()` utilisait `pandas.to_datetime(..., utc=True)` sur `Date_verification_UTC`. Cette conversion accepte silencieusement une date naïve ou un fuseau différent et leur attribue une représentation UTC. Une revue documentaire peut ainsi apparaître horodatée sans preuve d'une heure UTC explicite.

Ajout de `horodatage_verification_utc_strict()` : format ISO avec heure et suffixe `Z` ou `+00:00`, date réelle et décalage nul. La validation 07R refuse désormais les horodatages naïfs, date seule, fuseaux non UTC, `-00:00` et dates impossibles ; le contrôle historique des dates futures est conservé. La date de publication des documents peut rester une date civile (précision documentaire, sans prétendre à une heure publiée).

## Commits et contrôle de changement

1. `af35c9dd753e940d4e4feebd1c60d2f4a48ae1fd` : premier patch ; défaut d'échappement lors de la construction de la chaîne de remplacement, avec duplication involontaire du module. **Non validé**.
2. `b1a13f48fe1a79a1237cf24eb6f6822c60a5f3ca` : correction immédiate de cette duplication, reconstruction depuis le blob original et réapplication minimale. Contrôle : une seule définition `verifier()`.
3. `602007759e2e207e482a4a6c4f1a5b44f919d82b` : création du test de régression fictif, hors réseau.
4. `5286e0391bbd719fe11d93c32666a54ca965cb6b` : correction du test pour distinguer format UTC valide et horodatage futur interdit.
5. `70b6bfbe0583b4c666fde4622dedaca420310c8f` : ajout du test au workflow de réparation.

Comparaison Git depuis `205454cd` jusqu'à `70b6bfbe` : **5 commits, 3 chemins** (module de preuves, test, workflow CI). Aucune écriture sur `main`, le portefeuille réel, les 40 historiques officiels, CPI, ETF assurance-vie ou le coffre maître.

## Tests reproductibles et statut scientifique

- Test : `python -B TESTS/test_07r_horodatage_preuves_utc_hors_reseau.py`. Cas : `Z` et `+00:00` acceptés ; date seule, heure naïve, `+01:00`, `-00:00`, date impossible, champ vide rejetés ; futur interdit ; fichier brut SHA256 préservé.
- CI réparation : [run 41270799101](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41270799101).
- Replay isolé : [run 41270798935](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41270798935).
- À la rédaction de ce journal, ces deux runs sont **en cours**, donc non déclarés réussis. Contrôler leurs conclusions avant toute affirmation de validation.

Ce passage ne certifie aucune identité SCE, aucune transcription financière et aucun score SSI/MCPA. Aucun challenger ni arbitrage économique n'est promu. Les candidats incomplets restent `EN_ATTENTE_DATA`.

## Étape suivante

Vérifier les conclusions des runs et corriger toute régression. Ensuite, appliquer les contrôles documentaires aux preuves SCE indépendantes ICAPE/Fermentalg et aux autres dossiers sans inventer d'identité, puis compléter B4–B7. Le système reste incomplet ; **ne pas fusionner**, ne pas créer `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant validation bout en bout.

## Résultats CI contrôlés après exécution

Sur le commit de code/test/workflow `70b6bfbe0583b4c666fde4622dedaca420310c8f` :
- [CI complète 41270799101](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41270799101) : **success**, job `test` terminé. Étape `Rejeter preuves SSI sans heure de verification UTC explicite` : **success** ; contrôle intégrité CHASSE 31 352 détections, 07Q3, 07R et isolation historiques : **success**.
- [Replay isolé 41270798935](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41270798935) : **success**.
- [Second replay isolé 41270802405](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41270802405) : **success**.

Ces résultats valident les tests reproductibles sur fixtures et l'intégrité des contrôles prévus, **pas** l'existence de challengers qualifiés ou d'un arbitrage opérationnel sur données économiques réelles. Aucun ordre financier réel ni fusion sur `main`.

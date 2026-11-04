# MICRO CAPS — passage isolé du 2026-11-01, contrôle 10:42–10:45 UTC

## Reprise et inventaire préalable

- PR brouillon #1, branche `repair/microcaps-chain-20261030`, tête initiale `729a5eaadeb14df19a14ff90a5d1210ef679b748`.
- Réutilisation du module historique `SCRIPTS_ACTIFS/07Q3_RACCORDER_FAITS_FINANCIERS_NON_CERTIFIES.py` et de son test existant ; **aucun collecteur ni note créé**.
- Google Drive : `PRICE02A` retrouvé (parquet 9 558 146 octets et dossier raw_prices) ; `SEC_BRIDGE` retrouvé (archives CIK et dépôts) ; `DATA04_EODHD_FUNDAMENTALS` retrouvé mais vide à sa racine (liste de dossier contrôlée) ; aucune occurrence ciblée de `FUND02E` et `FUND03A` dans les résultats de recherche. Ne pas conclure à leur inexistence globale.
- Les transcriptions ICAPE et Fermentalg déjà archivées ont été réutilisées, avec leur URL, horodatage, chemin brut et SHA256. Aucune archive n'a été modifiée.

## Blocage critique traité

Le parseur `date_utc()` du raccordement financier 07Q3 acceptait tout fuseau explicite, puis convertissait silencieusement les dates en UTC. Ce comportement n'était pas cohérent avec les contrôles plus stricts de 07Q2 et 07R. Une date de provenance `+01:00` ne doit pas être acceptée comme une date *déclarée UTC*. Le contrôle de `Periode_cloture` acceptait aussi des heures et fuseaux via `datetime.fromisoformat(...).replace(tzinfo=UTC)` : cette conversion masquait une période comptable non civile.

**Correctif** : dates de publication et collecte acceptées uniquement en ISO 8601 avec heure complète et `Z` ou `+00:00` ; `Periode_cloture` acceptée uniquement sous la forme `AAAA-MM-JJ`, validée par le parseur. Une ligne non conforme reçoit `EN_ATTENTE_DATA_DATES` ; les autres continuent, sans admission ni notation.

## Commits, échecs et corrections

1. `55fec7882798fb2dbc2c8eabd859efd1da602f54` — premier correctif 07Q3. **Défaut de patch** : expression régulière écrite avec antislashs doublés, détecté après lecture de la branche. La CI `41298647421` a échoué sur ce commit ; il ne constitue pas une validation.
2. `9baae2fc46b5b5552854113ccc3129452de7e5a0` — correction des échappements de l'expression régulière ; la CI `41298655099` a réussi.
3. `237ff0005637f0c87ca4c8b943e34ba46f8213bb` — extension du test hors réseau existant : fuseaux non UTC, dates naïves, formats ambigus, date civile de clôture, quarantaine individuelle et maintien de 17 faits exploitables en piste lorsqu'un seul fait est invalide. CI complète `41298666695` **SUCCESS** ; replays isolés `41298671409` et `41298666698` **SUCCESS**.
4. Publications automatiques SSI : `e88218afb8be71518b573b8ea2fea198e0e346ff` puis `00589e53329804c28d9482140514f53c3ba9eb25`. La préparation SSI `41298655206`, sur le correctif `9baae2fc`, est **SUCCESS**. L'état de sortie final de cette préparation est vérifié, mais la réussite du workflow ne signifie pas admission économique.

Le diff entre la tête initiale et `237ff000` comprend exactement deux fichiers : module 07Q3 et test hors réseau. Aucun coffre, historique officiel, CPI ou ETF Assurance-Vie n'a été modifié. `main` reste à `ffd7a3b3c2889148fcea9d925ec59d1c089b12a2`.

## Résultat réel et limites

- `DONNEES/AUDIT_RACCORDEMENT_FAITS_SSI.csv` après préparation : **18 observations**, **2 émetteurs**, **0 observation certifiée**, **18 en attente de données**, **0 score attribué**. Les lignes restent `EN_ATTENTE_DATA_IDENTITE` malgré leurs archives SHA256 : l'identité SCE indépendante manque.
- `DONNEES/AUDIT_SSI.csv` du 2026-11-01T10:44:20.623838Z : **1 361 dossiers**, **0 admis**, **1 361 identités en quarantaine**. Aucune admission, aucun challenger SSI >= 65 / MCPA >= 80, aucun arbitrage économique réel validé.
- Les tests de quarantaine utilisent des dates et montants modifiés **uniquement sur copies temporaires**, sans mutation des 18 transcriptions officielles. Les données réelles ne sont jamais remplacées par ces fixtures.
- La PR reste brouillon, ouverte et non fusionnée. Aucune transaction financière réelle.

## Prochaine étape vérifiable

Certifier indépendamment les identités d'ICAPE et de Fermentalg à partir de documents primaires datés (deux URL et deux SHA distincts concordants), sans considérer les captures répétées comme indépendantes. Vérifier les 18 transcriptions chiffre par chiffre, puis compléter B4–B7. Poursuivre les autres candidats en `EN_ATTENTE_DATA` sans blocage global. Les duels 09B, le replay mensuel et les benchmarks doivent rester sous contrôles tant que les notes sont absentes. **Ne pas créer `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant la validation intégrale.**

## Liens d'exécution

- CI finale : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41298666695
- Replays : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41298671409 et https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41298666698
- Préparation SSI : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41298655206
- PR brouillon : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/pull/1

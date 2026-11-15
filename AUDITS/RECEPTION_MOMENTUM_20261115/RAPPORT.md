# Micro Caps — exécution Zonebourse du 15 novembre 2026

Branche : `repair/microcaps-chain-20261030`. Collecte dans le navigateur, puis exécution réelle du moteur 40M et des tests. La stratégie momentum 1/2/3 mois remplace ici le prérequis de notation MCPA ; les maîtres figés restent inchangés.

## Résultat actuel

Deux lectures complètes : Intellicheck et InfuSystem. Troisième page atteinte : One Stop Systems, arrêt sur « LIMITE QUOTIDIENNE GRATUITE ATTEINTE ». Les 37 autres pages n’ont pas été consultées après ce blocage. 38 lignes restent sans relevé complet ; elles n’ont aucun signal actuel inventé.

La date de consultation est le 15 novembre, dimanche. Les dernières clôtures vérifiées datent du vendredi 13 novembre 2026 à 22 h, heure affichée par Zonebourse. Aucun cours du 15 novembre n’est prétendu.

| Société | Clôture USD | Volume | 1 séance | 5 séances | 1 mois | 2 mois | 3 mois | Signal |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Intellicheck | 1.86 | 479914 | -16.96% | -8.82% | -19.13% | -28.46% | -50.40% | DIRECTION_BAISSIERE |
| InfuSystem | 14.72 | 144991 | -0.47% | +7.52% | +9.12% | +21.15% | +17.95% | DECELERATION_A_SURVEILLER |

Intellicheck passe de « décélération à surveiller » le 12 novembre à « direction baissière » le 13, calculé sur les clôtures lues. InfuSystem reste en décélération : dernière séance négative, cinq séances positives. Il ne s’agit pas d’une prévision de rendement.

Les variations mensuelles sont recalculées sur les dates calendaires exactes : 13 octobre, 11 septembre (le 13 est un dimanche), 13 août. Elles diffèrent des pourcentages synthétiques « 1 mois » / « 3 mois » affichés par Zonebourse. Les cours de référence et dates sont conservés dans la colonne Ancrages ; les pourcentages synthétiques ne remplacent pas les historiques.

## Réparations et vérification

40M consomme exclusivement les lectures du navigateur du passage. Il rejette les dates futures, les doublons contradictoires, l’identité divergente, les historiques sans ancrage exact et les données périmées au regard des séances de marché. Il distingue les pence des livres. Le classement commence par la dernière séance ; aucune mesure 6/12 mois n’intervient.

Le journal d’arbitrage est inchangé (SHA256 `8662c18842e2f06d8fabe714e5032a375b306102aee2691309ef9220e6b72e78`). L’intégrité des références T0 a été contrôlée. Deux replays identiques ne créent aucune opération. Aucun ordre réel et aucune modification de main ou d’un maître figé.

La préparation hebdomadaire comporte 40 lignes, avec un diagnostic partiel sur deux titres et les blocages des 38 autres. Aucune confrontation complète ni rotation n’est déclarée exécutée. Les frais vente 2,5 % puis achat 2,5 % représentent une friction de 4,878 % du capital. Le témoin n’est pas modifié ; une ancienne valorisation globale n’est pas présentée comme une valorisation Zonebourse actuelle.

La tâche ouvrée a été actualisée : lundi à vendredi vers 22 h 30 Europe/Paris. La revue du mardi conserve sa cadence et utilise désormais le momentum court pour Micro Caps ; la partie IAN est conservée. GitHub Actions recalcule les relevés poussés et vérifie séparément les tests logiciels et la couverture actuelle. L’accès authentifié à Zonebourse reste nécessaire pour achever les lectures.

## Reprise après connexion

Reprendre par OSS, puis les 37 lignes suivantes du fichier ETAT_INITIAL_PORTEFEUILLE_GERE.csv. Ne pas inventer d’URL de société : utiliser la recherche Zonebourse, contrôler ticker, ISIN et place. Les fichiers sources IDN.json et INFU.json montrent le format attendu. Consulter les dates d’ancrage via le calendrier de l’historique, jamais par requête cachée. Recalculer, tester, enregistrer les preuves et les sorties sur la même branche.

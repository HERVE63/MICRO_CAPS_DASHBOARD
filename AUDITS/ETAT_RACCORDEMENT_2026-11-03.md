# Audit de raccordement — 2026-11-03

- Portefeuille initial : 40 positions, 100 EUR par position.
- Journal des arbitrages : en-tête seulement, aucune opération.
- Paramètres : frais 2,5 % achat et vente, revue mardi, arbitrage mensuel.
- Orchestrateur quotidien V3 et modules 05/05C/05D présents.
- Collecte EODHD fondamentaux : refus HTTP 403 pour le pilote précédent.
- Pilote SEC US : 5 XBRL non certifiés, 0 note, 0 arbitrage.
- À démontrer : certification des données, notation MCPA/IPS, confrontation, décisions et transmission contrôlée au journal.

Aucune transaction ni notation n'est autorisée par ce document.

## Inventaire approfondi des modules existants
- Agent chasse : 07S, 07K, 08S, 08A, 07P et workflow chasse_hebdomadaire.yml.
- Agent qualification : 07Q, 07Q2, 07R, 07W, 08B ; controle des preuves SSI.
- Comité MCPA/IPS : 09_CONTROLE_REVUE_MCPA_IPS.py ; revue fail-closed.
- Confrontation : 09B_DUEL_PROCHAIN_EURO.py ; note destination strictement supérieure.
- Execution : 10_EXECUTION_MENSUELLE.py ; replay 05C ; rapport 11_RAPPORT_3_AGENTS.py.
- Audit global déjà présent : 08C_AUDIT_CHAINE_COMPLETE.py.

## Constat sur les fichiers de la branche de réparation
- SORTIE_SCREENER_CANDIDATS.csv : 5737 lignes de candidats détectés (non qualifiés).
- DOSSIERS_SSI_A_QUALIFIER.csv : 1361 lignes.
- RESULTATS_SSI.csv : 1361 lignes, dont 1355 EN_ATTENTE_DATA_IDENTITE_CIK et 6 MANQUANTE (lecture de la colonne Statut_SSI).
- CHASSE_CANDIDATS.csv : zéro octet.
- REVUE_HEBDOMADAIRE_MCPA_IPS.csv : en-tête seul, zéro note.
- DUELS_PROCHAIN_EURO.csv : absent.
- JOURNAL_ARBITRAGES_GERE.csv : en-tête seul.

## Priorité de réparation
1. Expliquer pourquoi l'adaptateur 08S / import 08A ne peuple pas CHASSE_CANDIDATS malgré le screener disponible.
2. Rapprocher les preuves primaires SEC déjà collectées via 07W et lever seulement les quarantaines d'identité réellement justifiées.
3. Exécuter 07R et 09 uniquement sur les dossiers complets, sans imputation.
4. Tester 09B puis 10 en dry-run; aucun journal officiel modifié avant validation.
5. Ne pas fusionner les branches divergentes automatiquement : 649 commits d'avance, 5 de retard sur main lors de la comparaison.

# Micro Caps — résultat effectif du 16 novembre 2026

**Chaîne non opérationnelle : collecte bloquée techniquement.**

- Relevés complets et frais validés : **0/40** pour ce passage.
- Une preuve Premium partielle de Broadpeak conservée : dernier cours affiché 1,645 EUR au 16/11/2026 11:40:40, dernière clôture 1,630 EUR au 13/11 et 1 199 titres. Historiques un et deux mois récupérés ; trois mois absent. Cette preuve n’est pas validée pour arbitrage.
- Les 15 relevés complets du 15 novembre restent conservés à leur date et ne sont pas réétiquetés comme actualisés.

## Tests réellement exécutés dans GitHub

[Exécution 43861938553](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/43861938553), commit `66399348e65961e6d261f25eef8ced742ddda7cb`.

| Contrôle | Résultat réel |
|---|---|
| tests/test_40m_momentum_experience_integration.py | **14 passed in 8.68s** |
| Intégrité T0 | Réussie |
| 40M_MOMENTUM_EXPERIENCE.py | Exécuté ; 40 lignes exportées, 0 lecture exploitable |
| Archivage et sauvegarde des calculs | Réussis |
| ZONEBOURSE_MOMENTUM_40_GATE.py | Échec, code 2 : 0/40, journal inchangé, arbitrage_autorise=false |

Résultats calculés sauvegardés par GitHub dans `eac4f6fa286301daae98a38e55b84ce64194f01a`. Empreinte journal : `8662c18842e2f06d8fabe714e5032a375b306102aee2691309ef9220e6b72e78`.

## Correction et blocages précis

La correction distingue le volume de la dernière séance terminée du volume cumulé en séance, conserve leurs dates et refuse leur absence. Le test utilise un cours intrajournalier sans bougie du jour et vérifie la conservation du volume de la dernière clôture. Aucun champ requis absent ne devient un signal négociable.

Le navigateur Work affiche Premium, mais les commandes expirent : « CDP operation exceeded its deadline before command dispatch ». Récupération d’onglet, lecture ciblée et contrôle visuel essayés ; réinitialisations du noyau. Aucun message anti-robot observé. L’onglet Broadpeak est conservé pour reprise. Les 39 autres lectures actuelles n’ont pas été effectuées après ce blocage. Le manifeste conserve les 40 statuts individuels. Aucun autre fournisseur utilisé.

Pulsar reste sous suspension documentée. Plejd présentait des cotations anciennes lors du passage antérieur ; aucune cotation actuelle n’a été substituée. La différence de symbole Growens/MAIL devra être validée par ISIN avant admission d’un nouveau relevé.

## Revue hebdomadaire et alertes

Le tableau des 40 sociétés et la préparation hebdomadaire sont générés ; la confrontation complète et les alertes actuelles sont **non validables**. Aucun changement de direction actuel n’est affirmé. Les anciens signaux restent historiques. Aucun arbitrage virtuel autorisé, aucune opération réelle. Témoin statique et journal inchangés. Paramètres : T0 01/10/2026, 4 000 EUR par portefeuille, frais 2,5 % par côté.

GitHub Actions assure les tests, calculs, classements des lignes admissibles, exports et archivage lors des dépôts de preuves. La collecte Premium reste une consultation du navigateur Work ; son fonctionnement sans intervention n’est pas déclaré validé. Branche de travail exclusivement ; main et maîtres figés inchangés.

[Tableau des 40](TABLEAU_40.md) · [Preuves du passage](../../DONNEES/ZONEBOURSE_NAVIGATEUR/2026-11-16/)

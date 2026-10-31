# MICRO CAPS — passage autonome 31/10/2026, 12:01 UTC : Fermentalg, source primaire et faits

**Résultat : une nouvelle publication financière d'émetteur capturée et neuf observations vérifiées, sans qualification SSI/MCPA.** Branche `repair/microcaps-chain-20261030`, PR brouillon #1. Aucune fusion, aucun ordre réel, aucun arbitrage virtuel non documenté.

## Inventaire obligatoire avant intervention

- `DONNEES/CHASSE_CANDIDATS.csv` non vide (5 429 763 octets au contrôle antérieur, 31 352 détections historiques selon test de référence). Cohorte SSI : 1 361 dossiers, qualification économique encore bloquée, **sans bloquer les collectes individuelles**.
- Scripts existants réutilisés : `07AA_COLLECTE_DOCUMENTS_OFFICIELS.py`, `07Q/07R`, `preuves_ssi.py`, parseur HTML de `TESTS/test_icape_faits_financiers_primaire_hors_reseau.py`. **Aucun collecteur ni parseur dupliqué.**
- Archive `AUDITS/SOURCES_OFFICIELLES/20261010T132940591629Z` : Hofseth `HBQ.F` déjà capturé, SHA256 `46b6b8b1fd0e73a6a18f1320c5dd457bd8f35499a1eacae3a06ff471c41801c6`. Réutilisation contrôlée par test hors réseau, sans nouveau téléchargement Hofseth. Fermentalg `1F6.F` avait échoué HTTP 403 sur PDF Actusnews.
- Google Drive : `PRICE02A` et `SEC_BRIDGE` retrouvés ; `DATA04_EODHD_FUNDAMENTALS` retrouvé en dossier ; `FUND02E` et `FUND03A` introuvables dans les recherches exactes. Aucun raccordement de données sans schéma, date et preuve.

## Blocage, repli et preuve acquise

1. Reprise du PDF Fermentalg via page HTML Actusnews datée du **06/10/2026 18 h CEST**. Exécution [41199092902](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41199092902) `success` **pour le workflow seulement** : audit `AUDITS/SOURCES_OFFICIELLES/20261031T115926642824Z/` = `BLOQUE_SOURCE`, HTTP 403, **zéro document**. Le vert du workflow ne vaut donc pas réussite documentaire.
2. Repli sur le **communiqué d'émetteur diffusé par Webdisclosure**, même date et même ISIN indicatif `FR0011271600` :
   https://www.webdisclosure.fr/press-release/fermentalg-epa-falg-half-year-results-2026-strict-financial-discipline-and-a-stronger-cash-position-to-enter-the-next-growth-cycle-from-the-best-possible-position-Bw4WtT9ba1B .
   Registre de reprise isolé `AUDITS/REPARATION/REGISTRE_REPRISE_FERMENTALG_20261031.csv`. Le collecteur historique 07AA a produit la capture du **31/10/2026 à 12:00:58.499540 UTC** : `AUDITS/SOURCES_OFFICIELLES/20261031T120058499540Z/`.
3. [Capture réussie 41199188505](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41199188505) : **1 document / 1 configuré, 0 source bloquée**, HTML brut, empreinte SHA256 `e6b16e996a4e2eac0bf88e94bdc7c56082798f35bb467707fc1abdd8f61b2f55`. Manifeste, audit et fichier brut publiés par commit automatique `954f7bcc`. Le test vérifie les octets, le contenu `FERMENTALG` + ISIN et la cohérence du manifeste. **Date de publication déclarée à confirmer indépendamment** ; pas de certification de l'identité de la cotation Yahoo `1F6.F`.
4. Pistes opérateurs consultées (non encore capturées ni certifiées) : Börse Stuttgart
   https://www.boerse-stuttgart.de/de-de/produkte/aktien/stuttgart/a1103m-fermentalg-eo---04
   et Deutsche Börse https://live.deutsche-boerse.com/aktie/fermentalg-eo-04 .
   Elles relient `symbol 1F6`, `WKN A1103M`, `ISIN FR0011271600`, mais le suffixe fournisseur `.F` et le lien exact à la place doivent encore être certifiés. La capitalisation Yahoo du 08/10 (`50 012 872 EUR`) diverge de la fiche Stuttgart consultée le 31/10 (`32,58 M EUR`) : **aucune substitution silencieuse**, dates et nombres de titres à rapprocher.

## Neuf observations transcrites et contrôlées

Fichier `AUDITS/REPARATION/FAITS_FINANCIERS_FERMENTALG_S1_2026_NON_CERTIFIES.csv`, unités **kEUR**, période arrêtée au 30/06/2026 sauf CA comparatif 30/06/2025. Source, publication, capture et SHA256 sont répétés sur chaque ligne.

| Poste du communiqué | Valeur source (kEUR) |
| --- | ---: |
| Chiffre d'affaires S1 2026 | 7 416 |
| Chiffre d'affaires S1 2025 comparatif | 7 605 |
| Résultat opérationnel avant paiements en actions et éléments non récurrents S1 2026 | -4 270 |
| Résultat opérationnel après paiements en actions et éléments non récurrents S1 2026 | -4 395 |
| Résultat net part groupe S1 2026 | -4 199 |
| Capitaux propres au 30/06/2026 | 31 906 |
| Dettes financières non courantes au 30/06/2026 | 3 622 |
| Dettes financières courantes au 30/06/2026 | 310 |
| Trésorerie et équivalents au 30/06/2026 | 10 785 |

Le test `TESTS/test_fermentalg_faits_financiers_primaire_hors_reseau.py` réutilise le parseur HTML existant et compare chaque ligne avec les cellules des deux tableaux du fichier brut archivé, en contrôlant SHA256, dates, période, unité et refus des notes. Aucun FCF extrapolé ni score inventé.

## Commits, CI et échecs

Comparaison depuis `b8305292` : **14 commits** (dont deux publications automatiques), exclusivement sur la branche isolée :
`c57d4c33`, `3933cf37`, `95408a62`, `0dfcd1b5`, `2c3fa00d`, `5fbcc746`, `1ecf6195`, `4a0fb204`, `a0ae367f`, `08d5d4de`, `954f7bcc`, `9ac3db72`, `52caa341`, `d3b02804`.

- [CI complète 41199328341](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41199328341) **success** sur `d3b02804`, incluant les deux nouveaux tests Fermentalg et les contrôles de non-mutation. Replays isolés [41199328293](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41199328293) et [41199331845](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41199331845) **success**.
- Exécutions intermédiaires `41199179518`, `41199179235` et `41199184664` **failure** pendant les mises à jour séquentielles de la configuration, du registre et du test ; `41199184654` **cancelled**. Elles ne sont **pas** comptées comme validations. Les corrections ont abouti à la CI finale ci-dessus.
- Aucun changement sous `DONNEES`, `HISTORIQUE`, `SAUVEGARDES`, `APPLICATION`, `index.html` ni `main` dans la comparaison du passage. Aucun titre qualifié automatiquement.

## Limites et prochaine action

Le nouveau document et les neuf chiffres sont des **observations documentaires**, pas une validation SCE. Capturer les fiches officielles de marché (identité seulement), dater et vérifier leurs empreintes, rapprocher `1F6.F` de l'instrument `FR0011271600`, puis traiter les exclusions et les sept blocs SSI, avant tout score MCPA/IPS ou duel 09B. Poursuivre en parallèle les autres dossiers `EN_ATTENTE_DATA` ; ne jamais imputer une note manquante. La sauvegarde `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` reste interdite jusqu'à validation bout en bout.

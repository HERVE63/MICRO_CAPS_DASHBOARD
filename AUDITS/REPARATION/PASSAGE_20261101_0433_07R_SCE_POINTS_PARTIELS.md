# MICRO CAPS — contrôle de réparation SSI 07R — 2026-11-01 04:33 Europe/Paris

## Périmètre et état de départ
- Dépôt : `HERVE63/MICRO_CAPS_DASHBOARD`, PR brouillon #1.
- Branche exclusive : `repair/microcaps-chain-20261030` ; base observée `edf1f0eb14b8acdd2261abc2cbedce6089b61865`.
- Comparaison initiale : **0 commit** depuis la dernière intervention. Aucune intervention sur `main`, historiques, portefeuille, CPI, ETF ou coffre maître.
- Inventaire Google Drive **avant modification** : `PRICE02A` (signaux mensuels et dossier `raw_prices`), `SEC_BRIDGE` (archives et correspondances SEC) retrouvés ; `DATA04_EODHD_FUNDAMENTALS` présent mais racine vide ; aucune correspondance exacte `FUND02E` ni `FUND03A` dans les recherches ciblées. Ces archives ne sont pas reconstituées.

## Blocage critique constaté
Le validateur `07R_VALIDER_NOTES_SSI.py` empêchait déjà toute **admission SSI** si l'identité SCE n'était pas certifiée, mais appelait `bilan_blocs_documentes` **avant** cette vérification : des points partiels et un plafond arithmétique pouvaient donc être affichés sur un dossier avec identifiant formel valide mais deux preuves SCE absentes ou invalides. Cela risquait de faire passer une piste documentaire pour une qualification.

## Correctif effectivement publié
1. Commit `22bdd2755d0dc9050c27bfbecc0cfab731551f60` : vérifier les preuves d'identité SCE avant de calculer les points partiels. Si la certification échoue, publier `Points_sur_blocs_documentes=0`, `Plafond_SSI_si_blocs_restants_maximaux=100`, `Portee_plafond=NON_CALCULE_IDENTITE_SCE`. L'état SSI reste non admis et les erreurs documentaires continuent d'être contrôlées.
2. Commit `e72cfab16367258fc76bff7ac3503271cceea58f` : expliciter la validation SCE simulée dans la fixture isolée CIK, qui n'utilise aucun document primaire.
3. Commit `ee6934602e8cff6d1041b4739c785775d15ee990` : tests adverses : identité SCE non validée malgré quatre blocs financiers contrôlés ; double preuve SCE valide ; seconde preuve supprimée ; recalcul des points uniquement après rétablissement de la double preuve.

Comparaison Git vérifiée : exactement **trois fichiers** modifiés, tous sous `SCRIPTS_ACTIFS/07R_...` et `TESTS/`. Aucune modification de donnée réelle, portefeuille, historique, branche `main`, ou coffre maître.

## Validation CI et statut scientifique
- CI de réparation déclenchée sur `ee693460` : run [41269737904](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41269737904).
- Replay isolé déclenché : runs [41269737875](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41269737875) et [41269741558](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41269741558).
- Lors de la rédaction, les runs sont **en cours**, donc **non déclarés réussis**. Le résultat final doit être contrôlé avant toute validation.
- Les tests utilisent des documents et notes **fictifs** ; aucun score économique réel ni preuve primaire n'a été certifié durant ce passage.
- 1 361 dossiers précédemment en attente de certification : ne pas déduire leur nouvel état de la seule couleur CI.

## Étape suivante
Vérifier les résultats complets de CI, puis relancer ou examiner les sorties SSI 07Q/07Q2/07Q3/07R, sans interpréter un workflow vert comme une admission. Certifier indépendamment les identités ICAPE/Fermentalg, puis les transcriptions, B4–B7 et le contrôle de chaque candidat. Continuer les dossiers valides et marquer les autres `EN_ATTENTE_DATA`. Aucun arbitrage ni sauvegarde totale tant que la chaîne scientifique complète n'est pas validée.

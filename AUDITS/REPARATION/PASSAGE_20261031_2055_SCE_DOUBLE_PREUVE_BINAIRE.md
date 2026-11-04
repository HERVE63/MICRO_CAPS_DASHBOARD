# MICRO CAPS — passage du 31 octobre 2026, 20:52–20:57 UTC

## État vérifié avant intervention

- PR #1 ouverte en brouillon ; branche `repair/microcaps-chain-20261030`, tête initiale `fc088208934a44e6f22937c150537f8087da3ad7`. Comparaison Git : **0 commit** depuis le passage précédent.
- Inventaire Google Drive effectué **avant toute édition** : `PRICE02A` et `SEC_BRIDGE` retrouvés ; recherches `FUND02E` et `FUND03A` sans résultat. Les modules existants `preuves_ssi.py`, `07AL`, `07Q`, `07R`, les registres et tests historiques ont été réutilisés, sans nouvelle collecte ni nouvelle brique concurrente.
- Registre CHASSE présent dans `DONNEES/CHASSE_CANDIDATS.csv` ; l'audit SSI publié indiquait 1 361 dossiers, **0 admis**, 1 361 identités en quarantaine. Le raccordement 07Q3 indiquait **18 faits**, 2 dossiers, 18 en attente, 0 score.

## Blocage critique corrigé

Le validateur SCE acceptait **deux URL différentes désignant le même document binaire** comme deux preuves d'identité indépendantes. Cela rendait possible une validation documentaire trompeuse même avec des octets identiques, tant que les deux enregistrements étaient marqués vérifiés.

La validation commune `preuves_ssi.verifier_identite_sce` et le sas US `07AL.appliquer_revues` exigent désormais **au moins deux URL distinctes ET deux empreintes SHA256 distinctes** pour les deux preuves d'identité SCE. Chaque document reste soumis à sa vérification individuelle : source primaire autorisée, émetteur, dates, fichier brut et empreinte. Le contrôle ne crée **aucune note**, ne transforme **aucune piste** en preuve vérifiée et ne certifie pas à lui seul l'indépendance juridique des éditeurs : une revue documentaire demeure indispensable.

## Commits de développement et tests

1. `e4b50becaa3c4de8f27b0fbf53fb054555eb6d91` : verrou SHA256 distinct dans `preuves_ssi.py`.
2. `aba65a23b15eeb2e10a57ae54ecdce1f9d3947e7` : même verrou dans le sas SCE US `07AL`.
3. `387717cf3a8f560c71c2a977a25eb6da04cf2759` : fixture non-US avec deux documents réellement distincts et contre-exemple de deux URL sur un seul binaire.
4. `95f3ebc9302e891f87cec10be2ab6fd81b740fc8` : adaptation des fixtures de quarantaine CIK pour porter des empreintes distinctes.
5. `2c67f260043f0d90ae4ac42e7eecd92ecbe5d728` : adaptation du test SSI de plafonnement à deux pièces d'identité distinctes.
6. `0f11bd6dfcde94cca7d994796f4dae96dfccb006` : fixture US avec deux documents distincts et refus explicite des deux URL à octets identiques.
7. `3f042b34d74471d45ddfefa8e0df29e9c15e0ca1` : ajout du test adversarial US à la CI principale.
8. Commit automatique ultérieur `5bfe423e8602ae851e7a2a45a1b0c39cfcf66a92` : mise à jour exclusive de `DONNEES/AUDIT_SSI.csv` par la préparation SSI, sans changement de production.

Les CI intermédiaires avant correction complète des fixtures ont échoué (notamment `41241049937`, `41241053205`, `41241068387`, `41241073203`). Elles ne sont pas présentées comme des validations. Après corrections : CI `41241080018` **success** sur `0f11bd6d` ; CI finale du code et de l'ajout de test `41241101356` **success** sur `3f042b34`, y compris les étapes de contrôle non-US et le nouveau test US. Replay isolé `41241101315` **success** sur `3f042b34`. Les runs `action_required` ne sont pas comptés comme succès.

## Périmètre et état fonctionnel

- Seuls deux scripts existants, quatre tests et le workflow CI ont été modifiés par les sept commits de développement. Le présent fichier est uniquement un journal de réparation.
- Aucune modification de `main`, des portefeuilles officiels, de `HISTORIQUE`, du coffre `MICRO_CAPS_DOSSIER_TRANSMISSION_V3_MAITRE`, de CPI ou d'ETF Assurance-Vie par cette intervention.
- Aucune transaction réelle, aucune nouvelle note SSI/MCPA, aucun challenger ni arbitrage économique déclaré validé. La PR demeure brouillon/non fusionnée.
- `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` **non créée** : la validation complète reste bloquée.

## Étape critique suivante

Confronter les preuves d'identité SCE des dossiers à des **documents primaires réellement indépendants**, avec identité émetteur/cotation, dates, provenance et SHA256 ; poursuivre les autres candidats en `EN_ATTENTE_DATA` sans bloquer l'univers. Ensuite seulement, vérifier les sept blocs SSI, les seuils SSI >=65 et MCPA/IPS >=80 et les duels 09B. Ne jamais déduire une admission d'une CI verte.

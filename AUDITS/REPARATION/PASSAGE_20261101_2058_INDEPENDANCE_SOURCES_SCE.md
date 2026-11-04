# MICRO CAPS — contrôle de l'indépendance minimale des sources SCE
Date d'intervention : 2026-11-01, 20:58 UTC. Branche isolée : `repair/microcaps-chain-20261030`. PR brouillon #1. État de départ vérifié : `488d64587155136c9fc0fa433f3879c1568dffaf`.

## Inventaire de réutilisation
- GitHub : réutilisation directe de `SCRIPTS_ACTIFS/preuves_ssi.py`, `07AL_RACCORDER_SCE_DISCOVERY_SSI_US.py`, des tests SSI existants et des archives primaires `AUDITS/SOURCES_OFFICIELLES/`.
- Google Drive : recherche ciblée `PRICE02A` (2 résultats), `SEC_BRIDGE` (1 résultat), `FUND02E` et `FUND03A` (aucun résultat exact). Absence de résultat de recherche ne signifie pas preuve de suppression.
- `DONNEES/CHASSE_CANDIDATS.csv` présent dans l'arbre Git (5 429 763 octets), non réécrit. `AUDIT_SSI.csv` avant intervention : 1 361 dossiers, zéro admis, 1 361 identités CIK en quarantaine (validation 20:45:36 UTC).
- Aucun fichier historique ni module PRICE02A/FUND/SEC/EODHD recréé.

## Anomalie et correctif
Avant correction, deux documents avec URL différentes et SHA256 distincts, mais servis depuis le même hôte (`issuer.example` et `www.issuer.example`), pouvaient satisfaire le critère de double source SCE. Ces documents ne démontrent pas deux sources indépendantes.
- `preuves_ssi.py` : nouvelle vérification `domaines_sce_distincts` des hôtes normalisés (www retiré) ; refus SCE si une seule origine, même avec deux URL et deux SHA256.
- `07AL_RACCORDER_SCE_DISCOVERY_SSI_US.py` : même verrou au raccordement amont SCE.
- Six tests existants ont été adaptés pour utiliser deux hôtes fictifs distincts, et deux assertions adverses rejettent désormais les doubles URL d'un même hôte. Les fixtures sont entièrement fictives, sans score réel.
- Limite explicitée : hôtes distincts = garde-fou minimal, non preuve complète de l'indépendance éditoriale/propriétaire. Revue primaire humaine/assistant identifiée, dates, empreintes et correspondance émetteur demeurent obligatoires.

## Commits de l'intervention
1. `5886eaa885ff08ca79c1e2b8091db489ba2b9691` — contrôle central SCE.
2. `791cc2d970941d83ae3a069da40c70d8b89d2f84` — raccordement 07AL.
3. `68a2b043c836326dc551a718c2f66c66d304c86a` — test première identité 07Q.
4. `04991ef05e10663c7189241d2a550f1d2c24964b` — test reprise identité 07Q.
5. `1fc3556c4a052d18d258f3656f4c990aef8a160d` — test 07R et refus même hôte.
6. `bb71c30842e6abd92a6899d012fb70d234fa682d` — test notes documentaires.
7. `863b18fafa15e6de5b6522b439e0c17a83445507` — test SCE amont et refus même hôte.
8. `2d87d3e8fdfbb0a33c56f7d588b2e632a0f122b6` — test quarantaine CIK.

## Validation et statut
À la rédaction initiale, CI complète `41349555360` et replay isolé `41349555341` sur le dernier commit étaient **en cours** : aucun succès anticipé. La validation n'est acquise qu'après consultation des conclusions effectives et des journaux d'échec éventuels.

Aucune admission SSI/MCPA ni transaction virtuelle nouvelle n'est revendiquée. Pas de modification de `main`, des historiques officiels, du coffre maître `MICRO_CAPS_DOSSIER_TRANSMISSION_V3_MAITRE`, de CPI ou ETF Assurance-Vie. Aucune transaction financière réelle. Pas de sauvegarde finale `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant validation intégrale.

## Étape suivante
Vérifier CI/replay sur commit final, corriger les éventuelles régressions, puis certifier les correspondances émetteur/ISIN–ticker sur pièces primaires réellement indépendantes et horodatées. Laisser les dossiers incomplets `EN_ATTENTE_DATA` sans bloquer les autres.

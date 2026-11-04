# MICRO CAPS — passage du 1er novembre 2026, 11:19–11:23 UTC

## Reprise réelle et réutilisation obligatoire

- PR brouillon #1, branche isolée `repair/microcaps-chain-20261030`. Tête initiale `c7c1002cc23a35a94b38174eb9b6cb22cc6be929`; comparaison Git : **aucun changement depuis le passage précédent**.
- Inventaire Google Drive avant modification : PRICE02A (table et dossier) et SEC_BRIDGE (dossier) retrouvés ; FUND02E et FUND03A non retrouvés par recherche ciblée ; EODHD présent en dossier. Aucune absence globale inférée.
- Modules historiques réutilisés : `07AA_COLLECTE_DOCUMENTS_OFFICIELS.py`, `07Q2_AUDIT_PREUVES_SSI.py`, `07R_VALIDER_NOTES_SSI.py` et test `test_fermentalg_fiche_marche_sha256_hors_reseau.py`. **Aucun nouveau collecteur, aucune note, aucune transaction**.

## Blocage traité et opération réalisée

La fiche Deutsche Börse établissait seulement une piste pour `1F6.F`, avec publication inconnue. Ajout d'une **seconde source primaire de marché indépendante**, la fiche de transfert Euronext Growth de Fermentalg : `https://live.euronext.com/en/ipo-showcase/fermentalg-0`. Cette page établit `FERMENTALG / FR0011271600 / ALGAE` pour la place de Paris ; elle ne prouve pas à elle seule le suffixe fournisseur `.F`. La date du transfert (16 avril 2024) **n'a pas été transformée en date de publication** de la page, laquelle reste `INCONNUE`.

- `a89056caf668d2aabaf33cec00b2d77cb8b4e60a` : ajout d'une ligne au registre de collecte Fermentalg isolé, sans modifier les registres historiques.
- Les workflows du commit intermédiaire ont échoué, car l'ancien test exigeait exactement une source : `41301463298` (collecte) et `41301463352` (CI). **Échecs non comptabilisés comme validations**.
- `a8dc7aa7691639504b0c05dd5ab2748accacd034` : adaptation du test existant à deux sources, contrôles des deux domaines et des empreintes, vérification de `ALGAE` sur Euronext et de `1F6` sur Deutsche Börse ; repli explicite `BLOQUE_SOURCE` si Euronext devient inaccessible, sans note.
- `dd03864678be786b6659555c49ab7670d324980b` : publication automatique **réussie** de l'audit et des deux captures primaires par le workflow `41301497928`.

## Preuves collectées et vérifications

Archive **réelle**, publiée uniquement sur la branche isolée :
`AUDITS/SOURCES_OFFICIELLES/20261101T112119040817Z/`.

- Deutsche Börse, `1F6`, ISIN `FR0011271600` : SHA256 `b9d880ae4ecea8b36e580e0fa4aabd11da24f70aa8067aebc93a6faa43af1ec0`.
- Euronext Growth, `ALGAE`, ISIN `FR0011271600` : SHA256 `c1dd1d0a467ca41d5fabea9f0959a3e40a31159d3bb4697e0390e2c0efa9f86b`.
- Capture UTC commune : `2026-11-01T11:21:19.040817+00:00` ; 2 documents capturés, 0 source bloquée, 0 note attribuée. `MANIFESTE.json` contrôle le SHA256 du registre, de la couverture, des audits et des octets des deux documents.
- Test de capture du workflow `41301497928` : **SUCCESS**. CI complète `41301497929` : **SUCCESS**. Replay virtuel isolé `41301497949` : **SUCCESS**.
- SSI régénéré par `41301530694` : **SUCCESS**. Audit `DONNEES/AUDIT_SSI.csv` daté du `2026-11-01T11:22:19.324234+00:00` : 1 361 dossiers, 0 admis, 1 361 identités en quarantaine. `07Q3` : 18 observations financières, 2 émetteurs, 18 en attente, 0 score.
- File de certification 07Q2 : Fermentalg `1F6.F` possède désormais **8 captures, 7 couples URL–SHA256 uniques, 3 URL et 3 domaines**, mais `Identifiant_dossier_source=MANQUANTE`, `Statut_certification=PISTES_NON_CERTIFIEES`. Ne pas considérer les répétitions comme indépendantes.

## Protection, portée et suite

- Les documents Euronext/Deutsche Börse sont des **pistes d'identité**, pas des validations SCE, des preuves financières, ni des scores SSI/MCPA. L'absence de date de publication des pages de marché interdit de prétendre à une preuve rétrospective datée.
- `main` observée à `ffd7a3b3c2889148fcea9d925ec59d1c089b12a2` ; PR ouverte, brouillon et non fusionnée. Aucune modification volontaire des coffres, historiques, CPI, ETF Assurance-Vie, ni aucun ordre réel.
- Prochaine priorité : rapprochement indépendant de l'ISIN et des deux places avec publication datée de l'émetteur ; certification réglementaire SCE après vérification des conditions du protocole ; contrôle chiffre par chiffre des 18 transcriptions et blocs B4–B7. Tous les autres dossiers incomplets restent `EN_ATTENTE_DATA` et continuent sans bloquer le traitement.
- **Interdiction maintenue** de créer `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant validation complète de la chaîne.

## Liens vérifiables

- Collecte : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41301497928
- CI : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41301497929
- Replay : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41301497949
- Préparation SSI : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41301530694
- PR : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/pull/1

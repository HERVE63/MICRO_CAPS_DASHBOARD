# MICRO CAPS — reprise autonome du 31 octobre 2026, 10:32 UTC

**Statut : collecte documentaire supplémentaire RÉELLE, qualification économique EN_ATTENTE_DATA.** Travail exclusivement sur `repair/microcaps-chain-20261030`, PR brouillon #1. Ne pas fusionner. Aucune transaction financière réelle ou virtuelle. Aucun score, aucune preuve SCE certifiée, aucun challenger admis.

## Inventaire historique avant modification

- GitHub : registre `DONNEES/CHASSE_CANDIDATS.csv` non vide ; modules historiques `07AA_COLLECTE_DOCUMENTS_OFFICIELS.py`, `preuves_ssi.py`, `07Q` et `07R` réutilisés. Capture antérieure ICAPE : `AUDITS/SOURCES_OFFICIELLES/20261031T094048100672Z/` (deux pages sans date de publication).
- Google Drive : `PRICE02A/PRICE02A_MONTHLY_SIGNALS.parquet` (9 558 146 octets), `SEC_BRIDGE`, `DATA04_EODHD_FUNDAMENTALS` localisés. Recherche exacte `FUND02E` et `FUND03A` sans résultat. **Aucun raccordement** de ces archives sans vérification du schéma, des dates et des preuves.

## Sources primaires additionnelles réellement acquises

Capture GitHub Actions [41193084442](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41193084442), exécution `success`, répertoire `AUDITS/SOURCES_OFFICIELLES/20261031T103236976336Z/`, publication automatique commit `7234e0cfb1e42170daf528c07a70d3081da63f6b`.

1. Rapport financier semestriel ICAPE 2026, PDF **42 pages**, [émetteur](https://www.icape-group.com/wp-content/uploads/2026/10/ICAPE-GROUP-RFS-30.06.2026-VF_vdef.pdf), daté **08/10/2026** dans l'[index officiel de documentation](https://www.icape-group.com/fr/documentation/). Capture **31/10/2026 10:32:36 UTC**. SHA256 des octets bruts : `549ce7bd618afe3c8fab56a33898566e6e3ad9272fb05527e78989d860e7ad96`. Date déclarée à vérifier indépendamment ; date de signature du rapport 30/09/2026 distincte de la publication.
2. Communiqué résultats S1 2026, [Euronext / diffusion de l'émetteur](https://live.euronext.com/en/ajax/node/company-press-release/12913664), daté **01/10/2026 à 07:45 CEST** (05:45 UTC). Capture **31/10/2026 10:32:36 UTC**. SHA256 : `05605e38d3a3e9778d3d8468b613752fe54ef2bbe529bd109b5c622824b0669c`.
3. Les deux pages historiques d'identité ont été recapturées : émetteur SHA256 `3456548fb514b0bceb2f8a7d865b7dde1f21716bd5fd3b1abdc2c0ce1761a395` et Euronext IPO SHA256 `e17a69ac2f4dbcc1670c95f206c2c6cfc791b044f7d667156a97d363c49e1ae6`. Leurs **dates de publication restent inconnues**.

Les quatre lignes portent `Z8J.F` et l'ISIN indicatif `FR001400A3Q3`, sans présumer la certification du lien entre la cotation allemande et l'émetteur. Le registre conserve l'URL, le type, la date déclarée, la source de cette date, la date de capture, l'URL finale et le SHA256. La vérification CI contrôle les octets des quatre captures et les empreintes du manifeste. Le PDF est contrôlé par signature `%PDF-` et taille, **pas** par une recherche binaire d'ISIN dans du contenu PDF compressé.

## Commits, tests, échecs et correctifs

- `7b1fb37f` : ajout des deux sources officielles datées dans le registre de collecte, sans score. Première capture [41193052660](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41193052660) **failure** : le workflow précédent exigeait encore deux documents (`assert len(df)==2`) alors que le registre en comportait quatre ; aucune donnée de production altérée.
- `77709481` : workflow corrigé pour quatre sources, vérification du PDF, des pages HTML, des SHA256, du manifeste et de la non-promotion ; exécution intermédiaire [41193067797](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41193067797) **cancelled** par l'ordonnanceur concurrent, non comptée comme validation.
- `2e53ea47` : test hors réseau renforcé sur les quatre sources, leurs dates et leur provenance ; [CI complète 41193084555](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41193084555) **success**, [replay isolé 41193084409](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41193084409) **success**.
- `7234e0cf` : commit automatique des quatre documents bruts, `AUDIT_DOCUMENTS.csv`, `COUVERTURE.csv` et `MANIFESTE.json` ; comparaison Git depuis `2e53ea47` : **sept fichiers ajoutés exclusivement sous AUDITS/SOURCES_OFFICIELLES**.

Manifeste : **4 configurés, 4 collectés, 0 source bloquée, 2 publications datées à vérifier, 2 publications inconnues, 1 361 dossiers univers, 1 360 sans source configurée, 0 note attribuée, couverture incomplète**. Le workflow vert certifie uniquement la capture et l'intégrité, jamais la qualification SSI/MCPA.

## Prochain blocage prioritaire

Contrôler de manière indépendante la date de publication et la correspondance `Z8J.F`/émetteur/ISIN, puis extraire les données financières du rapport avec pages, périodes, unités, normes comptables et empreintes de source. Inscrire les revues SCE append-only **seulement** lorsque tous les contrôles sont satisfaits ; faire passer les sept blocs SSI, les exclusions, puis MCPA/IPS avant tout duel 09B. Tous les autres dossiers restent `EN_ATTENTE_DATA` sans interrompre leur collecte. Le coffre `MICRO_CAPS_DOSSIER_TRANSMISSION_V3_MAITRE`, les historiques, CPI, ETF AV et `main` sont exclus des écritures. La sauvegarde `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` est **interdite** tant que la validation intégrale n'est pas acquise.

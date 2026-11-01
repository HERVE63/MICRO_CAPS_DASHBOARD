# Passage autonome — 2026-11-01 08:11–08:18 Europe/Paris — vérification textuelle des identités sur archives primaires

## Reprise et inventaire avant développement

PR brouillon #1, branche isolée `repair/microcaps-chain-20261030`, tête de départ `6e6a35435368869432fdfb038a2bc3b14267315f`. `main` était `d86124b648222eab0cef1090980cd95d71dbd417`. Archives Google Drive inventoriées AVANT édition : PRICE02A (parquet de signaux mensuels de 9 558 146 octets et dossier raw_prices), SEC_BRIDGE (archives CIK, filings, companyfacts) retrouvés ; FUND02E et FUND03A non retrouvés par recherche ciblée. Réutilisation des captures 07AA et de l'indexeur 07Q2, sans nouveau collecteur, sans écriture dans les archives.

## Développement effectif

Le module existant `SCRIPTS_ACTIFS/07Q2_AUDIT_PREUVES_SSI.py` contrôle déjà les manifestes et les SHA256 des octets bruts. Il produit maintenant, en plus de la file agrégée, `DONNEES/CONCORDANCES_IDENTITE_BRUTS_NON_CERTIFIEES.csv`. Pour les captures HTML/texte déjà vérifiées, il recherche l'ISIN déclaré dans les octets archivés et, pour une fiche de marché, la chaîne exacte `Symbol: <ticker_local>`. Chaque ligne conserve ID de document, type, URL, chemin brut, SHA256, dates déclarées, date de collecte et statut NON CERTIFIÉ. Les documents PDF restent explicitement NON ANALYSÉS, les CIK ne sont pas prétendument vérifiés, et deux captures identiques URL+SHA256 ne deviennent jamais deux sources. Aucune note n'est attribuée.

**Sortie réellement publiée :** 29 captures URL+SHA256 distinctes (contre 49 captures indexées avant déduplication), dont 16 avec ISIN déclaré présent dans le texte archivé, quatre avec symbole de marché exact ; les 29 restent `Identite_SCE_certifiee=NON` et `Note_SSI=MANQUANTE`. Répartition : 1F6.F 5, Z8J.F 12, BMBN.US 4, CPKF.US 3, STBI.US 3, UNIB.US 2. Les autres candidats ne sont pas bloqués.

## Rapprochements documentaires vérifiés, sans certification SCE

- **Fermentalg 1F6.F** : fiche Deutsche Börse du 31/10/2026, archive `0b0cec4aa4275668eca11eda86659971389ee45f42e465e5a818e6d30527e904`, contenu HTML `FERMENTALG ... FR0011271600` et `Symbol: 1F6` ; URL https://live.deutsche-boerse.com/equity/fermentalg-eo-04. La date de publication de cette fiche reste **INCONNUE** (collecte 2026-10-31 17:31:26 UTC). Deuxième URL, communiqué Fermentalg sur Webdisclosure daté 2026-10-06 16:00 UTC, archive `492c9c030ec1eacf4dda899bf63126f146d2959c87c91d4f0d00904be568b263`, contient l'ISIN FR0011271600. Il ne mentionne pas le symbole francfortois 1F6.
- **ICAPE Z8J.F** : fiche Deutsche Börse du 31/10/2026, archive `9fe2d9b02b8d42055e92f8d7159e4dee6bc083aa0b4567e5e7ee51068b2c8dcc`, HTML `ICAPE HOLDING ... FR001400A3Q3` et `Symbol: Z8J` ; URL https://live.deutsche-boerse.com/equity/icape-holding-eo-40. Date de publication **INCONNUE** (collecte 2026-10-31 23:16:41 UTC). Le communiqué ICAPE sur Euronext daté 2026-10-01 05:45 UTC, archive `05605e38d3a3e9778d3d8468b613752fe54ef2bbe529bd109b5c622824b0669c`, contient l'ISIN FR001400A3Q3. La page investisseurs de l'émetteur, archive `1f2d7ee82deaf0479be0a66f78996ffcf89f3fc36cac3b2bd11576e6bfaefbde`, affiche `FR001400A3Q3 / ALICA` (symbole Euronext, pas Z8J) ; date de publication inconnue.

Ces concordances de chaînes sont des **indices factuels** dans les captures déjà collectées, pas une certification réglementaire : indépendance éditoriale, chronologie des publications et rattachement historique de cotation restent à examiner. Ne pas traiter le même communiqué relayé par Euronext et l'émetteur comme deux preuves indépendantes. Le validateur 07R exige toujours deux preuves SCE datées, vérifiées, de SHA et URL distincts. Aucun nouveau score SSI, MCPA, challenger ni arbitrage.

## Commits, échecs et vérifications

Commits de code et de publication : `08784ceb` (indexeur), `504978dd` (première correction regex), `4ac34403` (tests adverses), `33dc6c56` (publication Git), `62e2d97f` (correction finale regex), et commits automatiques SSI `58d28ce5`, `b98e6da6`, `56acbe14`. Comparaison de `6e6a3543` à `56acbe14` : huit commits, cinq fichiers touchés (script 07Q2, test, workflow et deux sorties SSI) ; aucun coffre, historique officiel, portefeuille réel ou fichier `main` modifié.

La CI `41283975153` a **échoué** sur l'assertion du symbole de marché : la borne finale de regex avait été écrite avec un antislash surnuméraire. Corrigée au commit `62e2d97f`. La CI complète `41284067389` a ensuite **réussi**, tout comme les deux replays virtuels isolés `41284067420` et `41284070768`, et la préparation SSI `41284067382`. Les runs `action_required` des commits automatiques ne valent pas preuve de succès.

Liens de contrôle : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41284067389 ; https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41284067382 ; https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41284067420 ; https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41284070768 .

## Prochain blocage réel

Pour 1F6.F et Z8J.F, trouver et archiver via 07AA **une preuve primaire indépendante avec date de publication vérifiable** du lien ISIN ↔ symbole francfortois, ou établir une chronologie documentaire admissible sans inventer la date de la fiche web. Ensuite effectuer une revue de contenu et provenance distincte de la collecte, et seulement si les conditions 07R sont démontrées renseigner les preuves append-only. Vérifier séparément les 18 transcriptions financières existantes ; les blocs B4–B7 restent à documenter. Tous les dossiers incomplets demeurent EN_ATTENTE_DATA. Ne pas créer la sauvegarde finale, ne pas fusionner, ne pas négocier d'actifs réels.

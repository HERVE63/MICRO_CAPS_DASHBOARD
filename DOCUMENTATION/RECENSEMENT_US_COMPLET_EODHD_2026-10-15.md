# Recensement américain complet via EODHD — 15 octobre 2026

## Correction de périmètre

L'objectif est de recenser l'ensemble des microcaps du marché américain disposant de données publiées, et non de rester dans les 172 pistes tirées du précédent fichier de cotations allemandes. Le nouveau recensement part du **catalogue US complet EODHD**, indépendamment des 172 et des 1 361. Les pièces SEC déjà acquises restent conservées et réutilisables. Le T0 et les positions ne sont pas modifiés.

## Méthode exécutable

`07AH_RECENSER_MICROCAPS_US_EODHD.py`, raccordé au workflow `recensement_us_eodhd.yml` :

1. Contrôle la clé et les quotas réels de l'abonnement. Réserve 10 000 crédits pour les autres outils et ne dépasse pas 30 000 crédits estimés dans une exécution. Aucun achat ou supplément automatique. Un quota insuffisant provoque un arrêt documenté, pas un univers déclaré complet.
2. Télécharge le catalogue complet des cotations actives US, sans limite à un sous-ensemble existant.
3. Obtient le dernier cours EUR/USD disponible avant le jour de collecte et conserve sa date. La tranche de **50 à 300 M€** est convertie en USD pour interroger le fournisseur, puis contrôlée de nouveau en EUR dossier par dossier.
4. Interroge le screener sur toute la tranche. Une requête saturant 1 000 résultats est subdivisée en tranches de capitalisation disjointes, jusqu'à obtenir des pages terminales. Aucun plafond 172, Top100 ou Top1000 n'est accepté comme recensement exhaustif. Les doublons de pagination et la saturation d'une valeur unique bloquent l'achèvement.
5. Contrôle les types d'instruments, devises, dates et capitalisations. Les cas ambigus restent distincts des rejets financiers ; aucun filtre de rentabilité, croissance ou momentum arbitraire n'est ajouté au recensement.
6. Contrôle l'accès aux fondamentaux EODHD avec AAPL.US, puis collecte les fondamentaux complets des candidats si les droits et quotas le permettent. Un refus HTTP 401/403 sur ce contrôle déclenche le repli vers la SEC, sans répéter le refus sur tous les titres.
7. Distingue **marché de cotation US** et **origine de l'émetteur**. Le champ EODHD `General.CountryName` décrit le pays de la place selon le glossaire fournisseur : il ne valide donc pas l'origine américaine. Les CIK disponibles sont rapprochés des profils officiels SEC ; immatriculation, adresse et type d'émetteur sont contrôlés avec le module d'origine déjà testé. Les cas sans preuve restent à clarifier.
8. Rapproche les tickers du registre officiel SEC, sans recherche approximative ni exclusion fondée sur une lettre du ticker. Un CIK fournisseur vide ou nul n'est pas une contradiction ; un CIK positif réellement divergent bloque le rapprochement. Les `companyfacts` sont recherchés pour tous les CIK résolus, y compris les émetteurs étrangers ou d'origine à préciser.
9. Après la collecte, `07AI_RACCORDER_COMPTES_US_SSI.py` relit les seules archives financières officielles SEC, vérifie leurs empreintes et réutilise réellement 07U, 07V et 07W : extraction, contrôle des périodes/unités et rapprochement documentaire avec les blocs SSI. Les sorties sont isolées dans `AUDITS/QUALIFICATION_US/`. Les candidats non documentés restent dans le tableau de couverture. Aucun fichier de données de production, preuve humaine ou portefeuille n'est écrasé.

Les fondamentaux EODHD sont une source fournisseur secondaire. Leur collecte ne vérifie pas automatiquement les sept blocs SSI, ne transforme pas un pourcentage d'insiders en dirigeants investis vérifiés et ne produit aucune admission.

## Sources et protection

Les réponses, catalogues, résultats normalisés et fondamentaux sont conservés **chiffrés** dans `AUDITS/RECENSEMENT_US_EODHD/`, avec index sans token et empreintes. Les données fournisseur ne sont pas publiées en clair dans le dépôt. Le déchiffrement nécessite la clé EODHD utilisée lors de l'archivage ; elle n'est ni sauvegardée ni affichée. Les réponses du même jour peuvent être réutilisées après contrôle des archives et déchiffrement authentifié, en conservant leur date de collecte.

Les bilans publics ne contiennent que l'état d'exécution, les métriques de couverture, la pagination, les quotas non personnels et les blocages. Les noms, adresse e-mail, données de paiement et jetons d'invitation du compte EODHD ne sont pas archivés.

Références techniques primaires :

- https://eodhd.com/financial-apis/covered-tickers-eodhd
- https://eodhd.com/financial-apis/stock-market-screener-api
- https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds
- https://eodhd.com/financial-academy/financial-faq/fundamentals-glossary-common-stock
- https://eodhd.com/financial-apis/user-api
- https://eodhd.com/financial-apis/api-limits

## Contrôles d'accès et recensement effectivement exécutés

Le blocage initial de clé absente est conservé dans [38763331997](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38763331997) et `AUDITS/ACCES_EODHD/RUN_38763331997/STATUT.json`. L'exécution [38764364040](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38764364040) avait effectivement passé 18 fichiers de tests puis arrêté le collecteur sur cette absence. Ces anciens échecs ne décrivent plus l'état d'accès actuel.

Le secret créé dans MICRO_CAPS porte le nom `EODH_API_KEY`. Les deux workflows d'accès et de collecte acceptent désormais ce nom ainsi que `EODHD_API_KEY`, tout en transmettant au script la variable canonique `EODHD_API_KEY`. La première clé correspondait à une limite de 20 appels ; après remplacement par l'utilisateur, l'abonnement renvoie une limite de **100 000 crédits par jour**. Aucun fichier ni secret CPI ou Assurance-Vie n'a été modifié.

La deuxième tentative de [38770708991](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38770708991), audit `20261015T165157408909Z`, a effectivement recensé :

| Contrôle | Résultat observé |
|---|---:|
| Inscriptions du catalogue US actif EODHD, tous instruments | 50 997 |
| Actions ordinaires du catalogue | 17 805 |
| Résultats du screener dans les tranches interrogées | 2 674 |
| Cotations ordinaires conservées dans la tranche 50–300 M€ | **2 490** |
| Cas hors bande ou à revoir | 184 |
| EUR/USD utilisé | 1,11945 au 14 octobre 2026 |

Ces nombres constituent un recensement fournisseur au 15 octobre, **pas une reconstitution de l'univers au T0 du 1er octobre**, ni un nombre d'émetteurs américains uniques validés. Les classes d'actions et les origines restent à rapprocher. Les 184 cas écartés du périmètre mécanique ne sont pas des rejets pour mauvaise qualité financière.

L'API des fondamentaux EODHD renvoie HTTP 403, confirmé également sur le contrôle AAPL.US. Ce droit d'accès n'est donc pas supposé acquis malgré la limite de 100 000 crédits. La SEC reste la source officielle de repli, sans achat d'extension d'abonnement.

L'exécution [38773567471](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38773567471) a fini techniquement en vert mais produit **zéro dossier SEC** : un CIK fournisseur manquant était transformé en zéro puis comparé à tort au CIK officiel. Ce résultat est invalidé comme preuve d'enrichissement. La correction `f81076835584705e5813e94522b91e79e5ece917` ajoute la régression correspondante, rend les erreurs visibles et empêche ces erreurs d'identité de produire un succès silencieux. La reprise effective est [38774469065](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38774469065).

Le raccordement est publié dans `ea3cf8f5fb31179fc69b7d2754fcfc6c78a2a5d9`. La réception [38775166167](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38775166167) passe effectivement les **20 fichiers de tests hors réseau**. Le test de pagination utilise 1 400 titres fictifs : il contrôle le programme et ne compte pas comme données de marché.

## Couverture scientifique

Les dénominateurs seront les nombres réellement recensés, dédoublonnés et contrôlés, pas les 172 du pilote. Le minimum de 50 % et la cible de 90 % concernent des dossiers effectivement évaluables au SSI. Le nombre de réponses fournisseur, de fichiers téléchargés ou de candidats dans la tranche ne constitue pas cette couverture vérifiée.

Le catalogue et le screener du fournisseur ne démontrent pas à eux seuls que toutes les sociétés américaines publiant des comptes sont couvertes. Les trous de capitalisation, les origines inconnues et les cotations non rapprochées restent à auditer. Une sélection mondiale ou américaine complète ne sera pas proclamée à partir d'un résultat tronqué ou partiel.

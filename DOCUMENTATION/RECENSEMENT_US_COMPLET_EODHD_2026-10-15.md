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
6. Collecte les fondamentaux complets des candidats avec l'abonnement, si les droits et quotas le permettent, et contrôle le code du titre retourné. Une absence de droit HTTP 401/403 arrête la collecte plutôt que de répéter le même refus sur tous les titres.
7. Distingue **marché de cotation US** et **origine de l'émetteur**. Le champ EODHD `General.CountryName` décrit le pays de la place selon le glossaire fournisseur : il ne valide donc pas l'origine américaine. Les CIK disponibles sont rapprochés des profils officiels SEC ; immatriculation, adresse et type d'émetteur sont contrôlés avec le module d'origine déjà testé. Les cas sans preuve restent à clarifier.

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

## Contrôle d'accès effectivement exécuté

Le workflow [38763331997](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38763331997) confirme : **`EODHD_API_KEY` n'est pas disponible dans MICRO_CAPS_DASHBOARD**. Le statut est sauvegardé dans `AUDITS/ACCES_EODHD/RUN_38763331997/STATUT.json`. Aucun résultat EODHD ni nombre total de microcaps US n'est donc annoncé à ce stade.

La variable portant ce nom est référencée par le workflow CPI, consulté en lecture seule. Aucun fichier ni secret de CPI n'a été modifié. Un secret GitHub chiffré d'un autre dépôt ne peut pas être relu par ce connecteur pour le recopier.

Pour ouvrir l'accès au collecteur prêt à exécuter, ajouter la clé existante en secret de dépôt `EODHD_API_KEY` dans MICRO_CAPS_DASHBOARD, puis lancer le workflow **MICRO CAPS - RECENSEMENT US COMPLET EODHD**. La clé ne doit pas être collée dans la conversation.

## Couverture scientifique

Les dénominateurs seront les nombres réellement recensés, dédoublonnés et contrôlés, pas les 172 du pilote. Le minimum de 50 % et la cible de 90 % concernent des dossiers effectivement évaluables au SSI. Le nombre de réponses fournisseur, de fichiers téléchargés ou de candidats dans la tranche ne constitue pas cette couverture vérifiée.

Le catalogue et le screener du fournisseur ne démontrent pas à eux seuls que toutes les sociétés américaines publiant des comptes sont couvertes. Les trous de capitalisation, les origines inconnues et les cotations non rapprochées restent à auditer. Une sélection mondiale ou américaine complète ne sera pas proclamée à partir d'un résultat tronqué ou partiel.

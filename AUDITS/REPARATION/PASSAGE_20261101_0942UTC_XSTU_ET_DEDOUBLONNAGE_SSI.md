# MICRO CAPS — intervention isolée du 2026-11-01, contrôles 09:39–09:42 UTC

## Inventaire et reprise, avant toute écriture

PR brouillon #1, branche `repair/microcaps-chain-20261030`, tête de départ `f1bf6a48c1b04974fa633d5b910ef17e271de7b3`. Vérification Google Drive : dossier PRICE02A retrouvé (parquet de signaux mensuels 9 558 146 octets et dossier raw_prices), SEC_BRIDGE retrouvé (mapping CIK, fichiers filings/companyfacts) ; DATA04_EODHD_FUNDAMENTALS présent mais vide à sa racine ; FUND02E et FUND03A non retrouvés par recherche ciblée. Aucun fichier de ces archives n'a été modifié. Réutilisation des modules 07AA, 07Q2 et 07R, sans nouveau collecteur.

## Travail effectué et commits

1. Commit `cbe07ab7b4071d379881e8a179c52907bb20c174` : ajout de la fiche officielle Börse Stuttgart pour ICAPE, ISIN FR001400A3Q3 et symbole Z8J, dans le registre de collecte ICAPE ; adaptation du workflow isolé et du test hors réseau. **XSTU/Stuttgart n'est pas XFRA/Francfort** : la fiche ne peut pas, à elle seule, certifier Z8J.F. La date de publication est déclarée inconnue, sans la confondre avec l'horodatage de collecte. Le test exige le statut A_VERIFIER et aucune note.
2. Collecte GitHub Actions `41293986396` **SUCCESS** : six sources configurées, cinq fichiers bruts effectivement collectés avec SHA256, une source **BLOQUE_SOURCE HTTP 403** (Börse Stuttgart). Le collecteur n'a donc PAS obtenu de nouvel octet Stuttgart, ni de SHA256 pour cette sixième source. Publication automatique des cinq captures et de leurs audits au commit `53f6bbe38409344aae8b8d7fb3bb76b285503e29`, dossier `AUDITS/SOURCES_OFFICIELLES/20261101T093901458943Z/`. Empreintes des cinq bruts : `ee7ad3a86ea8d5fe93beb9016aba1c3b69b33a6e0c912f5169e038f11959c91a` (émetteur), `a277764892bf481339a79e5c81c8c05731fb2ee66e54997627ad7875c4f488c2` (Euronext IPO), `549ce7bd618afe3c8fab56a33898566e6e3ad9272fb05527e78989d860e7ad96` (PDF S1 2026), `05605e38d3a3e9778d3d8468b613752fe54ef2bbe529bd109b5c622824b0669c` (communiqué Euronext), `195fae401abb29142a7438d5e140b62dfbb2ff1430fd2ecd2b160474e6614ceb` (Deutsche Börse). Manifest et audit CSV disponibles dans le même dossier ; les publications des pages dynamiques restent inconnues.
3. Commit `7c20b9c3c2c82f36a7617ec1920f4013cee8f6e9` : correction de la **mesure de couverture** dans 07Q2. Une répétition exacte `(Source_URL, SHA256)` est désormais comptée une seule fois dans la file de certification, et une date manquante ou contradictoire entre répétitions reste classée inconnue. Deux colonnes ajoutées : `Documents_uniques_URL_SHA256_pistes` et `Repetitions_captures_pistes`. Le nombre brut historique de captures est conservé pour traçabilité. Tests adverses hors réseau ajoutés au module de test existant.
4. Préparation SSI sur `7c20b9c3`, run `41294197539` **SUCCESS**, publication automatique de la file et de l'audit SSI au commit `e0bb87e581b89c8b77885286c08548ec5a7d0466`.

## Vérifications reproductibles réellement exécutées

- CI complète `41293986398` et `41294197638` : **SUCCESS**.
- Replays virtuels isolés `41293986399`, `41293989775`, `41294197545` et `41294203054` : **SUCCESS**. Les exécutions `action_required` liées à des commits automatiques ne sont pas assimilées à des succès.
- Préparations SSI `41294056725` et `41294197539` : **SUCCESS**. Ces résultats valident le fonctionnement technique, pas la sélection économique.
- Sortie SSI publiée à 2026-11-01T09:42:04.789049+00:00 : **1 361 dossiers, zéro admission, 1 361 identités en quarantaine**. Plan 07Q2 : 12 249 lignes ; 54 captures brutes indexées, six anomalies exclues et deux sources bloquées. La file de certification dédoublonnée indique Fermentalg **6 captures / 5 couples URL-SHA uniques / 1 répétition**, ICAPE **30 / 15 / 15**. Aucune des deux sociétés n'est certifiée SCE.
- Le registre CHASSE n'a pas été modifié ; la CI inclut son contrôle historique de 31 352 détections. Aucun score SSI/MCPA/IPS, challenger, performance ou arbitrage inventé.

## Isolation, sécurité et état des blocages

La PR #1 reste **brouillon, ouverte, non fusionnée**. La branche `main` est distincte ; elle a avancé indépendamment jusqu'au commit `ffd7a3b3c2889148fcea9d925ec59d1c089b12a2` (deux commits depuis `d86124b6`, dont un workflow de diagnostic EODHD et une exécution quotidienne). Ces deux changements ne proviennent PAS des commits de cette intervention ; aucune écriture de notre part sur main, HISTORIQUE officiel, CPI, ETF AV ou le coffre maître. Aucune transaction financière réelle.

**Blocage externe constaté :** HTTP 403 sur Börse Stuttgart malgré l'URL officielle. Ne pas prétendre à une capture réussie, ne pas fabriquer de SHA256, ne pas réessayer indéfiniment la même URL. Conserver `EN_ATTENTE_DATA` pour cette source et poursuivre avec les archives primaires existantes. Prochain travail utile : revue indépendante des dates et identités de Fermentalg et ICAPE, rapprochement des 18 faits financiers déjà archivés et recherche de sources officielles datées réellement accessibles, puis qualification SSI B4–B7 et confrontation 09B. Aucun accès utilisateur requis pour cette étape.

La sauvegarde finale `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` n'est pas créée : les conditions d'admission SSI, d'arbitrage virtuel complet et de validation bout en bout ne sont pas remplies.

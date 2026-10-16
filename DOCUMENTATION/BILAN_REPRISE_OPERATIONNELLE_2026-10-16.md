# Reprise opérationnelle — 16 octobre 2026

Ce bilan décrit les exécutions réellement observées, et non l’état souhaité. Le recensement du marché US est une nouvelle piste indépendante de l’ancien sous-ensemble de 172 valeurs. Aucun de ses volumes ne constitue un classement d’investissement.

## Résultats effectivement exécutés

| Contrôle ou collecte | Résultat constaté | Preuve GitHub Actions |
|---|---|---|
| Production quotidienne | Succès, 40 lignes, 0 anomalie de qualité ; séance du 15 octobre | [38905484741](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38905484741) |
| Instruments : répertoires officiels Nasdaq/otherlisted | Succès, 2 490 cotations conservées | [38907888613](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38907888613) |
| Collecte documentaire élargie | 2 949 documents archivés ; exécution en échec contrôlé à cause de sources/identités à vérifier | [38906284085](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38906284085) |
| Extraction et normalisation financières enrichies | Succès à la tentative 2, après correction d’une fixture de test | [38908413602](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38908413602) |
| Matrice des preuves et index de gouvernance | Succès, 2 490 lignes préservées | [38910062827](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38910062827) |
| Réception complète hors réseau, incluant les nouveaux raccordements | 26 fichiers de tests réussis, syntaxe et intégrité des entrées contrôlées | [38912257459](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38912257459) |
| Sources officielles US hors SEC | Succès, 6 fichiers archivés dont un index sans comptes | [38911447302](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38911447302) |
| Raccordement des publications hors SEC à la matrice | Succès ; 5 publications à vérifier et 1 index, toujours zéro candidat autorisé | [38911923459](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38911923459) |

Les comptes rendus complets sont conservés dans `AUDITS/TESTS/RUN_<identifiant>_<tentative>/RESULTATS_TESTS.json`. Les tests 07X et Form 4 multi-XML sont inclus ; aucune connexion réseau n’est autorisée pendant leur exécution.

## Production et expérience T0

Le défaut de planification a été corrigé : une arrivée tardive du déclencheur GitHub ne provoque plus un abandon silencieux de la production prévue. Le choix été/hiver utilise le déclencheur déclaré ; l’heure effective ne doit pas être exactement 22 h 30. Le même défaut a été corrigé dans le verrou de la chasse du mardi à 22 h 15, avec tests été/hiver et retard après minuit. Cela ne constitue pas l’exécution effective de la prochaine chasse hebdomadaire, ni la planification complète du nouveau recensement US. Un refus du contrôle qualité dans 07B provoque maintenant un échec explicite ; une séance déjà présente reste idempotente.

L’exécution du 16 octobre à 13 h 09 UTC utilise la dernière séance achevée, le 15 octobre. Les deux portefeuilles valent **3 887,505145688508 €**, soit **−2,812371357787299 %** depuis T0. Ils restent identiques car aucun arbitrage validé n’a été réalisé. Benchmarks observés sur le même suivi : S&P 500 +1,012331148106881 %, Nasdaq 100 −1,855514692863764 %, STOXX Europe 600 +2,1559001363003176 %.

L’empreinte du T0 a été contrôlée avant/après. Le coffre maître V3 et les positions témoins n’ont pas été modifiés. Les trous historiques du 6 au 14 octobre ne sont pas artificiellement remplis. CPI et ETF Assurance-Vie sont hors périmètre et inchangés.

## Couverture : distinguer cotations, émetteurs et dossiers qualifiés

| Élément | Volume | Limite d’interprétation |
|---|---:|---|
| Cotations issues du recensement EODHD 50–300 M€ | 2 490 | Pistes sur le marché US, pas 2 490 sociétés américaines déjà authentifiées et admises |
| Cotations rapprochées d’un CIK | 1 468 | 1 444 CIK distincts ; les classes multiples restent visibles |
| Cotations sans CIK résolu | 1 022 | Manque d’identité/preuves, pas une appréciation négative de qualité |
| Cotations avec faits financiers comparables extraits | 1 267 | 50,9 % de 2 490, mais ce n’est pas une couverture SSI complète |
| Observations financières comparables et rattachées aux blocs | 321 999 | Pas des notes ; pas de total de dette ou de FCF fabriqué |
| Documents 10-K, 10-Q et DEF 14A archivés | 2 949 | 4 332 emplacements attendus sur 1 444 émetteurs ; absence de DEF 14A possible et absence de formulaire non équivalente à absence de comptes |
| Émetteurs avec les trois documents recherchés | 829 | 842 cotations ; ancienneté et périmètre à vérifier individuellement |
| Libellés d’action ordinaire dans les répertoires officiels | 1 105 | N’authentifie ni le domicile ni l’éligibilité de l’entité ; fonds/SPAC restent à contrôler |
| Instruments explicitement non ordinaires | 3 | À exclure selon les règles, sans les confondre avec des sociétés de mauvaise qualité |
| Cotations absentes des deux répertoires officiels | 1 297 | OTC ou identité à compléter ; jamais exclues sur cette seule absence |
| Références de gouvernance indexées par 07X | 272 782 | Références documentaires, pas des preuves de détention déjà lues |
| Références Form 4 / 4-A | 210 995 | **XML non extraits dans cette collecte élargie** ; aucune transaction ni exposition personnelle n’en est déduite |
| Dossiers admis SSI et candidats sélection autorisés | **0** | Le classement final et les arbitrages restent bloqués |

Le secret EODHD permet le recensement et les données de marché testées ; l’appel aux fondamentaux a répondu 403 lors de la vérification effective antérieure. Un abonnement ne démontre donc pas, à lui seul, l’accès à cet endpoint. Les comptes SEC constituent une autre source officielle. Les secrets ne sont jamais imprimés.

## Sources, identités et alertes documentaires

Les manifestes conservent URL, dates disponibles, empreintes des octets bruts et archives compressées. Les profils SEC ont été rapprochés du CIK attendu. Douze téléchargements sont bloqués, notamment d’anciens dépôts texte ou des références sans document primaire ; ils ne sont pas déclarés réussis. Il reste 1 371 emplacements non référencés par l’index récent.

Douze documents ont déclenché le contrôle strict de CIK. L’examen complémentaire montre **11 documents contenant le CIK attendu parmi plusieurs CIK**, et **un document EFR.US / DEF 14A ne contenant pas le CIK attendu**. Ces observations sont conservées dans `AUDITS/CONTROLE_SYSTEME/EXAMEN_CIK_2026-10-16/`. **Aucune alerte n’est levée** : il faut vérifier le périmètre de consolidation ou corriger le document associé. Les contrôles initiaux sont conservés.

## SCE-Discovery et maintien des corrections humaines

Les documents maîtres SCE du 12 août ont été retrouvés. Leur ordre de contrôle déterministe SHA-256 est raccordé au recensement actuel ; les anciens paramètres expérimentaux et scores d’août ne sont pas appliqués au mandat microcaps d’octobre. La transcription, les sources et l’adaptation de mandat figurent dans `DOCUMENTATION/RELEVE_PROTOCOLE_SCE_DISCOVERY_2026-10-16.md`.

L’exécution conserve les 2 490 cotations, trouve 1 650 ISIN avec clé de contrôle correcte et deux cotations partageant un ISIN. Une clé correcte n’est pas une preuve officielle d’identité. Les identités non validées, les doubles cotations et les types d’émetteurs non confirmés empêchent encore une admission SCE finale. Aucun seuil financier absent des documents maîtres n’a été inventé.

Le registre `CONFIG/QUALIFICATIONS_SSI_US_HUMAINES.csv` reçoit les preuves, corrections et notes validées. Les exécutions le lisent sans l’écraser. Les sorties de préparation restent isolées dans les audits et sont raccordées au validateur SSI existant ; celui-ci refuse les notes sans preuves vérifiées.

## Sources officielles US hors SEC : complément effectivement exécuté

La collecte [38911447302](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38911447302) a réussi : **six fichiers pour quatre sociétés**, zéro source bloquée, zéro note attribuée. L’audit est conservé dans `AUDITS/SOURCES_OFFICIELLES/20261016T135505996066Z/`. Le dénominateur reste 2 490 ; 2 486 cotations n’ont pas encore de source configurée dans ce registre complémentaire, sans préjuger de leurs pièces SEC déjà disponibles.

- BMBN : comptes annuels audités 2025 et communiqué des résultats au 30 juin 2026, liés depuis la page officielle des actionnaires.
- UNIB : comptes annuels audités 2025 et complément financier au 30 juin 2026, liés depuis la page officielle des états financiers.
- CPKF : communiqué de résultats du deuxième trimestre 2026 publié sur le site officiel de la banque ; le périmètre de la holding doit être vérifié.
- STBI : **index officiel de rapports annuels uniquement** ; le contenu du rapport hébergé dans une visionneuse externe n’est pas compté comme des comptes archivés.

Les six dates exactes de mise à disposition publique restent explicitement inconnues. La période comptable et la date de signature de l’auditeur ne sont pas converties en date de publication. Ces pièces sont donc exclues de toute utilisation rétrospective non prouvée. Aucun compte de filiale n’est assimilé automatiquement aux comptes consolidés de la société cotée. La matrice exécutée le 16 octobre à 13 h 59 UTC incorpore ces cinq publications et distingue l’index STBI ; elle vérifie les empreintes des fichiers, le dénominateur du recensement et la correspondance du CIK déclaré, sans valider automatiquement l’identité ou les comptes. Le collecteur existant 07AA est réutilisé ; les domaines et redirections, les tailles et les empreintes sont contrôlés.

## Ce qui bloque encore la sélection finale

1. Vérifier l’identité complète, la cotation primaire, l’ISIN officiel et le domicile, notamment pour les 1 022 pistes sans CIK ; distinguer entreprises US et entreprises étrangères cotées aux États-Unis.
2. Lire les pièces et leur périmètre ; compléter les rapports officiels hors SEC, les formulaires étrangers 20-F/40-F et les archives historiques non encore paginées.
3. Extraire et vérifier le contenu de gouvernance, les détentions réelles, options/actions gratuites et transactions ; un index Form 4 ne suffit pas à B4/B5.
4. Collecter les volumes/turnover et le spread disponible pour B7, puis documenter chaque note des sept blocs selon le barème existant. Atteindre au moins 50 %, idéalement 90 %, de dossiers réellement évaluables, en publiant le dénominateur exact.
5. Après admission SSI ≥65 : compléter MCPA/IC/CX/Δ/WWWS et scénarios 3/6 mois, puis IPS, Top20/Top5, confrontation aux 40 et test du prochain euro avec frais aller-retour. Sans ces preuves, aucun classement des « meilleures » valeurs ni arbitrage mensuel ne peut être validé.

Les données découvertes après T0 ne sont pas utilisées comme si elles étaient connues au 1er octobre. Les frais restent 2,5 % à l’achat et à la vente ; réussir le test du moteur de duel ne constitue pas la validation d’un arbitrage réel. La collecte mondiale hors US n’est pas déclarée complète. La revue du mardi existe, mais le nouveau recensement US complet reste déclenché manuellement ; son automatisation de bout en bout, synchronisée avec l’ensemble de ses dépendances, n’est pas déclarée terminée.

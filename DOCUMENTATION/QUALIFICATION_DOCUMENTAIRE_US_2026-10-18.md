# Qualification documentaire US — 18 octobre 2026

Cette étape prolonge la collecte sur un premier lot de 12 émetteurs pris dans l’ordre SCE déjà archivé, parmi les dossiers disposant de faits financiers comparables. Ce lot n’est pas représentatif de tout le marché et ne remplace pas l’univers de 2 490 cotations. Il ne permet pas d’annoncer 50 % de dossiers SSI complets.

## Exécution effectivement constatée

- Collecte SEC : [exécution 39135798581](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39135798581), succès, journal du job 117699931692.
- 12 profils avec concordance CIK/ticker ; 216 dépôts Form 4 / 4-A ; 259 lignes non dérivées ; 473 réponses HTTP archivées.
- Vérification locale de toutes les empreintes des 510 fichiers du manifeste et des 473 contenus HTTP décompressés. Réception hors réseau : 29 fichiers de tests exécutés ; intégrité T0 contrôlée.
- Archive : `AUDITS/RELECTURE_INITIES_US/20261018T142514404414Z/`.
- Revue indépendante identifiée comme effectuée par l’assistant Codex, sans revendiquer de validation humaine : `AUDITS/QUALIFICATIONS_DOCUMENTAIRES_US/2026-10-18_LOT_SCE/`.

## Décisions et contrôles documentaires

Quatre exclusions de SPAC identifiables : **MUZE, AACP, XFLH et SVCC**. La note 1 de chaque dernier 10-Q décrit une blank check sans activité opérationnelle au dernier arrêté. Les profils actualisés concordent avec les tickers. Pour XFLH, le 8-K du 22 septembre décrit une lettre d’intention avec Renogen Biolab et des accords définitifs restant à négocier. Ces sources, dates, empreintes, justifications et limites sont conservées. L’absence de 8-K plus récent dans les index parcourus ne garantit pas une absence absolue d’événement non déposé.

Ces décisions utilisent l’exclusion « SPAC identifiable » du protocole existant. Elles ne créent aucun seuil ni aucune note. Les preuves EXCLUSIONS sont ajoutées au registre append-only. Un registre documentaire distinct est lu avant les corrections humaines ; celles-ci priment et ne sont pas modifiées. Le validateur 07R a effectivement produit sur le contrôle local : **2 490 lignes conservées, 4 ELIMINE, 2 486 A_COMPLETER_PREUVES_SSI, 0 ADMIS_SSI**.

**RACC n’est pas exclue à ce stade** : accord OHB Pediatrics annoncé dans le 10-Q, SIC actuel différent de l’ancien signal blank check, état de clôture à contrôler. Le SIC n’est pas une preuve suffisante.

## B4 : actions existantes distinguées des droits futurs

| Dossier | Date de détention du proxy | Bénéficiaires groupe | Droits sous 60 jours inclus | Actions existantes hors ces droits | Rapport au capital existant |
|---|---|---:|---:|---:|---:|
| NUS | 31 mars 2026 | 1 381 722 | 358 288 | 1 023 434 | 2,0811 % |
| PLAY | 23 avril 2026 | 602 533 | 45 144 | 557 389 | 1,6045 % |
| DTIL | 25 mars 2026 | 702 426 | 37 965 | 664 461 | 2,5751 % |

Ces calculs datés décrivent une détention bénéficiaire du groupe, pouvant inclure des détentions indirectes. Ils ne prouvent pas un patrimoine net personnel ni les détentions au 18 octobre. Aucun score B4 n’est attribué : il reste à actualiser les mouvements et la composition du groupe, à vérifier les actions gratuites et la valeur exposée.

ISPR présente un écart non résolu de 13 000 titres entre la ligne Michael Wang et le détail de sa note ; aucune correction inventée. CCFN : tableau groupe 326 293 titres / 9,23 %, ventilation à terminer. BHM : base mêlant actions, OP Units et LTIP, non comparable directement à un pourcentage d’actions ordinaires cotées ; 44 609 LTIP à acquérir sous 60 jours font partie du dénominateur publié.

## Form 4 : éviter les faux achats et doubles comptes

- PLAY : le 4/A `0001193125-26-394477` corrige explicitement le titre « option » en « Common Stock » du dépôt `0001193125-26-394355`. Il s’agit d’un même achat de 12 000 actions par Nathaniel Lipman le 17 septembre, conservé une seule fois pour l’interprétation. Les deux dépôts bruts restent archivés.
- Un autre amendement PLAY reste à rapprocher ; aucun total de flux n’est publié tant que ce point subsiste.
- 11 lignes concernent des opérations de 2025 déposées en 2026 : conservées mais hors flux transactionnel 2026.
- MUZE et AACP : placements privés de units comprenant action et warrants/rights. Le prix d’une unit ne valorise pas séparément la seule action. Une déclaration conjointe ne multiplie pas le nombre d’achats par le nombre de déclarants.
- Les codes A/F/M/G/D ne sont pas transformés en achats cash libres. Les achats et ventes P/S restant à qualifier ne sont pas assimilés automatiquement à une conviction personnelle.

La fenêtre concerne les dépôts du 1er janvier au 18 octobre 2026. L’exhaustivité de l’historique et les détentions actuelles ne sont pas déclarées validées. Le parseur conserve les fonctions des déclarants, les titres, les notes de bas de page, les détentions indirectes et les amendements ; il ne reconstruit pas les positions dérivées.

## Raccordement et limites restantes

La consolidation réapplique 07AL puis le validateur SSI, et raccorde les 12 profils / 259 lignes Form 4 à la matrice globale avec une couverture partielle explicite. Les 210 995 références de l’ancien index global ne sont pas confondues avec ces dépôts extraits. Les corrections humaines, le T0 et les données de portefeuille restent protégés.

Aucune admission SSI, note MCPA ou sélection finale n’est créée. Les principaux travaux restants sont l’actualisation des détentions, les blocs financiers et de gouvernance sur preuves relues, les identités encore incomplètes et l’extension de cette qualification au reste de l’univers. Le seuil de 50 % de dossiers entièrement évaluables reste à atteindre.

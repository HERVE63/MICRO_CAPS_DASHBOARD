# Premières notes SSI documentaires US — 18 octobre 2026

Le travail passe de pièces collectées à des notes justifiées : **11 blocs sur trois dossiers**, avec **15 références primaires ajoutées** au registre append-only. Les notes sont des jugements explicites de l’assistant Codex selon le barème SSI V1.0 ; elles ne sont ni des chiffres publiés par l’émetteur, ni une validation humaine, ni une notation automatique de la collecte.

## Résultats partiels, sans note globale imputée

| Dossier | B1 /20 | B2 /15 | B3 /15 | B6 /10 | Points sur blocs documentés | Maximum des blocs documentés | Plafond conditionnel sur 100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nu Skin — NUS | 13 | 3 | 2 | 8 | 26 | 60 | 66 |
| Dave & Buster’s — PLAY | 8 | 5 | 3 | 8 | 24 | 60 | 64 |
| Precision BioSciences — DTIL | 12 | 7 | À compléter | 8 | 27 | 45 | 82 |

**Le plafond est une borne arithmétique conditionnelle : points documentés + maximum des blocs restants.** Il ne constitue ni une note SSI sur 100, ni une prévision, ni une admission. Les notes peuvent être remplacées après une nouvelle preuve. Avec les notes présentes, PLAY ne peut atteindre 65, même en obtenant le maximum sur les trois blocs restants ; son statut officiel reste incomplet, sans inventer des notes pour prononcer un refus complet. Ce tableau ne classe pas les sociétés : les périmètres de preuve diffèrent.

B4, B5 et B7 ne sont pas renseignés pour ces trois sociétés. Pour DTIL, B3 n’est pas renseigné non plus : les revenus de milestones et les progrès cliniques ne prouvent pas une croissance commerciale récurrente. Les contrôles d’identité/SCE et d’exclusions des sociétés opérationnelles restent à terminer. **Aucune admission SSI ou sélection MCPA n’est prononcée.**

## Ce qui justifie les notes

### Nu Skin

Les comptes arrêtés au 30 juin montrent 189,643 MUSD de cash et 1,743 de placements courants, contre 213,664 de dette comptable courante et longue. Les échéances sont étalées, mais un tirage supplémentaire de revolving après arrêté et un FCF simple semestriel de **−12,646 MUSD** empêchent de considérer la situation comme solide. B1 = 13, dans la classe acceptable.

La perte nette de 247,962 MUSD comprend d’importants éléments non monétaires. Nous ne la confondons pas avec une consommation équivalente de cash. L’EBIT publié est néanmoins négatif et le FCF simple se dégrade : B2 = 3. Le recul du CA se poursuit après 2025, avec **−14,64 % au S1** et une baisse des clients : B3 = 2. Les comptes annuels audités, les états trimestriels et leurs rapprochements soutiennent B6 = 8.

### Dave & Buster’s

Les **492,1 MUSD de liquidité** correspondent à **16,0 de cash + 476,1 de crédit disponible**. Le crédit disponible n’est pas une trésorerie possédée. Dette, charges d’intérêt et engagements immobiliers maintiennent B1 en classe fragile, à 8.

Au S1, le CFO de 160,6 moins les investissements de 190,0 donne **−29,4 MUSD de FCF simple**. Le FCF ajusté publié de +19,5 incorpore 48,9 de financements de sale-leaseback. Le flux s’améliore par rapport au S1 de l’exercice précédent, mais la perte nette et la baisse de l’EBIT ne permettent que B2 = 5. Les ventes comparables du T2 reculent de 2,9 % malgré les ouvertures : B3 = 3. B6 = 8 pour les états audités et rapprochements détaillés ; les changements d’équipe doivent encore être intégrés à B4/B5.

### Precision BioSciences

Le total de **112,406 MUSD** comprend **26,330 de cash bloqué**, séparé des **86,076 de cash libre et équivalents**. La dette et sa maturité 2029 sont distinguées des financements potentiels. L’estimation de runway jusqu’en 2028 reste une perspective de la direction sous hypothèses, pas une garantie. B1 = 12.

La consommation de cash opérationnel diminue de 39,323 à 25,379 MUSD, et la perte opérationnelle diminue ; la perte nette augmente notamment sous l’effet de la réévaluation des warrants. Cette amélioration ne signifie pas rentabilité : B2 = 7. Les comptes réglementaires recoupables soutiennent B6 = 8. Aucun revenu produit n’est inventé à partir de résultats cliniques.

## Sources et conservation

Les justificatifs détaillés, montants, calculs et références primaires sont dans `AUDITS/NOTATION_SSI_DOCUMENTAIRE_US/2026-10-18_PREMIERS_BLOCS/`. Chaque preuve référence le document SEC brut archivé, sa date de dépôt, son empreinte et son auteur de revue. Les sources des comptes proviennent de l’archive conservée `AUDITS/RELECTURE_INITIES_US/20261018T142514404414Z/`.

Les 8-K du lot ont été collectés pour tous les émetteurs, indépendamment du SIC. La tentative [39139511115](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39139511115) a échoué sur un timeout Form 4 : 215 dépôts traités, un téléchargement interrompu. L’échec et les pièces ont été conservés ; la consolidation a bloqué ce lot incomplet. La reprise [39139925778](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39139925778) a réussi : **216 dépôts, 259 lignes, 498 réponses archivées dont 270 réutilisées par empreinte**, profils relus sans cache et T0 intègre. Une date de collecte ancienne n’est pas remplacée par une fausse date fraîche.

Les annonces examinées signalent notamment le congé médical d’un dirigeant NUS, les changements de CEO/équipe chez PLAY, et les nominations ainsi que le premier patient du programme DMD chez DTIL. Ces événements expliquent pourquoi les tableaux de détention des proxies ne sont pas assimilés à des détentions actuelles.

## Raccordement et contrôles

Les notes documentaires sont stockées séparément des corrections humaines. Le registre humain garde la priorité et son empreinte est préservée. 07AL assemble les références, 07R valide les preuves et publie les blocs réellement documentés, puis 07AM les raccorde à la matrice globale. Le calcul du plafond ne modifie pas les règles d’admission. Les mises à jour des registres déclenchent la consolidation ; la collecte n’écrit aucun de ces registres de notes.

Le contrôle local effectif a conservé les 2 490 cotations, les quatre exclusions SPAC antérieures et les 11 blocs documentés, sans aucune admission. Trente fichiers de tests ont été exécutés localement avec succès. Les tests couvrent notamment : preuve corrompue refusée, CIK divergent écarté du décompte partiel, note ne concordant pas avec sa preuve refusée, priorité humaine, absence d’admission par simple plafond, cache SEC corrompu refusé et reprise après timeout.

Le seuil de 50 % de dossiers entièrement évaluables n’est pas atteint. Ce premier lot documente le passage à la notation ; il ne clôt pas la qualification de l’univers ni la confrontation aux 40 titulaires.

## Précision de libellé conservée dans l’historique

Une justification NUS désignait improprement les 251,802 MUSD d’actifs courants moins passifs courants comme un « BFR net ». Il s’agit du fonds de roulement courant. Une preuve de remplacement identifiée corrige ce seul libellé ; le montant et B1 = 13 restent inchangés. L’ancien enregistrement n’est pas réécrit. Les notes initiales et leur première réception GitHub restent archivées.

## Réception de production effectivement contrôlée

La [consolidation finale 39140662021](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39140662021) et la [réception SEC SSI 39140662040](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39140662040) sont terminées avec succès. Les 30 fichiers de tests sont archivés avec statut OK. Le CSV sauvegardé et son empreinte ont été relus : 2 490 cotations, 11 blocs sur trois dossiers, quatre exclusions SPAC et aucun candidat autorisé. Le résultat SSI référence bien la preuve corrigée NUS. Le journal confirme l’intégrité SHA256 du T0.

La matrice contrôlée est `AUDITS/MATRICE_PREUVES_US/20261018T153000025501Z/MATRICE_PREUVES_SSI_US.csv`. Les contrôles de remplacement de preuve, de reprise SEC et de priorité des corrections humaines sont opérationnels. Il reste à terminer les blocs et identités manquants, étendre la qualification, puis seulement passer aux admissions SSI et au moteur MCPA/IPS.

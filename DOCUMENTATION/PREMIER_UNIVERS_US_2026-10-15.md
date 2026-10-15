# Premier univers US documenté — 15 octobre 2026

L'utilisateur demande de commencer par un univers américain. Il s'agit d'un **pilote US**, extrait des 1 361 dossiers déjà constitués, sans refaire la chasse ni changer le T0. Ce sous-ensemble ne prétend pas recenser toutes les microcaps américaines. Les 1 116 dossiers dont l'origine n'est pas documentée restent dans le périmètre mondial, sans rejet financier.

## Premier cadrage exécuté sur les archives authentiques

Le module `07AE_CADRER_UNIVERS_US.py` trouve 172 pistes avec immatriculation dans un État US et adresse d'activité US concordantes, 25 profils hors de ce cas, 39 origines à compléter, 8 cas mixtes et un type d'émetteur à clarifier. Les 1 116 autres dossiers n'ont pas de profil d'origine exploitable. Les codes SEC d'États sont interprétés comme tels : `DE` signifie ici Delaware, pas Allemagne. Le champ Pays des dossiers est un pays de cotation.

La concordance administrative ne vérifie pas à elle seule le lien entre l'émetteur et sa cotation allemande. Toutes les pistes gardent donc `A_VERIFIER_COTATION_EMETTEUR`. Les émetteurs sont dédoublonnés par CIK avant tout calcul de couverture. Aucun score et aucune identité ne sont validés automatiquement.

Sur ce premier périmètre provisoire de 172 émetteurs, le minimum de 50 % correspond à **86 émetteurs effectivement évaluables au SSI**, la cible de 90 % à **155**. Les seuils mondiaux restent 681/1 225 sur 1 361 ; les seuils US ne les remplacent pas. L'origine inconnue d'une partie des 1 361 empêche d'affirmer que ces 172 représentent tous les émetteurs américains présents dans le fichier.

## Collecte des pièces primaires

Les index SEC archivés référencent les trois types de documents pour les 172 pistes : 10-K (annuel), 10-Q (trimestriel), DEF 14A (gouvernance, actionnariat et rémunérations). **Une référence ne prouve pas un téléchargement réussi.**

**Réception effective :** le [workflow 38759384293](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38759384293) s'est terminé avec succès le 15 octobre : **516 documents sur 516 collectés**, zéro source bloquée, trois pièces pour chacun des 172 émetteurs provisoires. Les 16 fichiers de tests ont passé la réception avant collecte ; le contrôle du T0 et l'absence de modification des dossiers et sauvegardes ont réussi. Le commit de sauvegarde est `c408242`.

Les pièces sont conservées dans `AUDITS/DOCUMENTS_US/20261015T152042462891Z/` (manifestes, audit CSV et fichiers bruts). Le périmètre exécuté est dans `AUDITS/UNIVERS_US/20261015T152040768212Z/`. Les profils utilisés proviennent des réponses SEC datées du 10 octobre ; les dates des documents restent celles de leurs dépôts. Ce premier passage ne revendique pas un index SEC rafraîchi au 15 octobre.

Le module `07AF_COLLECTER_DOCUMENTS_US.py` sélectionne le dépôt le plus récent de chaque type, uniquement parmi les dates connues à la date de collecte. Les noms de documents et accessions proviennent du profil SEC brut dont l'empreinte et le CIK sont contrôlés. Il télécharge les fichiers primaires avec le contact SEC du dépôt, limite les requêtes, contrôle les redirections et refuse les pages de blocage. Chaque réponse est conservée avec SHA-256, URL, date de dépôt, date de collecte, CIK et statut. Les fichiers déjà archivés sont réutilisés après vérification de leur empreinte, en conservant leur date originale.

Le workflow `univers_us_documente.yml` exécute réellement les tests, le cadrage puis la collecte ; il contrôle le T0 et l'absence de modification des dossiers et sauvegardes. Les audits sont conservés même en cas d'échec. Un refus de source garde une trace et fait échouer l'étape de collecte.

Le contrôle `07AG_CONTROLER_DOCUMENTS_US.py` vérifie ensuite les empreintes, les dates et le CIK iXBRL quand il figure dans le document. Un CIK absent dans un proxy reste à relire ; il n'est pas transformé en concordance. Une concordance du CIK du dépôt ne valide toujours pas la cotation allemande ni les notes SSI. L'âge des dépôts est conservé pour la revue de fraîcheur, sans seuil d'exclusion inventé.

Les relectures locale et [GitHub 38760717623](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38760717623), terminée avec succès, des **516 fichiers authentiques sauvegardés** vérifient toutes les empreintes et les dates : **498 CIK iXBRL concordants, zéro divergent, 18 absents**. Les 18 absences concernent des DEF 14A et restent à relire. Les **17 fichiers de tests**, incluant la reprise sans réseau, la conservation de la date de collecte, le refus d'un cache altéré et la distinction entre CIK absent/multiple/concordant, passent dans [GitHub Actions 38760718258](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38760718258).

La deuxième exécution sauvegarde le contrôle dans `AUDITS/CONTROLE_DOCUMENTS_US/20261015T153002852798Z/` et les pièces réutilisées dans `AUDITS/DOCUMENTS_US/20261015T152954158149Z/`. Le contrôle du T0 et l'absence de modification des dossiers et sauvegardes réussissent de nouveau. Le cadrage actualisé produit aussi `COUVERTURE_SECTORIELLE_US.csv` dans son archive `AUDITS/UNIVERS_US/` : les activités SIC et les données de secteur manquantes restent visibles, sans quota ni note supplémentaire inventés. Le commit de sauvegarde est `2673bea`.

## Fraîcheur : résultat à ne pas masquer

| Type | Dépôts datés de 2026 | Dépôt le plus ancien du lot |
|---|---:|---|
| 10-K | 163 / 172 | 2025-06-23 |
| 10-Q | 171 / 172 | 2024-11-14 |
| DEF 14A | 153 / 172 | 2013-10-10 |

**146 émetteurs sur 172** ont les trois dépôts datés de 2026. C'est un indicateur descriptif de fraîcheur, pas une règle SSI nouvelle et pas une preuve de complétude : les périodes, amendements et autres types de dépôt restent à examiner. Un ancien DEF 14A ne prouve pas l'absence de toute communication récente ni, à lui seul, une mauvaise gouvernance. Les pièces anciennes nécessitent une recherche complémentaire et un contrôle de l'identité/statut actuel de l'émetteur.

## Mesures à ne pas confondre

1. Piste d'origine US concordante.
2. Documents primaires téléchargés.
3. Identité et preuves vérifiées pour tous les blocs SSI, ou exclusion documentée.
4. Admission SSI ≥65, puis MCPA/IC/CX/Δ/WWWS et IPS validés.

Le minimum de 50 % porte sur le niveau 3, pas sur le nombre de fichiers téléchargés. L'audit initial du validateur SSI donne encore **zéro émetteur évaluable**, et pas 172. La couverture sectorielle sera mesurée par SIC et la provenance des données suivie ; elle ne sera pas présentée comme représentative du monde.

Aucun Top5 final, arbitrage ou changement des 40 positions n'est produit par ce pilote.

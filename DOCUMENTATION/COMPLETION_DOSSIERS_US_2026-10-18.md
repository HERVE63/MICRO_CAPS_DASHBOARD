# Compléter les dossiers US — 18 octobre 2026

## Objectif retenu

Rendre d’abord au moins 50 % de l’univers pertinent réellement évaluable selon les sept blocs SSI, en maintenant un audit de toutes les 2 490 cotations recensées. Les 1 267 dossiers contenant des observations financières comparables ne sont pas assimilés à 1 267 dossiers SSI complets. Aucun dossier pauvre en informations n’est déclaré peu intéressant sur ce seul motif.

## Recherche complémentaire et sources

Le premier lot est pris dans l’ordre SCE existant parmi les dossiers disposant déjà de faits financiers comparables. Les 12 rangs du lot, y compris les sociétés de type Blank Check à contrôler et le dossier restant à poursuivre, sont conservés dans `AUDITS/RECHERCHE_COMPLEMENTS_US/2026-10-18_LOT_ORDRE_SCE/LOT_PRIORISATION.csv`. Six dossiers ont fait l’objet d’observations documentaires ciblées : NUS, PLAY, CCFN, DTIL, ISPR et BHM. Ce lot est un ordre de travail, pas une liste de valeurs recommandées.

Les pages Zonebourse de NUS, PLAY, ISPR et DTIL ont été consultées. UNIB est conservé comme cas antérieur hors lot : son profil est accessible, sa page de comptes redirige vers une connexion. Le registre conserve les URL, dates de consultation, objets et limites ; il ne prétend pas archiver les octets des pages ou disposer d’un accès authentifié. Les chiffres d’institutionnels, les pourcentages à des dates différentes et les cotations alternatives ne sont pas fusionnés.

Les observations primaires renvoient aux proxies SEC déjà archivés, avec leur URL, leur date de dépôt et l’empreinte de leurs octets. Exemples :

- NUS : le groupe déclare une propriété bénéficiaire de 1 381 722 titres et 2,8 %, dont 358 288 droits à acquérir sous 60 jours. Le pourcentage brut n’est pas un pourcentage d’actions personnelles déjà détenues.
- PLAY : 602 533 titres et 1,73 % pour le groupe dans le tableau ; la note précise 45 144 titres issus d’options exerçables sous 60 jours. Les véhicules Hill Path ne sont pas assimilés intégralement au patrimoine personnel d’un administrateur affilié.
- DTIL : 702 426 titres et 2,7 % de propriété bénéficiaire du groupe. La distinction actions/options et, pour certains institutionnels, warrants doit être conservée.
- ISPR : 37 845 663 titres et 65,9 % pour le groupe. Les véhicules familiaux et leurs bénéficiaires ne doivent pas être additionnés deux fois.
- CCFN : les règles de propriété incluent conjoint, pouvoirs partagés et options ; la détention personnelle doit être reconstruite depuis les notes.
- BHM : le dénominateur combine classes A/C, OP Units et LTIP acquis. Il n’est pas celui des seules actions ordinaires cotées.

Ces données décrivent les documents et leurs dates ; elles ne sont pas présentées comme des détentions actualisées au 18 octobre. Aucune note B4/B5 n’a été attribuée à partir de ces seuls constats.

## Lecture des documents de gouvernance à grande échelle

Le module 07AO lit les proxies DEF 14A déjà archivés et accepte seulement les pièces dont le contrôle de CIK est concordant. Il vérifie à nouveau les empreintes des archives et octets décompressés, les dates et le périmètre du recensement. Les pièces absentes, sans CIK ou divergentes restent signalées.

L’exécution GitHub [39133010038](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39133010038) a réussi :

| Résultat | Volume |
|---|---:|
| Cotations conservées dans la couverture | 2 490 |
| Proxies concordants avec passages repérés | 650 |
| Passages de gouvernance extraits avec contexte et ancrages | 2 867 |
| Émetteurs avec un passage sur le groupe dirigeant | 583 |
| Proxies non traités pour source ou CIK à vérifier | 782 |
| Notes attribuées | 0 |

Les libellés non repérés restent à relire. Un passage peut être une explication de définition ou un tableau, et ne constitue pas automatiquement une détention nette calculable. L’extraction conserve un contexte autour des mentions de groupe, droits à 60 jours et dilution/rémunération. Les offsets dans le texte normalisé et les empreintes rendent la relecture reproductible.

## Complément de marché EODHD

Le module 07AN est exécuté sur les 2 490 cotations, sans tri par disponibilité, qualité ou performance. La dernière séance disponible de l’indice GSPC.INDX fixe une ancre commune. Les momentum utilisent les cours ajustés sur 1/3/6/12 mois calendaires ; un cours absent à l’ancre ou un point de départ trop éloigné reste manquant. EODHD fournit un cours brut et un volume ajusté des splits : leur produit direct ne suffit pas. Les volumes monétaires sont donc recalculés avec les événements de splits pour remettre prix et volumes sur une base homogène ; sans ces événements, le montant échangé reste manquant. Les cas de split et reverse-split sont testés. Le premier passage a effectivement obtenu 2 474 cours à l’ancre et 2 106 séries avec les quatre momentum ; ses anciens produits naïfs prix-volume sont invalidés dans la matrice, sans effacer l’archive originale. Le deuxième passage réutilise les archives chiffrées du même jour et complète les splits.

Les données et métriques fournisseur restent chiffrées. Les fichiers publics décrivent la disponibilité, les dates, le nombre de séances et les empreintes, sans publier les cours et métriques licenciés. Une réserve de 10 000 crédits est protégée pour les autres outils ; CPI et ETF Assurance-Vie ne sont pas modifiés.

La force relative calculée contre GSPC.INDX utilise un indice de prix : elle ne constitue pas une comparaison total-return homogène avec les actions ajustées des dividendes, et n’autorise aucune note automatique. Le spread et le turnover rapporté au capital ne sont pas inventés à partir d’un historique quotidien.

Le premier passage complet ([39132514558](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39132514558)) est conservé pour ses cours et momentum. La correction du volume monétaire est documentée sans effacer ce premier état. Le résultat définitif ci-dessous correspond au passage avec événements de splits.

L’exécution corrigée [39133897615](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39133897615) a réussi, avec date de référence commune **16 octobre 2026** :

| Mesure de disponibilité | Cotations | Part des 2 490 |
|---|---:|---:|
| Collecte tentée | 2 490 | 100 % |
| Cours ajusté à l’ancre commune | 2 474 | 99,4 % |
| Momentum 1/3/6/12 mois tous disponibles | 2 106 | 84,6 % |
| Volume médian en valeur sur 63 séances, corrigé des splits fournis | 2 402 | 96,5 % |

Le second passage a réutilisé les historiques du même jour et consommé 2 403 crédits estimés pour compléter principalement les événements de splits. Les points de départ, dates, erreurs individuelles et empreintes sont conservés dans `AUDITS/MARCHE_US_EODHD/20261018T135934886533Z/`. Zéro erreur globale bloquante ; les données individuelles absentes restent visibles.

Ces pourcentages mesurent la **couverture de marché**, pas la complétude SSI. Un volume disponible peut être faible ou nul ; sa réception ne prouve pas une liquidité suffisante. Aucun score ni achat ne découle de cette collecte.

## Réception et raccordement

La matrice finale [39134487981](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39134487981) a réussi et confirme 2 490 lignes, 2 402 mesures de volume corrigées, 2 106 séries de quatre momentum et 583 cotations avec passages sur le groupe dirigeant. Son état est conservé dans `AUDITS/MATRICE_PREUVES_US/20261018T140728373220Z/`. Aucun candidat de sélection n’est autorisé par cette matrice.

Les nouvelles sorties sont raccordées à la matrice 07AM avec contrôle d’empreinte, de dénominateur et d’unicité des tickers. Elles indiquent ce qui est disponible et ce qui reste à lire, sans convertir des champs reçus en notes vérifiées.

La première réception GitHub a révélé `cryptography` absent de certains workflows, alors qu’il était disponible localement et dans le workflow de collecte EODHD. L’installation a été corrigée dans tous les workflows lançant la réception complète. La matrice a été réexécutée avec succès après cette correction ([39133201530](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39133201530)), avec les 2 490 lignes et les passages de détention raccordés. Le contrôle T0 et la production quotidienne ont également réussi ([39133201555](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39133201555)). Les détails des futurs échecs sont désormais imprimés dans les journaux, en plus du rapport JSON. Le workflow SEC historique conserve son déclenchement manuel ; une modification de ses dépendances ne relance plus automatiquement une collecte de 300 pistes anciennes.

La réception finale [39133897619](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/39133897619) a ensuite réussi : **28 fichiers de tests**, dont le calcul des horizons, l’ancre commune, les valeurs absentes, la séparation des bases prix-volume, les splits et reverse-splits, le chiffrement des archives et les garde-fous de la matrice. Les tests restent hors réseau, sans modifier DONNEES ou SAUVEGARDES.

## Limites conservées

L’analyse des profils officiels a aussi retrouvé **197 CIK portant le SIC 6770, Blank Checks**. Ce sont des signaux à examiner, pas 197 exclusions rétroactives automatiques : un code peut nécessiter une actualisation après une combinaison d’entreprises. Le fichier source, le CIK et l’empreinte sont conservés dans le registre de recherche. Le dénominateur initial n’est pas effacé pour présenter artificiellement un meilleur taux de couverture.

La quantité de documents ou de passages ne prouve pas encore que 50 % des dossiers soient évaluables sur sept blocs. Les identités, les échéances et risques financiers, la détention personnelle actualisée, la dilution, la liquidité et les justifications exactes des notes restent à valider. Aucun classement MCPA/IPS ni Top5 n’est déclaré terminé. Les informations découvertes aujourd’hui ne sont pas projetées à T0.

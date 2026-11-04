# Traitement des 40 fiches MICRO CAPS — 4 novembre 2026

**40/40 fiches enrichies et auditées. La mission de finalisation intégrale reste inachevée : aucune fiche n’est déclarée complète ou validée MCPA/IPS.**

2,045 champs renseignés sur 4,320 (47.34%). Le total inclut 880 champs de scénarios, notes et décisions, laissés vides. Hors bloc `complements` : 59.45%. Ces taux mesurent la présence de valeurs, pas leur validation financière.

1273 valeurs relèvent de sources secondaires non rapprochées. 40 autres sont des proxys de liquidité explicitement estimés. Les niveaux de fiabilité figurent dans chaque cellule.

## Couverture par société

| Société | Ticker | Renseignés / 108 | Couverture | Secondaires à rapprocher |
|---|---|---:|---:|---:|
| Intellicheck | IDN | 55 | 50.93 % | 22 |
| InfuSystem | INFU | 58 | 53.7 % | 29 |
| One Stop Systems | OSS | 52 | 48.15 % | 25 |
| Crexendo | CXDO | 56 | 51.85 % | 30 |
| Lifeway Foods | LWAY | 57 | 52.78 % | 29 |
| ActiveOps | AOM.L | 53 | 49.07 % | 31 |
| STIF | ALSTI.PA | 54 | 50.0 % | 34 |
| MEMSCAP | MEMS.PA | 53 | 49.07 % | 33 |
| Firan Technology | FTG.TO | 56 | 51.85 % | 38 |
| Electrovaya | ELVA.TO | 53 | 49.07 % | 33 |
| Covalon Technologies | COV.V | 51 | 47.22 % | 31 |
| ROK Resources | ROK.V | 51 | 47.22 % | 35 |
| Made Tech Group | MTEC.L | 56 | 51.85 % | 32 |
| Zoomd Technologies | ZOMD.V | 53 | 49.07 % | 33 |
| CEMATRIX | CEMX.TO | 51 | 47.22 % | 36 |
| CTT Systems | CTT.ST | 52 | 48.15 % | 37 |
| ICAPE Holding | ALICA.PA | 53 | 49.07 % | 38 |
| Plejd | PLEJD.ST | 54 | 50.0 % | 36 |
| Software Circle | SFT.L | 49 | 45.37 % | 34 |
| Tristel | TSTL.L | 55 | 50.93 % | 37 |
| Generic Sweden | GENI.ST | 50 | 46.3 % | 34 |
| Light Science Technologies | LST.L | 46 | 42.59 % | 31 |
| Growens | GROW.MI | 42 | 38.89 % | 24 |
| Hardide | HDD.L | 50 | 46.3 % | 31 |
| Kenorland Minerals | KLD.V | 45 | 41.67 % | 30 |
| Sidetrade | ALBFR.PA | 55 | 50.93 % | 34 |
| Cerillion | CER.L | 54 | 50.0 % | 38 |
| Transense Technologies | TRT.L | 48 | 44.44 % | 33 |
| Pulsar Group | PULS.L | 49 | 45.37 % | 32 |
| Hargreaves Services | HSP.L | 55 | 50.93 % | 36 |
| Broadpeak | ALBPK.PA | 38 | 35.19 % | 22 |
| Entech | ALESE.PA | 49 | 45.37 % | 25 |
| Diagnostic Medical Systems | ALDMS.PA | 50 | 46.3 % | 36 |
| StreamWIDE | ALSTW.PA | 50 | 46.3 % | 35 |
| Sogeclair | ALSOG.PA | 52 | 48.15 % | 36 |
| Mon Courtier Énergie Groupe | ALMCE.PA | 49 | 45.37 % | 35 |
| 2CRSi | AL2SI.PA | 52 | 48.15 % | 27 |
| WALLIX | ALLIX.PA | 51 | 47.22 % | 31 |
| Arcure | ALCUR.PA | 47 | 43.52 % | 26 |
| IEVA | ALIEV.PA | 41 | 37.96 % | 24 |

## Collecte et conservation

- 120 requêtes de recherche tracées pour les 40 sociétés : publications financières, Zonebourse/consensus, transactions d’initiés. Ces recherches ne sont pas exhaustives et leurs titres ne valent pas preuve d’une donnée.
- Statistiques financières collectées pour 40/40 cotations, profils et historiques annuels pour 40/40; Plejd rapproché à la cotation Spotlight du fournisseur, sans changer le ticker de la cohorte.
- Prévisions annuelles publiques recherchées pour 40/40; les valeurs masquées par `Upgrade`, les devises non explicites et les erreurs de page restent manquantes. Les BPA ajustés sont distingués des BPA comptables.
- Identités et Companyfacts SEC récupérés pour les cinq émetteurs US. Calculs TTM sur exercices et cumuls de durées identiques; extraits XBRL utilisés livrés avec empreintes des réponses complètes.
- 125 formulaires SEC Form 4 / 4-A effectivement lus et analysés, hors un échec technique; montants P/S uniquement, fenêtres et amendements contrôlés. Les agrégats 180 jours de Crexendo et Lifeway restent bloqués.
- Valeurs et métadonnées déjà renseignées dans les 40 fichiers de départ conservées exactement. Les publications nouvelles sur un champ déjà vérifié figurent dans `observations_complementaires`; la cellule d’origine peut donc conserver un arrêté plus ancien.
- Aucune modification du coffre maître, des pondérations ou du référentiel. Aucune note inventée et aucun ordre réel.

## Contrôles techniques

15 tests passent : cohorte/identité, conservation des données antérieures, métadonnées complètes, manquants explicites, absence de score/ordre, GBp vers GBP, historique court IEVA, absence de n/a transformé en zéro, conflits de cours, fenêtres initiés, taux de couverture, raccordement, recherches par société, nombres finis et réexécution idempotente.

L’adaptateur `09S_ADAPTATEUR_FICHES_MCPA_40.py` s’exécute correctement et renvoie **0/40 fiches éligibles**. Il conserve la revue existante. Ce résultat valide le raccordement technique et le refus des dossiers non validés; il ne démontre pas un filtrage financier opérationnel des 40 valeurs.

Cours techniques : dernière séance archivée au plus tard le 3 novembre 2026, pour éviter d’utiliser la séance US du 4 novembre avant sa clôture. Ratios fournisseurs : instantané du 4 novembre, explicitement distinct de la date des cours techniques. Périodes et devises ne doivent pas être fusionnées sans contrôle.

## Informations encore manquantes et limites réelles

- Révisions du consensus BPA à 30/90 jours : séries datées comparables non collectées; ni variation d’objectif de cours ni changement de guidance ne les remplace.
- Registres exhaustifs d’initiés hors États-Unis non reconstitués. Une transaction isolée retrouvée ne suffit pas à produire un net de 90/180 jours.
- Plusieurs prévisions, PEG, données de gouvernance, concentration client, revenus récurrents, refinancement, risques réglementaires, historique de valorisation et données de marché adressable restent à documenter et à analyser.
- Les montants financiers secondaires doivent être rapprochés des comptes primaires : périmètre des activités poursuivies, conversion de devises, traitement des locations et actifs destinés à la vente. Les anomalies de marge brute de 2CRSi, Sidetrade et Generic ne sont pas importées comme preuves primaires.
- Le bloc complémentaire (SSI, IC/CX, scénarios, probabilités, décisions) et les sous-notes MCPA restent vides.
- EODHD : aucune clé n’est disponible dans l’environnement local de cette exécution. Il ne s’agit pas d’une preuve d’indisponibilité des données chez le fournisseur.
- Limite intrinsèque constatée pour IEVA : historique archivé inférieur à 200 séances et à 12 mois; MM200 et momentum 12 mois impossibles à calculer fidèlement sur cet historique.

**Aucune information n’est déclarée « définitivement indisponible »** : pour les autres manquants, l’indisponibilité définitive n’a pas été démontrée. Les recherches restent explicitement non closes. Le détail champ par champ figure dans `AUDIT_40.json` et dans chaque fiche.

## Alertes à conserver dans la revue

2CRSi : impossibilité annoncée de certification des comptes. InfuSystem : revue du traitement comptable des coûts ERP. ActiveOps : risque de non-renouvellement d’un client majeur en mars 2027. STIF : perte annoncée du client Tesla sur Megapack 3. Cerillion : prévisions abaissées après reports de commandes. Ces éléments n’équivalent pas à une décision d’arbitrage.

## Fichiers utiles

- `DONNEES/COUVERTURE_FICHES_40_20261104.csv` : couverture des 40 sociétés.
- `AUDITS/FINALISATION_FICHES_20261104/AUDIT_40.json` : manquants par champ et résultats.
- `TESTS/test_finalisation_fiches_40.py` : audit reproductible hors réseau.
- `SCRIPTS_ACTIFS/09U` à `09Z` : collectes et enrichissement datés; aucune chaîne d’ordres.

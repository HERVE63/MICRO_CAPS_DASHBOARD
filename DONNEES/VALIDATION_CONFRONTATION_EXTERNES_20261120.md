# Confrontation externe vérifiée — 20 novembre 2026

Branche : repair/microcaps-chain-20261030. Main et maîtres figés inchangés.

## Résultat réellement exécuté
- Référence : clôtures du 19 novembre 2026.
- 4 dossiers externes relus individuellement dans Zonebourse Premium : SRT Marine Systems, Eleco, Pro-Dex, Kewaunee Scientific.
- 37 positions actives avec données momentum validées, sur 39 positions actives ; cohorte initiale couverte 38/40.
- 148 confrontations (4 × 37). 0 candidat admissible et 0 nouvelle opération externe.
- SRT, Pro-Dex et Kewaunee : momentum non confirmé sur les cinq horizons.
- Eleco : offre en numéraire 235 pence, dernière clôture 234 pence ; écart brut 0,427 % inférieur aux frais d'une rotation. Sources officielles dans CONFIG/CANDIDATS_EXTERNES_MOMENTUM.json.
- Les deux écritures de la rotation interne SFT.L vers MTEC.L déjà exécutée restent conservées. Frais cumulés 4,260178870469337 EUR. Aucune écriture ajoutée par la confrontation externe.
- Journal SHA256 : 1eac2a5b42507a0b28a4c5fb54de4bb349a23a349fc2c257f540c68042c340ce.

## Tests et preuves
GitHub Actions : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/44769687752
Résultat : succès, 31 tests passés, contrôle de couverture validé au seuil 35/40.
Code : b2cbe9e79f1ad907190687281d78f4640d1c2307.
Résultats : 6946919d308ba11b4395f8b739a2fc3dd692f01e.
Fichiers : DONNEES/ETAT_CONFRONTATION_EXTERNES.json, CANDIDATS_EXTERNES_MOMENTUM.csv, CONFRONTATION_MOMENTUM_EXTERNES.csv, VIGILANCE_EXTERNES_QUOTIDIENNE.csv et ZONEBOURSE_EXTERNES/2026-11-20/.

## Vigilance
7 133 cotations/tickers incomplets sur 7 137 répertoriés. Il ne s'agit pas de 7 137 sociétés distinctes certifiées. Les archives ne constituent pas des cours actualisés.
Tâches quotidienne 22h30 Europe/Paris et revue du mardi mises à jour : relecture des candidats déjà validés, collecte progressive de dix nouvelles priorités au maximum par passage, contrôle de l'identité/ISIN et de la place principale, puis réintégration uniquement après contrôles réussis.
Aucune visite quotidienne exhaustive des 7 133 lignes n'est revendiquée ; l'exécution des prochains passages reste à vérifier.
Plejd et Pulsar conservées hors arbitrage tant que les données manquantes ne sont pas validées.

## Affichage livré
https://microcaps-momentum.goodborage.chatgpt.site/
Site privé, authentification ChatGPT du propriétaire requise.
Déploiement confirmé réussi : appgdep_6b007181016c819199bd1239fe79fdf6.
Source du site : dd2293eb21c01b2e02f2dad33b1f2b5859c13b93.
Le HTML et momentum-data.json proviennent exactement du résultat GitHub 6946919.
Vérification navigateur de l'aperçu : données GitHub chargées, quatre onglets fonctionnels, quatre candidats et leurs décisions, 148 confrontations, recherche Bitzero dans l'extrait de vigilance, journal de deux écritures/frais 4,26 EUR, MTEC 310,4112 titres et SFT sorti.
Contrôle visuel sur ordinateur effectué. Format mobile réel non vérifié.
En production, page de connexion privée observée : contenu après connexion non vérifié dans ce navigateur. Aucun changement des droits pour contourner cette protection.
La nouvelle vue est distincte de l'ancienne page publiée depuis main. Aucune mise à jour de l'ancienne icône n'est revendiquée.
Le site recharge les données du fichier APPLICATION/momentum-data.json sur la branche autorisée à l'ouverture, sur demande et toutes les cinq minutes ; la date reste visible. Les GitHub Actions génèrent ce fichier. En cas d'échec réseau, l'instantané daté est explicitement indiqué.

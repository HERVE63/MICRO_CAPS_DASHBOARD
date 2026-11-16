# Exécution Micro Caps du 16 novembre 2026

## Résultat de collecte

0/40 relevés complets actuellement validés pour ce passage. Une lecture Premium partielle de Broadpeak est conservée avec son URL et son heure de consultation. Les relevés du 15 novembre sont archivés à leur date, sans promotion à la date du 16.

Broadpeak : 1,645 EUR, 16/11/2026 11:40:40 (heure affichée), variation publiée +0,92 %, cinq séances -0,30 %. Dernière clôture disponible dans le tableau : 1,630 EUR le 13/11, volume 1 199 titres. Historique 1 mois : 1,505 EUR au 16/10 ; 2 mois : 2,120 EUR au 16/09. Historique trois mois non récupéré ; aucun signal validé ni rang attribué.

## Blocage technique constaté

Après une lecture de la page Premium et deux historiques, les commandes du navigateur Work expirent et réinitialisent le noyau. Erreur précise : « CDP operation exceeded its deadline before command dispatch ». La récupération de l’onglet et la lecture ciblée du tableau échouent aussi. Le contrôle visuel affiche le navigateur sans réaction au changement d’onglet. Aucune preuve de blocage anti-robot ni de déconnexion Premium. Aucun contournement et aucune donnée d’un autre fournisseur.

## Calculs et tests

Le moteur existant, ses tests d’intégration et ZONEBOURSE_MOMENTUM_40_GATE.py sont exécutés par GitHub Actions sur ce commit. Les résultats et preuves sont archivés par ce workflow. Le contrôle 40/40 doit rester en échec tant que les relevés sont incomplets. Une correction distingue le volume de la dernière séance terminée du volume cumulé intrajournalier, et exige leur présence avant validation.

Les tentatives locales ont constaté l’absence de pytest et pandas_market_calendars dans le runtime renouvelé. GitHub installe ces dépendances ; le résultat distant fait foi. Le contrôle d’intégrité T0 local passe.

## Arbitrage

Statut : COLLECTE_INCOMPLETE, aucun arbitrage autorisé. Le portefeuille témoin et le journal virtuel ne sont pas modifiés. Le capital T0 reste de 4 000 EUR par portefeuille ; frais 2,5 % par côté. Le classement et les alertes complètes ne peuvent pas être validés avec ces données. Pulsar reste sous le verrou de suspension déjà documenté ; Plejd nécessitait déjà une résolution de ses cotations anciennes. Les 40 statuts et les champs calculables sont exportés par le moteur, sans invention des champs manquants.

Branche exclusivement : repair/microcaps-chain-20261030. main et les maîtres figés restent inchangés.

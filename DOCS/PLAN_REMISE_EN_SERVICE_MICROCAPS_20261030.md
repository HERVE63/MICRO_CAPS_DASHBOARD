# MICRO CAPS — plan de remise en service et critères de réception (30 octobre 2026)

**Document de travail, non constitutif de la sauvegarde finale.** Branche de réparation isolée `repair/microcaps-chain-20261030`, PR n° 1 en brouillon. Aucune fusion en production sans preuve de bout en bout. Les coffres maîtres, le T0, les historiques officiels, le CPI et les ETF Assurance-Vie sont hors périmètre de modification.

## Constat vérifié dans le dépôt

- La chasse hebdomadaire du 28/10/2026 a traité 5 737 tickers ; 5 398 métriques de marché ont été disponibles, 339 manquantes. Le registre de chasse contient 31 352 **détections** (événements historiques, pas 31 352 entreprises uniques). Le fichier `CHASSE_CANDIDATS.csv` existe et pèse 5 429 763 octets ; sa réponse vide dans certains outils de lecture ne prouve **pas** qu'il soit vide.
- `DONNEES/AUDIT_DOSSIERS_SSI.csv` : 1 361 dossiers préparés, zéro note SSI documentée/admission dans cette chaîne de préparation.
- Archive US `AUDITS/SCE_DISCOVERY_US/20261018T163259392136Z/MANIFESTE.json` : 2 490 cotations, 2 dossiers SSI complets, 1 admission SSI, couverture 0,0803 % (univers distinct du registre de chasse).
- Archive `AUDITS/LISTE_PERMANENTE_US/20261018T163321370926Z/MANIFESTE.json` : 1 analyse MCPA, 0 candidature MCPA ≥80, ni Top 20 ni Top 5 validés. L'analyse CCFN.US donne MCPA 72 et ne doit pas être promue artificiellement.
- `DONNEES/REVUE_HEBDOMADAIRE_MCPA_IPS.csv` ne contient que son en-tête ; les 40 titulaires ne sont pas confrontés.
- `DONNEES/JOURNAL_ARBITRAGES_GERE.csv` ne contient que son en-tête : aucun arbitrage mensuel effectivement démontré.
- Les 40 lignes du portefeuille virtuel et les 3 benchmarks sont valorisés au 29/10/2026. Portefeuille géré et témoin : 3 950,99 € chacun, alpha 0. Il ne s'agit pas d'une preuve de fonctionnement de la gestion active.
- L'échec du workflow mensuel du 28/10/2026 se produit lors de `git pull --rebase` à cause de modifications non indexées. Correctif enregistré **sur la branche isolée uniquement**, sans validation de production.

## Chaîne cible et conditions de passage

1. **Conservation et identité.** Vérifier empreintes T0, 40 identités, devises, sources, absence de doublons, intégrité des fichiers suivis. Jamais de correction silencieuse d'une cohorte figée.
2. **Chasse.** Univers US/Canada/Europe, filtrage microcaps 50–300 M€, datation des sources, identité de l'émetteur et cotation primaire, volumes et momentum ; enregistrer les rejets et les manquants.
3. **Présélection.** Alimenter les candidats prêts SSI à partir des variables fondamentales et marché observées. La chasse et la présélection doivent partager une clé d'identité explicite ; une cotation secondaire ne doit pas être prise pour une société nouvelle.
4. **SSI documentaire.** Sept blocs notés seulement sur pièces traçables et archivées, avec contrôle de date, d'émetteur et d'empreinte. La couverture de qualification de l'univers US doit atteindre au moins 50 % avant de déclarer le classement représentatif (objectif ultérieur 90 %). Aucun remplissage automatique des `MANQUANTE`.
5. **MCPA/IPS.** Pour les dossiers SSI admis (≥65), produire six sous-scores Q/V/G/R/M/D pondérés 30/20/20/10/10/10, IC/CX, WWWS, scénarios 3–6 mois, preuves, révisions, momentum, insiders et risques. Un challenger investissable exige MCPA ≥80, admission SSI actuelle, analyse validée et comparaison explicite au titulaire.
6. **Comité du mardi.** Revoir **les 40 positions actives** et les challengers, puis produire les duels « prochain euro » avec décision motivée. Aucune revue vide ou antidatée ne vaut validation.
7. **Arbitrage mensuel.** Exécuter uniquement dans la fenêtre permise et avec duels validés, 2,5 % à la vente et 2,5 % à l'achat, conservation du témoin T0. Tester le rejeu, l'idempotence, les frais, les espèces, les anomalies de prix et l'absence d'écriture hors fenêtre.
8. **Tableau de bord.** Afficher les 40 valeurs, géré, témoin, 3 benchmarks, date de clôture, SSI/MCPA et challengers **réellement admis**, sur mobile et ordinateur. Les chiffres de chasse, les dossiers SSI et les challengers doivent être distingués.
9. **Recette intégrale.** Exécuter l'audit `08C_AUDIT_CHAINE_COMPLETE.py` et les tests isolés GitHub Actions ; confirmer la conformité des journaux, la couverture des titulaires, les empreintes et l'absence de modification des données maîtres. Un succès technique de GitHub Actions n'est **pas** une recette fonctionnelle.
10. **Sauvegarde finale, seulement après recette.** Créer séparément `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avec document scientifique français, synoptique des modules, scripts, configurations, références, documentation et manifeste SHA-256 vérifié. Ne pas modifier les archives existantes. Signaler emplacement et contrôles d'intégrité uniquement une fois l'ensemble validé.

## État de réception

**NON REÇU — SAUVEGARDE INTERDITE.** La détection et la valorisation quotidienne fonctionnent, mais SSI/MCPA, revue exhaustive, challengers admissibles, affichage effectif de challengers et arbitrage mensuel validé ne sont pas démontrés. Les tests isolés vérifient explicitement que l'audit refuse une sauvegarde dans cet état.

## Précautions de reprise

Le workflow hebdomadaire historique n'exécute pas les modules 07Q/07R ni la notation MCPA ; les chaîner sans validation des sources risquerait d'écraser les champs humains et de publier des résultats sans preuve. Les archives SSI US et la chasse généraliste sont des univers distincts : ne pas additionner leurs compteurs. Toute nouvelle intégration doit être testée sur une copie temporaire avant publication.

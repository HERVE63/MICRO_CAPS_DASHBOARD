# Passage de contrôle — 30 octobre 2026, soirée (Europe/Paris)

## Réutilisation des archives avant développement
- GitHub : modules existants 07Q, 07R, preuves_ssi et test_pipeline_hebdo_isole relus. Aucun nouveau moteur SSI créé.
- Google Drive : dossier historique PRICE02A (ID 1_g42pXqd_XeYpzbh7eN5_7GyEuCSsFoD) inspecté directement.
- Fichier réellement présent : PRICE02A_MONTHLY_SIGNALS.parquet, ID 1CCBaaoMClsjtqsH0jtRbb38fu97oOJO3, 9 558 146 octets, dernière modification 2026-08-23T18:20:35.883Z.
- Sous-dossier raw_prices, ID 1NPSKBNWOq3YndFUUTLZhHFVixOuQzFBo : fichiers .parquet individuels visibles, notamment __SPY__.parquet, ZTS.parquet, ZION.parquet. Il s'agit d'un inventaire de métadonnées, pas d'une validation de schéma, de période ou de SHA256.
- DATA04_EODHD_FUNDAMENTALS (ID 1X3H4xuyODnmDST2ttFdNbGNfzCh4XmHA) : aucun enfant directement listé.
- Recherches Drive exactes FUND02E et FUND03A : aucun résultat. Ne pas reconstruire ces modules sans poursuivre la recherche des sauvegardes.
- Aucun fichier Drive n'a été modifié, ni raccordé sans inspection de schéma.

## Défaut critique 07Q et correction
Ancien comportement : à ticker égal, la préparation 07Q remplaçait sans condition le CIK de la nouvelle source par le CIK de l'ancien registre, et réutilisait ses preuves et annotations. Une réattribution de ticker pouvait ainsi propager les preuves d'un autre émetteur.

Correction en branche isolée :
- CIK de la nouvelle source conservé lorsqu'il est renseigné ; reprise de l'ancien seulement en cas de CIK source manquant.
- Divergence entre deux CIK renseignés : seul le dossier concerné est mis en quarantaine `EN_ATTENTE_DATA_IDENTITE_CIK`, les annotations, notes, preuves SCE et décisions antérieures sont invalidées ; les autres candidats continuent.
- L'ancien registre est archivé avant remplacement. L'audit indique le nombre de conflits CIK.
- Aucune note ou preuve nouvelle n'est produite.

Commits : c188ed826d3d57d97be370f50981db4e9a722a04 (correction), fbc9f63c8435b7c5ba3c33795b094c3d00fa49e2 (régression sur cohorte temporaire), 1f17b8640960a8ae44ac2a819a818b5439c888af (raccordement du test à CI).

## Contrôles et limites
- Le test ajouté `TESTS/test_07q_collision_identite_cik.py` crée trois candidats fictifs dans un dossier temporaire : CIK absent, collision CIK, nouvel identifiant ; vérifie l'archivage et la poursuite de la cohorte.
- La suite `test_reparation_microcaps.yml` déclenchée par push inclut désormais ce test. Résultat CI du nouveau commit : **à vérifier**, ne pas déclarer un succès sans exécution constatée.
- Aucun arbitrage, aucune fusion main, aucun changement de portefeuille témoin ou de coffre maître.
- Étape suivante : confirmer CI ; inspecter schémas/dates/empreintes PRICE02A et autres archives avant raccordement ; puis documenter les preuves primaires SCE/SSI, sans score imputé.

# MICRO CAPS — passage du 31 octobre 2026, 20:10–20:12 UTC

## État vérifié avant modification
- PR brouillon #1 ouverte, non fusionnée ; branche `repair/microcaps-chain-20261030`.
- Tête initiale : `c4da68490a933cd8d7e6afd619c0e2e8a2383267`.
- Registre `DONNEES/CHASSE_CANDIDATS.csv` : blob Git de **5 429 763 octets**, et non fichier vide. La lecture partielle par API GitHub peut retourner une chaîne vide pour ce gros fichier ; ne pas interpréter cette limite de lecture comme une perte de données. Le test historique en CI vérifie **31 352 détections**, dont **5 737** présentes dans la sortie du screener.
- Archives Drive inventoriées avant modification : `PRICE02A/PRICE02A_MONTHLY_SIGNALS.parquet` (9 558 146 octets) et `SEC_BRIDGE` (fichiers historiques SEC présents). `DATA04_EODHD_FUNDAMENTALS` sans enfant visible ; recherches `FUND02E` et `FUND03A` sans résultat.
- Les 18 faits financiers existants ICAPE/Fermentalg, les collecteurs 07AA, le raccordeur 07Q3 et les tests IFRS archivés ont été réutilisés, sans nouvelle collecte ni notation.

## Défaut corrigé
Dans `07Q3`, la construction `{r["Ticker"]: r for r in lignes_csv(...)}` écrasait silencieusement une identité précédente si le fichier SSI comportait deux dossiers de même ticker. Cela pouvait faire dépendre la concordance documentaire de l'ordre des lignes. Désormais, **tout ticker dupliqué**, même si ses identités sont égales, est isolé avec `EN_ATTENTE_DATA_IDENTITE_AMBIGUE`. Les autres tickers poursuivent le contrôle de provenance, de dates et de SHA256 sans interruption. Les scores restent `MANQUANTE`.

## Modifications et tests exécutés
1. Commit `ae2beca5bb6b8fd22ed35c391831496b14032088` : garde anti-collision dans `SCRIPTS_ACTIFS/07Q3_RACCORDER_FAITS_FINANCIERS_NON_CERTIFIES.py`.
2. Commit `74ec4c9114a9fb880a39cc526844515ceb0b02c9` : tests adverses hors réseau avec deux dossiers du même ticker et ISIN divergents, puis identiques ; quarantaine des neuf lignes du ticker et traitement des neuf autres.
3. CI isolée [41237667275](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41237667275) : **success** sur `74ec4c91`. Elle inclut le test 07Q3, le registre CHASSE, les modules SSI, les duels et le contrôle fail-closed de complétude.
4. Replay virtuel isolé [41237667313](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41237667313) : **success** sur `74ec4c91`.
5. Préparation SSI [41237657447](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41237657447) : **success** ; publication automatique `f438f9bb41188592aa1024de7b43122ced67f892` ne modifiant que `DONNEES/AUDIT_SSI.csv`.

## État et limites
- Audit 07Q3 publié : **18 observations**, **2 dossiers**, **18 EN_ATTENTE_DATA**, **0 note attribuée**.
- Ce passage ne certifie aucune identité SCE, aucun bloc SSI, aucun challenger MCPA/IPS et aucun arbitrage économique. Les tests avec identité fictive ne constituent pas des qualifications réelles.
- Aucun fichier de `main`, des historiques officiels, du coffre `MICRO_CAPS_DOSSIER_TRANSMISSION_V3_MAITRE`, de CPI ou d'ETF AV n'a été modifié dans les commits de ce passage.
- PR conservée en brouillon ; aucune transaction réelle, aucune fusion et **aucune** sauvegarde finale `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME`.

## Étape critique suivante
Certifier de manière indépendante les identités SCE (émetteur, ISIN, cotation fournisseur, deux preuves primaires distinctes et SHA256), puis compléter les sept blocs SSI ; ne promouvoir que les candidats réellement admissibles à SSI >=65 et MCPA/IPS >=80. Maintenir `EN_ATTENTE_DATA` et le traitement individuel pour les dossiers incomplets.

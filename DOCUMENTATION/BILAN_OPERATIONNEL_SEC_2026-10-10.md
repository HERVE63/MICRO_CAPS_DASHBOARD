# Réception opérationnelle MICRO CAPS — 10 octobre 2026

Le secret SEC est utilisable, les six modules SEC sont exécutés, les réponses brutes et leurs empreintes sont sauvegardées dans GitHub. La collecte fonctionne ; la qualification et la sélection finale ne sont pas terminées.

## Résultats effectivement mesurés

| Contrôle | Résultat |
|---|---|
| Périmètre conservé | 1 361 dossiers, sans nouvelle chasse |
| Pistes SEC par nom ou ticker exact | 245, aucune identité validée automatiquement |
| Dossiers avec faits financiers bruts | 234 |
| Faits distincts après consolidation numérique | 185 432 |
| Faits normalisés et rapprochés des blocs SSI | 70 078 |
| Pistes documentaires de gouvernance | 3 974 |
| Transactions Form 4 à vérifier | 4 030 |
| Erreurs de téléchargement de données financières | 9 réponses HTTP 404, conservées et bloquantes pour les dossiers concernés |
| Réponse financière sans CIK concordant | 1 dossier rejeté : 2W9.F, CIK demandé 0001790169, champ CIK absent dans la réponse |
| Piste sans fait financier retenu | 1 : 000.F |
| Dossiers sans rapprochement SEC | 1 116 ; ce nombre ne signifie pas exclusion financière |
| SSI admis / challengers MCPA validés | 0 / 0 |
| Opérations exécutées | 0 |

La dernière relecture GitHub [38055875295](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38055875295) est terminée : tests réussis, six étapes SEC exécutées, consolidation réussie, sources hors SEC contrôlées, bilan et sauvegarde réussis. Son statut global reste en échec pour les neuf erreurs source : sauvegarder ses résultats ne transforme pas une collecte partielle en réussite complète.

Les neuf réponses 404 concernent 2F60.F, 0PL.F, B40.F, SO6.F, G12.F, 3XS0.F, AGX.F, 6H90.F et CHC1.F. Elles prouvent que les URL companyfacts demandées ne fournissent pas de fichier exploitable ; elles ne prouvent ni insolvabilité ni absence de toute publication. Les données alternatives doivent venir des rapports officiels des émetteurs ou des autorités compétentes.

Pièces finales sauvegardées dans le dépôt :

- `AUDITS/SEC/RUN_38055875295_1/MANIFESTE.json` et `DONNEES/AUDIT_FAITS_FINANCIERS_SEC_SSI.csv` dans cette archive : secret contrôlé, dates, étapes, erreurs HTTP et empreintes.
- `AUDITS/SEC_CONSOLIDE/20261010T133017280444Z/MANIFESTE.json` : cinq archives contrôlées, 185 432 observations distinctes, 234 dossiers couverts, zéro divergence de valeur.
- `AUDITS/SELECTION/20261010T133018290290Z/BILAN.json` : T0, frais, journal vide, zéro admission et blocages.
- `AUDITS/SOURCES_OFFICIELLES/20261010T132940591629Z/AUDIT_DOCUMENTS.csv` : Hofseth collecté et Fermentalg bloqué.

Les 3 239 divergences signalées par la première consolidation étaient dues à des représentations numériques différentes, par exemple `10` et `10.0`. Le correctif compare les valeurs avec Decimal, conserve les représentations et les archives d'origine, et continue à signaler les véritables écarts. Ses relectures locale et GitHub des archives authentiques donnent 185 432 observations distinctes et zéro divergence de valeur. Le test utilise à la fois une égalité de représentation et une vraie différence, et refuse une archive dont l'empreinte a changé.

## Tests exécutés

Les **14 fichiers de tests** passent localement et dans [GitHub Actions 38055875164](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/38055875164), commit `3d6ee3e96f76e92981398cb2208fb1e26112f98c`.

Ils couvrent les modules SEC, l'isolation des chemins temporaires, plusieurs XML Form 4, la concordance du CIK émetteur, les cotations multiples, IFRS et les devises, la relecture sans réseau, la corruption d'archives, la conservation des corrections humaines, le verrou SSI, les frais, le calendrier, le contrôle du T0 et les sources officielles hors SEC. Une réussite hors réseau vérifie ces comportements ; elle ne certifie pas les comptes d'un émetteur.

Une relecture supplémentaire des dix premiers dossiers, avec les connexions réseau explicitement interdites, a utilisé 209 réponses archivées, effectué zéro téléchargement et ajouté les faits IFRS jusque-là omis. Son reçu est conservé dans `AUDITS/RELECTURES_SEC/2026-10-10/BILAN_RELECTURE_LOCALE.json`.

## Sources hors SEC

Le PDF Q2 2026 de Hofseth BioCare, publié le 21 août 2026 et référencé par le site de l'émetteur, est effectivement téléchargé et archivé. SHA-256 : `46b6b8b1fd0e73a6a18f1320c5dd457bd8f35499a1eacae3a06ff471c41801c6`. Sa collecte n'est ni une vérification de tous ses chiffres ni une admission SSI.

Le document Fermentalg configuré renvoie HTTP 403. Deux documents seulement sont configurés : **1 359 dossiers restent sans document officiel hors SEC configuré**. Les pistes d'identité Hofseth, Fermentalg et Techprecision sont enregistrées comme pistes à archiver et confirmer, sans validation fictive.

## Intégrité et décisions

Le bilan exécuté confirme 40 lignes T0 du 1er octobre, 100 € par ligne, 4 000 € dans chaque portefeuille initial, T0 identique à sa sauvegarde, et journal d'arbitrages vide. Les paramètres imposent revue le mardi, arbitrage mensuel et exception grave documentée. Les trois benchmarks sont présents et leur empreinte initiale est protégée ; cela ne constitue pas une mise à jour de leurs cours au 10 octobre.

Les frais sont de 2,5 % sur chaque côté. Une rotation complète de 100 € laisse 95,121951 € investis après vente puis achat selon les conventions du moteur. Le contrôle hors fenêtre refuse un forçage réel non documenté.

Les réponses originales, dates de collecte, dates d'extraction et empreintes sont distinctes. Les dépôts postérieurs à la date d'analyse sont écartés. La réutilisation d'une réponse ne la présente pas comme un nouveau téléchargement. Les entrées et positions restent contrôlées avant/après la collecte. CPI, ETF Assurance-Vie et coffre maître V3 ne sont pas modifiés ; l'archive maître retrouvée a uniquement été lue et son empreinte vérifiée avant/après.

## Travail restant avant toute sélection

1. Confirmer les identités ISIN–cotation–émetteur–CIK et les périodes ; maintenir les rejets de CIK discordants, y compris dans Form 4.
2. Compléter les sources officielles hors SEC et les preuves B1 à B7. Le barème SSI qualitatif retrouvé est enregistré dans `CONFIG/BAREME_SSI_V1_0.json` ; aucun intervalle n'est converti automatiquement en note.
3. Produire des notes justifiées sur preuves vérifiées ; atteindre SSI ≥65 avant admission. La présence de 185 432 faits ne fournit pas à elle seule B4, B5, B6 et B7.
4. Alimenter la revue MCPA/IC/CX/Δ/WWWS et IPS validée, actuellement vide ; MCPA ≥80 ne déclenche aucun achat.
5. Rendre exécutable le SCE-Discovery décrit par les documents maîtres. Les documents retrouvés décrivent l'architecture, pas un moteur complet ni tous les seuils numériques du screening. Ne pas importer les quotas d'une autre expérience ni inventer les seuils manquants.
6. Seulement alors publier Top20/Top5, confronter les challengers aux 40 titulaires et documenter le prochain euro avant arbitrage mensuel.

Le classement final, les Top20/Top5 et les décisions restent vides ou bloqués : **aucune meilleure valeur n'est déclarée validée**.

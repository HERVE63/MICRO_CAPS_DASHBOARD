# Réception MICRO CAPS — 9 octobre 2026

## Périmètre verrouillé

Qualification des 1 361 dossiers déjà préparés. Pas de nouvelle chasse pour remplacer ce lot.
Le SSI demeure un sas de microcaps avant MCPA/IPS, et ne remplace pas SCE-Discovery.
Aucun seuil économique absent des documents maîtres n'est ajouté.
Aucune donnée absente n'est imputée. Les workflows CPI/ETF et le coffre maître V3 sont hors périmètre.

## Preuves initiales d'exécution

- Commit audité initialement : `c6793563bb6d7917ebd2a95d5744e2d0a1cf626f`.
- Sept tests SEC exécutés localement : codes retour 0.
- Réception GitHub des sept tests déjà confirmée dans le run `37837934976` ; journaux contrôlés.
- Nouvelle réception et tentative SEC effectivement exécutées dans le run `37964548680`, commit `4372fcb91e935589d8f444118e194026bdd9f65f`.
- Réception hors réseau : OK ; collecte : BLOQUÉE par `SEC_USER_AGENT_ABSENT_OU_INVALIDE`.
- Aucune étape de collecte SEC exécutée dans ce run. Le manifeste et les entrées ont été sauvegardés au commit `fc4582dd204fd78d9ed7ad2096bb70e83b453f0e`.

## Corrections opérationnelles

- Retrait de caractères `\n` littéraux invalides dans 08S et 09C ; adaptateur relié à l'univers nettoyé.
- Le comité ne relance plus la chasse ; son workflow reste indépendant.
- Runner de tests : syntaxe de tous les modules, réseau interdit, exécution de chaque fichier et contrôle SHA256 des données avant/après. Résultats et empreintes de code exportés.
- Runner SEC : répertoire isolé par run/tentative, entrées copiées, documents bruts hashés, manifeste même en cas d'échec, aucun écrasement des corrections opérationnelles.
- Dates limites : documents et faits postérieurs exclus ; CIK submissions et Form 4 contrôlés.
- Rapprochement SEC : accession, tag, formulaire et période conservés.
- Préparation SSI : notes, preuves et corrections conservées par ticker ; ancien dossier archivé avant rafraîchissement ; admission à revalider.
- Validation SSI : exige un registre de preuves, une identité vérifiée, une source primaire, un document conservé avec SHA256, des dates cohérentes, un vérificateur et une justification de note. Une chaîne de texte seule ne vaut plus preuve.
- Duel : repasse par le contrôle SSI ; les admissions éditées ou périmées sont refusées.
- Revue : nombres finis, bornes, sommes, dates et couverture de toutes les positions actives contrôlées.
- Exécution mensuelle : forçage réel hors fenêtre refusé ; journal candidat vérifié avant publication atomique.
- Références T0 : empreintes du T0, de sa copie figée, de l'état initial et des benchmarks ; contrôle branché avant le moteur quotidien et l'exécution mensuelle.

## Hors SEC

`07AA` collecte des URLs documentaires d'émetteurs/dépôts inscrites dans un registre, avec domaine autorisé et habilitation sourcée. Il conserve les octets et leur empreinte, contrôle les redirections et interdit les adresses privées. Aucune note n'en découle.

Le premier document configuré est un communiqué Fermentalg du 6 octobre 2026, publié par son diffuseur et référencé par la page investisseurs de l'émetteur. La cotation `1F6.F` reste à vérifier : son nom ne suffit pas à certifier son identité. La tentative locale a rencontré un blocage de source ; cela ne constitue pas un document collecté.

Canada : point d'entrée SEDAR+ ; Royaume-Uni : LSE/RNS. Les URLs précises et identifiants des dossiers restent à qualifier. Ces points d'entrée ne sont pas présentés comme des API universelles exécutées.

## Résultat de sélection vérifié

Le bilan `07AB` exécute le validateur SSI sur le lot réel et produit : résultat SSI, Top20/Top5 (vides en l'absence de candidats validés), confrontation des 40 titulaires, couverture et blocages. Aucun ordre ni décision fictive n'est produit.

Au contrôle local : **1 361 dossiers, zéro admission SSI, zéro challenger MCPA validé**. La revue MCPA/IPS opérationnelle est vide. Aucun moteur SCE-Discovery exécutable n'est présent dans le dépôt. Les 1 361 lignes portent la zone de cotation « Allemagne » ; ce champ n'identifie pas le pays réel de l'émetteur. La collecte secondaire a des données vides pour les autres zones : cette couverture ne peut pas servir à conclure que les meilleures valeurs mondiales ont été sélectionnées.

T0 et copie figée identiques, 40 lignes de 100 €, portefeuille témoin et géré de 4 000 € chacun. Journal vide. Frais vérifiés : 2,5 % à la vente et 2,5 % à l'achat. Une rotation de 100 € sans variation de cours laisse **95,121951 €** investis après frais (achat calculé sur le montant hors frais), soit **4,878049 %** de friction.

## Reproduction

```bash
python -B TESTS/executer_tests.py
python -B SCRIPTS_ACTIFS/07AC_CONTROLER_T0.py
python -B SCRIPTS_ACTIFS/07AB_BILAN_SELECTION_DOCUMENTEE.py
```

Le workflow SEC lance d'abord la réception hors réseau, puis la collecte réelle avec le secret SEC_USER_AGENT. Il conserve les audits même si la collecte échoue et exécute indépendamment la collecte hors SEC et le bilan.

Pour lever le blocage SEC, renseigner dans les secrets Actions du dépôt `SEC_USER_AGENT` avec un nom de projet et un vrai contact courriel, puis relancer le workflow. Ne jamais coller le secret dans les scripts ou les journaux. Le lot actuel de cotations allemandes pourra rester non couvert par SEC : le secret n'est pas une preuve d'identité ni une source européenne.

Compléter les sources/identités officielles et les preuves vérifiées avant notation SSI. Le moteur SCE-Discovery et son barème doivent être raccordés depuis leurs véritables sauvegardes ; son absence n'autorise pas à créer une méthode parallèle. Les scénarios 3/6 mois et WWWS doivent être présents dans une revue validée avant classement final et confrontation.

## Réception finale GitHub effectivement contrôlée

Commit de code : `08a5acc610226ad9525640c1202e4cd1aa0f48f5`.

- **11 fichiers de tests hors réseau passent**, confirmés par les journaux du [run 37965994818](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/37965994818). Le test d'orchestration utilise des réponses factices : sa réussite n'est pas un enrichissement réel.
- [Réception replay 37965994888](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/37965994888) : succès sur l'état réel actuel et son journal vide.
- [Réception duel 37965994970](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/37965994970) : succès sur scénarios de test.
- [Préparation SSI 37965994998](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/37965994998) : succès ; l'ancien fichier de dossiers est archivé et les notes/corrections préservées.
- [Exécution opérationnelle 37965994849](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/37965994849) : tests réussis, SEC bloquée (secret non transmis), tentative du document hors SEC bloquée HTTP 403, bilan et sauvegardes réussis.

Le [bilan réel](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/blob/main/AUDITS/SELECTION/20261009T172428548373Z/BILAN.json) confirme **1 361 dossiers / 0 admis SSI / 0 challenger validé / T0 OK / 0 opération**. Les Top20/Top5 sont vides, avec motifs documentés. Aucune sélection finale n'est déclarée achevée.

Limites restantes : sources officielles et identités du lot à compléter, secret SEC indisponible au workflow, SCE-Discovery exécutable absent, revue MCPA/IPS vide, absence de qualification documentée permettant un classement. La collecte hors SEC fournit le raccordement testé et un audit d'échec réel ; elle ne fournit pas encore une couverture mondiale.

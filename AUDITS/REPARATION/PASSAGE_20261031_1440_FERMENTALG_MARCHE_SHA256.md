# Passage autonome — 31 octobre 2026, 14 h 40 (Paris)

## Inventaire préalable et reprise

PR #1 brouillon, branche `repair/microcaps-chain-20261030`, tête avant intervention `798b3a3016e5d4453cca5bbf41d1883708c881ac`.
Registre `DONNEES/CHASSE_CANDIDATS.csv` non vide (5 429 763 octets) et collecte financière Fermentalg du 31/10 à 12:00:58 UTC déjà présente : **réutilisées**, non reconstituées.
Recherche Drive : PRICE02A et SEC_BRIDGE retrouvés, DATA04_EODHD_FUNDAMENTALS retrouvé comme dossier ; FUND02E et FUND03A non retrouvés. Aucun schéma historique non validé n'a été importé.
Collecteur `SCRIPTS_ACTIFS/07AA_COLLECTE_DOCUMENTS_OFFICIELS.py` et tests existants réutilisés, sans réécrire le collecteur.

## Nouveau fait documentaire primaire (sans certification SCE)

Fiche de marché officielle Deutsche Börse : https://live.deutsche-boerse.com/equity/fermentalg-eo-04
- Émetteur affiché : FERMENTALG ; ISIN : `FR0011271600` ; symbole de marché : `1F6` ; place : Frankfurt.
- Document brut acquis le **31/10/2026 à 13:40:22.160074 UTC**, type `text/html; charset=utf-8`, via 07AA, chemin :
  `AUDITS/SOURCES_OFFICIELLES/20261031T134022160074Z/fb19577446061d121b4c8366422d650a8eee58fc390a27efaf6ab432b76908f5.bin`
- SHA256 du brut : `fb19577446061d121b4c8366422d650a8eee58fc390a27efaf6ab432b76908f5`.
- Manifeste : `AUDITS/SOURCES_OFFICIELLES/20261031T134022160074Z/MANIFESTE.json`.
- Audit : **1 source configurée, 1 collectée, 0 bloquée, 0 note**, couverture 1/1361, 1360 sans document dans cette collecte.
- **Date de publication de la page inconnue** : usage rétrospectif interdit. Le suffixe de fournisseur `.F` n'est pas une mention explicite de la fiche ; `1F6.F` reste à vérifier séparément. Une fiche de marché n'est pas une certification SCE.

Preuve distincte préexistante, réutilisée et non recollectée : communiqué Fermentalg S1 2026 du 06/10/2026, source Webdisclosure, brut
`AUDITS/SOURCES_OFFICIELLES/20261031T120058499540Z/e6b16e996a4e2eac0bf88e94bdc7c56082798f35bb467707fc1abdd8f61b2f55.bin`,
SHA256 `e6b16e996a4e2eac0bf88e94bdc7c56082798f35bb467707fc1abdd8f61b2f55`, neuf faits financiers contrôlés séparément, **non certifiés SSI/MCPA**.

## Modifications, tests et sécurité

Commits de développement : `4791d9b6` (registre primaire), `7c7bcee7` (test), `927dbd27` (correction regex), `e9ae0b69` (workflow isolé), `08ac4e64` (test intégré CI).
Commit automatique de collecte `245a51f2` : uniquement quatre fichiers d'audit sous `AUDITS/SOURCES_OFFICIELLES/20261031T134022160074Z/`.

- Capture réelle : GitHub Actions [41206601621](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41206601621), **success** ; contrôle SHA256, identité documentaire et absence de mutation des historiques **success**.
- CI générale sur `08ac4e64` : [41206609651](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41206609651), **success**.
- Replay 05C PR sur `08ac4e64` : [41206613962](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41206613962), **success**.
- Replay automatique PR après commit du bot `245a51f2` : [41206633024](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41206633024), **action_required** ; ne pas le compter comme validation.
- Comparaison `798b3a30...245a51f2` : six commits, huit fichiers ; aucun fichier `DONNEES`, `HISTORIQUE`, `SAUVEGARDES`, `APPLICATION` ou `main` modifié par ce passage.

## Statut scientifique et prochain blocage

**EN_ATTENTE_DATA** : concordance documentaire ISIN/symbole officiel acquise, mais ni certification SCE à deux preuves indépendantes datées et vérifiées, ni validation des sept blocs SSI, ni score MCPA/IPS. Aucun challenger, duel 09B ou arbitrage n'est autorisé sur cette seule base.
Prochain travail : confirmer séparément le mapping exact `1F6.F` (suffixe fournisseur), dater ou documenter le caractère non daté de la fiche, faire valider les preuves SCE sans reprise par ticker, puis compléter les blocs financiers et exclusions. Continuer les autres candidats malgré cette attente.
Aucune transaction réelle. Aucun score ou performance inventé. Ne pas fusionner `main`, ne pas toucher au coffre `MICRO_CAPS_DOSSIER_TRANSMISSION_V3_MAITRE`, ne pas créer `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME`.

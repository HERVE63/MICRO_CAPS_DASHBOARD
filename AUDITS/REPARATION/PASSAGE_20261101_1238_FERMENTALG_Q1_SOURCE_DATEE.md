# MICRO CAPS — passage du 1er novembre 2026, 12:33–12:38 UTC

## Reprise, inventaire et protection

- PR brouillon #1, branche isolée `repair/microcaps-chain-20261030`, tête de départ `215d028ed91e7de87e97bd5f27687943caf7e618`. Aucun changement de branche depuis le passage précédent au moment de la reprise.
- Inventaire Google Drive **avant toute écriture** : `PRICE02A` (dossier) et `SEC_BRIDGE` (dossier) retrouvés ; `DATA04_EODHD_FUNDAMENTALS` présent, racine vide ; `FUND02E` et `FUND03A` non retrouvés par recherches ciblées (ne prouve pas leur inexistence dans d'autres archives). Les archives `AUDITS/SOURCES_OFFICIELLES` et le collecteur **07AA existant** ont été réutilisés.
- `main` observée à `ffd7a3b3c2889148fcea9d925ec59d1c089b12a2` ; aucune fusion ni écriture sur `main`. Coffre maître, historiques officiels, CPI, ETF Assurance-Vie et ordres réels non touchés.

## Blocage documentaire et action concrète

La paire de fiches officielles Deutsche Börse / Euronext du passage précédent reliait l'ISIN `FR0011271600` aux symboles `1F6` et `ALGAE`, mais **leurs dates de publication étaient inconnues**. Le communiqué Fermentalg S1 du 6 octobre 2026 était déjà archivé : **ne pas le recapturer**.

Une **autre publication primaire datée**, distincte de S1, a été retrouvée et contrôlée : communiqué Fermentalg du **5 mai 2026**, « Success of the sales diversification strategy in the first quarter of 2026 and commercial launches of the new BioSolutions », publié comme communiqué de l'émetteur par Webdisclosure, mentionnant explicitement `Fermentalg`, `FR0011271600`, `ALGAE` et `Euronext Growth Paris`.

Source : https://www.webdisclosure.fr/press-release/fermentalg-epa-falg-success-of-the-sales-diversification-strategy-in-the-first-quarter-of-2026-and-commercial-launches-of-the-new-biosolutions-QoLS0cVIeRx

- La date de publication est inscrite sous la **forme civile** `2026-05-05` : aucune heure UTC n'a été inférée de la mention 18:00.
- Nouveau registre isolé : `AUDITS/REPARATION/REGISTRE_COMPLEMENT_FERMENTALG_IDENTITE_20261101.csv`, une seule URL nouvelle. **Aucun collecteur supplémentaire créé.**
- Commit `918a32c0366a368e9b451980098cb2ab021204b5` : raccordement de ce registre au workflow 07AA historique, adaptation du test hors réseau de reprise, contrôle de l'absence de notes, vérification du contenu brut en cas de succès et statut `BLOQUE_SOURCE` conservé en cas d'indisponibilité.
- Collecte effective : workflow **41307191839**, **SUCCESS**. Commit automatique `fcd3d45d81dc894cfa43a3a95f62c63d0d0d8ef2` ; une source collectée, zéro source bloquée, zéro note.
- Archive publiée : `AUDITS/SOURCES_OFFICIELLES/20261101T123531273278Z/`. Date de capture `2026-11-01T12:35:31.273278+00:00`, document HTML primaire, SHA256 `b1f9b7ea7553e9a2c21d125f17da49d272f2d411316369920d25f2c2a420f649`. Le manifeste recense et vérifie les empreintes du document brut, du registre et de l'audit ; le test du workflow a vérifié les octets, l'ISIN et le nom de l'émetteur.
- CI complète **41307191845 SUCCESS**, replays isolés **41307191879 SUCCESS** et **41307196101 SUCCESS**.
- Préparation SSI automatique **41307230227 SUCCESS**, commit `88adc1e0f250c6c587baa4572f90724311966b56`. La nouvelle capture est reprise par 07Q2 : `ISIN_observe_dans_brut=OUI`, `Identite_SCE_certifiee=NON`, `Note_SSI=MANQUANTE`.

## Résultats mesurés après régénération

- `DONNEES/FILE_CERTIFICATION_IDENTITES_SSI.csv` : Fermentalg `1F6.F` = **9 captures**, **8 documents uniques URL–SHA256**, **4 URL**, **3 domaines**, **5 documents à publication inconnue**, **3 documents à publication déclarée connue et encore à vérifier**. Les répétitions ne valent pas des preuves indépendantes.
- `DONNEES/AUDIT_COLLECTE_PREUVES_SSI.csv` : **1 361 dossiers**, **12 249 lignes de plan**, **57 captures SHA256 intègres comptées comme pistes**, **6 captures invalides exclues**, **2 sources bloquées**.
- `DONNEES/AUDIT_SSI.csv` daté du `2026-11-01T12:37:22.473669+00:00` : **1 361 dossiers, zéro admis, 1 361 identités CIK en quarantaine**. Aucun SSI >=65, MCPA/IPS >=80, duel 09B ou arbitrage économique validé par cette opération.
- Les deux communiqués Fermentalg de mai et octobre sont **deux documents différents, mais hébergés par le même diffuseur** : ne pas les qualifier automatiquement d'éditeurs indépendants. La certification SCE exige une revue indépendante de l'identité et des dates, avec contrôle du rattachement du ticker fournisseur `1F6.F`.

## Suite prioritaire et règles de sécurité

1. Relecture documentaire indépendante du nouveau communiqué et rapprochement réglementaire ISIN ↔ émetteur ↔ cotation allemande, sans déduire le suffixe `.F` de la seule fiche Euronext.
2. Certification SCE uniquement si deux preuves primaires recevables et leur chronologie sont effectivement vérifiées ; ne jamais convertir la collecte en `VERIFIEE` par automatisme.
3. Vérification chiffre par chiffre des **18 transcriptions financières** d'ICAPE et Fermentalg ; compléter les blocs B4–B7 et poursuivre les autres dossiers en `EN_ATTENTE_DATA`.
4. Conserver la PR brouillon non fusionnée et **ne pas créer** `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant validation intégrale des moteurs, du replay, des benchmarks et de la reconstruction.

## Exécutions vérifiables

- Collecte : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41307191839
- CI : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41307191845
- Replays : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41307191879 et https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41307196101
- Préparation SSI : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41307230227
- PR : https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/pull/1

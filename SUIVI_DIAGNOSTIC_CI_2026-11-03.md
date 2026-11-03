# MICRO CAPS — diagnostic CI reproductible (2026-11-03)

## Périmètre et sécurité
Branche isolée `repair/microcaps-chain-20261030`; PR brouillon #1. Aucun changement sur main, les historiques, le coffre maître, CPI ou ETF AV. Aucune qualification ni opération financière réelle ou virtuelle.

## Constat vérifié via API GitHub
- SHA tête avant ce diagnostic : `0db69a8e22830062ce5afa025a54cd2d48e14de6`.
- Comparaison entre cette tête et la branche : identical, 0 commit nouveau.
- Workflow run `41559991708` (« Replay 05C isolated validation », workflow_id `402248970`) : status `completed`, conclusion `action_required`, **0 job** renvoyé par l'API.
- Conséquence : aucune étape de test exécutée ; ne pas qualifier ce résultat de succès ou d'échec Python.
- `DONNEES/AUDIT_SSI.csv` blob Git `8894b547f5e6306fa9916d58d72001287fac051b` : audit du `2026-11-03T01:28:36.743436+00:00`, 1361 dossiers, 0 admis, 1361 identités CIK en quarantaine.

## Reprise technique sans altération de données
1. Vérifier dans GitHub Actions la raison exacte de `action_required` (approbation, politiques Actions, permissions du contributeur ou règles d'organisation). Ne pas conclure à une cause avant preuve.
2. Après autorisation, lancer un **nouveau** workflow manuel sur cette branche et relever run ID, SHA testé, jobs, étapes et journaux. Une relance de run sans jobs n'est pas une preuve de validation.
3. Reprendre 07Q/07R seulement avec provenance, date de publication, empreinte SHA256 et identité émetteur vérifiées. Isoler les titres incomplets en `EN_ATTENTE_DATA`.
4. Ne jamais fusionner ou créer `SAUVEGARDE_MICROCAPS_TOTAL_SYSTEME` avant validation complète bout en bout.

## Limites
Le contrôle présent ne certifie ni source primaire, ni score SSI/MCPA, ni arbitrage mensuel. Les archives Drive FUND02E/FUND03A ne sont pas attestées dans ce passage.

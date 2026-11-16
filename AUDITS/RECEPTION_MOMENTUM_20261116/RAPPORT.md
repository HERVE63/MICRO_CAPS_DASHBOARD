# Micro Caps — reprise exécutée du 16 novembre 2026

**Résultat vérifié : 10/40 lignes admissibles au contrôle de 14 h 07, chaîne globale encore bloquée.**

21 sociétés ont fait l’objet d’une nouvelle lecture individuelle Premium dans cette reprise ; 20 dossiers contiennent les quatre pages demandées. Transense reste partielle. Avec la preuve Broadpeak partielle du passage précédent, 22 preuves du jour sont conservées dans GitHub. Les 15 preuves complètes du 15 novembre restent archivées à leur date et ne sont pas présentées comme actuelles.

## Réparations et résultats distants

- Growens est identifiée par MAIL et ISIN IT0005040354, contrôlé contre le dossier existant. L’alias est refusé si l’ISIN diffère. La cohorte T0 est inchangée.
- La relance du navigateur a effectivement rétabli la session Premium et permis 21 lectures supplémentaires. Chaque société et chaque historique ont été consultés dans le navigateur, sans requête cachée ni autre fournisseur.
- Tests d’intégration : **15 passed in 11.78s**, GitHub Actions [43872640958](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/43872640958).
- Intégrité T0 : réussite. Moteur 40M : exécuté, 40 lignes exportées, 10 admissibles. Archivage et sauvegarde des calculs : réussis.
- Gate ZONEBOURSE_MOMENTUM_40_GATE.py : **échec, code 2**, 10/40 admissibles, 30 non admissibles, journal_inchange=true, arbitrage_autorise=false.
- Journal SHA256 : 8662c18842e2f06d8fabe714e5032a375b306102aee2691309ef9220e6b72e78. Aucune transaction réelle ou virtuelle ajoutée.

Commit logiciel et données : 412be729c3f11e77c78ff2b6014702349cfbab48. Résultats calculés enregistrés par GitHub : 6789c9169400348c96723e4c5dbb7b4dc5e5a081. Première sauvegarde de dix relevés : 80b8ebe0f9540f5b5dfa2fd505301bf97f9695fa.

## Changements de direction admissibles au contrôle

- CTT Systems (CTT.ST) : DECELERATION_A_SURVEILLER → DIRECTION_HAUSSIERE.
- Light Science Technologies (LST.L) : REBOND_A_CONFIRMER → ALERTE_REPRISE_HAUSSIERE.
- Entech (ALESE.PA) : DIRECTION_BAISSIERE → ALERTE_REPRISE_HAUSSIERE.
- Sogeclair (ALSOG.PA) : ALERTE_REPRISE_HAUSSIERE → DIRECTION_HAUSSIERE.
- Mon Courtier Énergie Groupe (ALMCE.PA) : STABLE → REBOND_A_CONFIRMER.
- 2CRSi (AL2SI.PA) : DECELERATION_A_SURVEILLER → DIRECTION_BAISSIERE.
- WALLIX (ALLIX.PA) : STABLE → DECELERATION_A_SURVEILLER.

Ces signaux sont des diagnostics partiels au moment du contrôle, pas une confrontation complète des 40 ni une prévision de rendement. Tous les cours restent soumis à leur date et heure affichées ; un signal ne devient pas une autorisation de transaction.

## Blocages restants précis

18 sociétés sans nouvelle lecture du passage : IDN, INFU, OSS, CXDO, LWAY, AOM.L, ALSTI.PA, MEMS.PA, FTG.TO, ELVA.TO, COV.V, ROK.V, MTEC.L, ZOMD.V, CEMX.TO, PLEJD.ST, PULS.L, HSP.L.

Onze preuves supplémentaires ont été rejetées pour fraîcheur à l’instant du calcul : ALICA.PA, SFT.L, TSTL.L, GENI.ST, ALBFR.PA, TRT.L, ALBPK.PA, ALDMS.PA, ALSTW.PA, ALCUR.PA, ALIEV.PA. À ces onze rejets s’ajoute Kenorland pour preuve inexploitable. Kenorland : le tableau « latest » récupéré ne certifie pas la clôture d’en-tête ; aucune substitution depuis les archives. Transense : dates septembre/août non confirmées par le tableau resté en octobre ; Broadpeak : trois mois absent. Ces deux derniers cas figurent déjà dans les onze rejets de fraîcheur.

Dernier blocage du navigateur, observé directement : « Browser Use rejected this action due to browser security policy … URL policy gate did not grant access … requested URL protocol is not allowed ». L’outil interdit explicitement un contournement par une autre surface ou une exécution indirecte. L’action concernée a été arrêtée ; aucun contournement essayé. Il ne s’agit pas d’un quota Zonebourse annoncé par le site. L’onglet est conservé pour reprise.

## Revue hebdomadaire

Préparation et tableau 40 lignes produits automatiquement par GitHub. Classement et alertes limités aux dix lignes admissibles ; confrontation complète impossible avec 30 lignes non admissibles. Arbitrage global désactivé. T0 01/10/2026, 4 000 EUR virtuels géré et 4 000 EUR témoin statique, frais 2,5 % par côté. Témoin inchangé. Aucune note MCPA, SSI ou WWWS ne conditionne le moteur momentum.

[Tableau des 40](TABLEAU_40.md) · [Preuves Zonebourse](../../DONNEES/ZONEBOURSE_NAVIGATEUR/2026-11-16/). Travail exclusivement sur repair/microcaps-chain-20261030 ; main et maîtres figés inchangés.

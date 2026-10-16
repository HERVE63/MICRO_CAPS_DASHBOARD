# Raccordement du protocole SCE retrouvé — 16 octobre 2026

Sources intégralement relues : `Fiche_maitre_SCE20260812_v1.1_CONSOLIDEE_2026-08-12.docx` (4 pages) et `Fiche_Architecture_Globale_Veille_Chasse_Selection_MCPA_IPS_SCE_Discovery_v1.0_2026-08-12.docx` (5 pages). Il s'agit d'un relevé pour le code opérationnel, pas d'une modification des documents maîtres.

Le document consolidé définit la sélection mécanique et l'analyse MCPA comme deux opérations séparées. Il impose les actions ordinaires, les exclusions de types d'instruments, le dédoublonnage par ISIN, le contrôle du domicile et la complétude du parsing. L'ordre des contrôles est déterministe : `SHA-256("SCE20260812 | ticker | ISIN")`. Il ne définit pas un score financier SCE supplémentaire.

La branche Discovery de l'architecture permet de nouveaux lots adaptés au mandat. Pour MICRO CAPS, le mandat verrouillé de 50–300 M€ remplace donc la tranche expérimentale de 100 M$–3 Md$. Les quotas du panel expérimental de 25 sociétés ne sont pas appliqués à l'étude de l'ensemble du marché US. Le panel et ses notes T0 ne sont ni lus comme recommandations actuelles ni modifiés.

`07AL_RACCORDER_SCE_DISCOVERY_SSI_US.py` applique l'ordre maître aux ISIN présents et valides selon leur checksum. Le ticker d'entrée est explicitement le code de cotation complet du recensement, suffixe conservé. Les doublons d'ISIN restent en attente de preuve de la cotation principale : aucun choix arbitraire n'ajoute une chance à un émetteur. Un checksum valide ne prouve pas l'identité de l'émetteur ; le programme conserve cette distinction.

L'ordre de contrôle ne classe pas les meilleures valeurs. Tous les candidats restent dans l'audit, y compris les absences de données, les identités ambiguës et les instruments non admissibles. Les éléments manquants sont exposés. Le programme n'ajoute ni seuil financier nouveau ni note SSI/MCPA fictive.

Les dossiers sont raccordés au validateur SSI 07R existant dans un répertoire d'audit isolé. Les notes et références vérifiées à l'avenir sont conservées dans `CONFIG/QUALIFICATIONS_SSI_US_HUMAINES.csv`, lu uniquement par ce raccordement. Les anciennes valeurs de ce registre ne sont jamais réinitialisées par une collecte. Les preuves doivent toujours satisfaire le registre SSI et les contrôles d'identité avant toute admission et avant le passage MCPA/IPS.

L'absence de preuve bloque le passage ; elle ne constitue pas un rejet pour mauvaise qualité financière. Aucun Top20, Top5 ou arbitrage n'est validé à partir du seul ordre SCE. Les décisions restent soumises aux règles prospectives MICRO CAPS, dont les frais de 2,5 % et le rythme mensuel des arbitrages.

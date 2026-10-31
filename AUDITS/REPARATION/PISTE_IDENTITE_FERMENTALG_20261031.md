# MICRO CAPS — piste indépendante Fermentalg, 31/10/2026

**Statut : PISTES PRIMAIRES À CAPTURER / EN_ATTENTE_DATA, non certifiées.**
Aucune note SSI/MCPA, aucune admission, aucun arbitrage. Ne pas attribuer de
SHA256 à une page simplement consultée : seule la capture brute 07AA et
sa revue indépendante pourront produire une empreinte et une preuve vérifiables.

## Réutilisation avant collecte

- `AUDITS/SOURCES_OFFICIELLES/20261010T132940591629Z/AUDIT_DOCUMENTS.csv` :
  `FERMENTALG_CP_S1_2026` bloqué HTTP 403 sur PDF Actusnews ; zéro document
  acquis, zéro note. `HOFSETH_BIOCARE_Q2_2026` acquis dans cette même
  archive, SHA256 `46b6b8b1fd0e73a6a18f1320c5dd457bd8f35499a1eacae3a06ff471c41801c6`.
  L'archive Hofseth ne doit **pas** être téléchargée une nouvelle fois.
- `CONFIG/DOCUMENTS_OFFICIELS_A_COLLECTER.csv` : URL Fermentalg remplacée
  par le communiqué HTML de l'émetteur, distribué sur Actusnews ; registre
  isolé `AUDITS/REPARATION/REGISTRE_REPRISE_FERMENTALG_20261031.csv`.
  Le collecteur historique `07AA` est réutilisé sans modification.

## Trois références primaires consultées le 31/10/2026

1. **Diffusion de l'émetteur / Actusnews**, communiqué résultats semestriels,
   publié le **06/10/2026 à 18 h 00 (Europe/Paris)**, soit 16 h UTC :
   https://www.actusnews.com/fr/fermentalg/cp/2026/10/06/resultats-semestriels-2026-discipline-financiere-stricte-et-renforcement-de-la-tresorerie-pour-aborder-dans-les-meilleures .
   Le document déclare `FR0011271600`, `9695007VNRQR6V5TMN85` et le
   mnémonique principal `ALGAE`. La date de publication reste à confronter
   au contenu brut capturé ; aucune empreinte SHA256 revendiquée ici.
2. **Börse Stuttgart, opérateur de marché**, fiche instrument :
   https://www.boerse-stuttgart.de/de-de/produkte/aktien/stuttgart/a1103m-fermentalg-eo---04 .
   La fiche associe explicitement `FERMENTALG`, `ISIN FR0011271600`,
   `WKN A1103M`, `symbol 1F6` et une cotation en EUR. Elle concerne
   Stuttgart, **pas une certification du suffixe Yahoo `.F`**.
3. **Deutsche Börse, opérateur de marché**, fiche :
   https://live.deutsche-boerse.com/aktie/fermentalg-eo-04 .
   La fiche associe `FR0011271600`, `A1103M`, `1F6` et présente
   des paramètres Frankfurt. L'égalité exacte entre la ligne `1F6.F`
   du fournisseur et l'instrument de la place doit être revue sur preuves
   brutes, notamment la devise, la place et la période.

## Points à réconcilier avant SSI

- La ligne `1F6.F` du dossier SSI vient de Yahoo, sans CIK, avec
  capitalisation `50 012 872 EUR` au scan du 08/10/2026. La fiche Stuttgart
  consultée le 31/10/2026 affiche `32,58 M EUR` : dates, places et
  dénominateurs ne sont pas homogènes. **Ne pas corriger une valeur par
  substitution silencieuse** ; recalculer avec nombre de titres, cours et
  date identiques, puis archiver les preuves.
- Le fournisseur affiche `Volume_monetaire_median_63s_local=0.0` :
  liquidité B7 **non documentée**, pas une note zéro inventée.
- Le communiqué de l'émetteur indique un CA S1 2026 d'environ 7,4 M EUR,
  une marge brute de 23 %, un résultat opérationnel négatif et une
  augmentation de capital. Les valeurs détaillées nécessitent extraction
  sur octets archivés, période et unité ; **aucune notation automatique**.
- Les deux sources d'identité ne sont pas encore enregistrées dans
  `REGISTRE_PREUVES_SSI.csv` avec provenance/date/SHA256/revue indépendante.
  Le statut reste `EN_ATTENTE_DATA_IDENTITE_CIK` (ou `EN_ATTENTE_DATA`
  selon le module), sans admission 07R.

## Séquence de contrôle

Vérifier résultat CI et collecte 07AA sur la branche isolée ; si HTTP 403
persiste, conserver `BLOQUE_SOURCE` et chercher une autre URL officielle.
Capturer ensuite les fiches opérateurs dans un registre 07AA dédié
(`DONNEE_MARCHE_IDENTITE`, jamais `PUBLICATION_EMETTEUR`), vérifier SHA256
et dates, puis revue SCE indépendante. Continuer les autres dossiers
sans attendre la résolution de ce titre.

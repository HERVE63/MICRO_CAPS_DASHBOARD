# Growens — diagnostic réel de la piste EODHD, sans substitution

Date de contrôle : **2026-11-02 UTC**. Source : capture **réelle**, et non fixture de test.
Statut : **EN_ATTENTE_DATA**. Aucun score, cours de Milan, arbitrage ou performance validé.

## Réutilisation et intégrité

- Cohorte T0 figée : **ligne 23, Growens, GROW.MI, EUR**.
- Exécution existante : [collecte 09D n° 41390569283](https://github.com/HERVE63/MICRO_CAPS_DASHBOARD/actions/runs/41390569283), artefact **13117561204**.
- Lot : `COLLECTE_40_20261102T045034810555Z`.
- Archive EODHD : `REPONSES_FOURNISSEUR/23_SEARCH.json`.
- SHA256 recalculé sur les **octets JSON canoniques effectivement archivés** :
  `8234be8653783f38cbd66dde2a8a36119d99b7d415cbfe1d3cfdbcea9338fe71`.
- SHA256 du ZIP d'artefact téléchargé et contrôlé :
  `df6fe02a59f34d55e50459d0ee8cae986bcb0c10240268b61f29769ad52fb523`.
- La requête EODHD `/api/eod/GROW.MI` répond **HTTP 404** ; `/api/search/Growens` répond **HTTP 200** avec une seule piste.

## Résultat exact de la recherche fournisseur (non primaire)

```json
[{"Code":"0MU","Country":"Germany","Currency":"EUR","Exchange":"F","ISIN":"IT0005040354","Name":"Growens S.p.A.","Type":"Common Stock","isPrimary":false,"previousClose":1.68,"previousCloseDate":"2026-10-30"}]
```

**Interprétation :** l'ISIN est concordant, mais le fournisseur indique **0MU.F, Francfort, isPrimary=false**, et non **GROW.MI, Euronext Growth Milan**. Le `previousClose=1.68 EUR` du 30 octobre 2026 est une **observation secondaire de la cotation allemande** : il est interdit de l'utiliser comme clôture de Milan, comme valorisation de la ligne 23 ou comme preuve SSI/MCPA. La source fournisseur peut comporter des retards ou erreurs.

## Sources primaires d'identité (liens ; octets bruts non archivés dans ce lot)

- Émetteur, document daté du 19/10/2026 : https://www.growens.io/en/documents/growens-october-2026/ — GROW.MI, ISIN IT0005040354, Euronext Growth Milan.
- Place italienne : https://www.borsaitaliana.it/borsa/azioni/scheda/IT0005040354-EXGM.html — code GROW, ISIN IT0005040354, marché EGM.
- Place allemande : https://live.deutsche-boerse.com/equity/growens-s-p-a — symbole 0MU, ISIN IT0005040354 (corroboration de la **cotation distincte**).
- Documentation officielle du fournisseur : https://eodhd.com/financial-apis/search-api-for-stocks-etfs-mutual-funds — `previousClose`, `previousCloseDate`, `isPrimary` et `Exchange` appartiennent à **l'instrument retourné**.

Ces références d'identité ne certifient **aucun cours de clôture italien** et ne constituent pas un dossier primaire brut admis par 07R.

## Décision technique

- Maintenir le ticker officiel T0 **GROW.MI** inchangé.
- Conserver la piste **0MU.F** comme donnée secondaire distincte et documentée, **sans substitution**.
- Conserver **EN_ATTENTE_DATA_COURS** pour Growens, sans bloquer les 39 autres titres.
- Prochaine collecte : obtenir une clôture historique **EGM/GROW** datée et archivée, avec devise, ISIN et place explicitement concordants ; sinon laisser la ligne en attente.
- Aucun ordre réel ni virtuel, aucune note, aucune mutation de `main`, des historiques officiels ou du coffre maître.

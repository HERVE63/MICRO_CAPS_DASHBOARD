# Piste primaire Growens — identité instrument, sans admission SSI

**Contrôle documentaire :** 2026-11-02 UTC. **État :** `IDENTITE_CORROBOREE_A_VERIFIER_PAR_CAPTURE`. Cette fiche n'est **pas** une preuve primaire brute archivée et ne doit pas alimenter 07R, une note ou une valorisation automatique.

## Source primaire émetteur
- Page : https://www.growens.io/en/documents/growens-october-2026/
- Document daté du **19 octobre 2026**.
- Transcription factuelle minimale de la page officielle, encodage UTF-8, lignes LF, saut de ligne final :

```text
Source: https://www.growens.io/en/documents/growens-october-2026/
Date_publication: 2026-10-19
Emetteur: GROWENS SPA
Ticker_editeur: GROW.MI
Marche: Euronext Growth Milan (EGM)
ISIN: IT0005040354
```

**SHA256 de la transcription ci-dessus, et non des octets HTML de la page** : `dc6eaaa7b81dbdef30c756deceacd2da6d622e7c58a8b5d9bb541464eb6bbc8d`. L'empreinte est reproductible en UTF-8 et ne doit pas être présentée comme une empreinte du document d'origine.

## Corroboration primaire de marché
- Fiche de la place : https://www.borsaitaliana.it/borsa/azioni/scheda/IT0005040354-EXGM.html?lang=it
- La fiche affiche **Growens**, **ISIN IT0005040354**, **code GROW**, **Euronext Growth Milan**. La cotation affichée est dynamique ; **aucun cours ni horodatage de séance n'est certifié par cette fiche**.

## Écart de fournisseur à traiter
- Cohorte T0 immuable : ligne 23, `Growens`, `GROW.MI`, EUR.
- La collecte EODHD précédente a reçu HTTP 404 sur `/api/eod/GROW.MI` ; cela **ne démontre ni un changement de ticker ni une radiation**.
- Le module 09D recherche désormais des **pistes fournisseur** en cas de HTTP 404, archive le JSON canonique et son SHA256, mais ne remplace jamais `GROW.MI` automatiquement.
- Pour exploiter un cours : capturer les octets de la source primaire ou la réponse de fournisseur datée, certifier instrument/ISIN/place, contrôler les unités et actions sur titres, puis seulement effectuer la conversion EUR et la valorisation. En attendant : `EN_ATTENTE_DATA`.

**Aucun score SSI/MCPA, aucune performance et aucun arbitrage générés par cette piste.**

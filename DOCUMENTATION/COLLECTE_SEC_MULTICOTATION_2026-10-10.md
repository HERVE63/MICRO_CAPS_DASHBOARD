# Collecte SEC et cotations multiples — 10 octobre 2026

Le run 38052884336 a confirmé le secret, les six modules et la sauvegarde. Il n'a collecté aucun fait financier : les 1 361 codes de cotation allemands étaient comparés uniquement aux codes américains SEC.

Sur le registre officiel brut SHA256 a9595d33a34615553ee706c95458fff0bb9fec9642a9d61710f3e5dbd45ca23e, 245 dossiers présentent une égalité de nom normalisé. Ce nombre décrit des pistes et ne constitue aucune validation d'identité, d'ISIN, de classe d'action ou d'admission SSI.

07T conserve les codes de cotation d'origine, recherche les noms exacts sans rapprochement flou, conserve les ambiguïtés entre CIK et distingue les alias d'un même CIK. Le nettoyage des lettres finales après plusieurs espaces sert uniquement à la découverte. Toutes les pistes restent CIK_verifie=NON. Les données collectées restent hors du registre de preuves validées.

Le lot technique est déterminé par ordre alphabétique du ticker parmi les pistes uniques, indépendamment du pays de cotation. Taille initiale 10, offset 0 ; les autres pistes restent explicitement PISTE_SEC_HORS_LOT. Cette limite est technique, sans présélection financière. 07Z ne déduit plus le domicile de l'émetteur du champ Pays.

Les 12 fichiers de tests hors réseau ont été exécutés localement avec succès avant publication. La collecte en ligne après cette correction doit être contrôlée sur les audits du nouveau run. Aucun score, classement ou arbitrage n'est déclaré validé.

# Consolidation additive des preuves SEC

07AD vérifie les SHA256 des faits et des index consignés dans chaque manifeste avant de les lire. Il conserve les références de toutes les archives pour chaque observation. Les doublons identiques sont réunis ; les valeurs différentes pour le même identifiant d'observation sont toutes conservées et marquées VALEURS_DIVERGENTES_A_RELIRE. Les normes et devises restent distinctes.

La couverture porte exclusivement sur les 1 361 dossiers de qualification. Les CIK découverts restent des pistes ; plusieurs CIK pour un même dossier produisent IDENTITE_DIVERGENTE_A_RELIRE. Les fichiers de qualification, preuves humaines et portefeuilles ne sont pas modifiés. Aucun score ni identité n'est validé par cette consolidation.

Les audits consolidés sont archivés dans AUDITS/SEC_CONSOLIDE avec les audits originaux. Le module est raccordé au workflow avant le bilan SSI. Quatorze fichiers de tests ont réussi localement avant publication, dont le test de consolidation, contradictions et corruption.

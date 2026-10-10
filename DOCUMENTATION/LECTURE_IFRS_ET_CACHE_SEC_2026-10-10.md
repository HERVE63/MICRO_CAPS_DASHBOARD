# Comptes IFRS et relecture des archives SEC

L'archive réelle companyfacts d'Anfield Energy (CIK 1519469), SHA256 13619406cac83aba15445064ba5da41db55cf150078d07acca7f51761e48df59, contient uniquement ifrs-full. Le lecteur initial limité à us-gaap écartait ces faits. La documentation primaire SEC confirme les taxonomies standard et les différentes unités : https://www.sec.gov/search-filings/edgar-application-programming-interfaces .

07U lit désormais les concepts explicites us-gaap et ifrs-full. La norme est conservée jusqu'au rapprochement SSI. 07V conserve les unités monétaires séparément et ne fait aucune conversion. Les actions émises IFRS ne sont pas assimilées aux actions en circulation. Les périodes cumulées ne sont pas transformées en trimestres et les dates futures restent exclues.

07Z peut relire les réponses brutes archivées le même jour UTC. Le SHA256 est recontrôlé à chaque lecture ; une altération bloque la collecte et produit un manifeste. Les dates de collecte originales sont conservées, la relecture est datée séparément. Les archives restent intactes. Un jour suivant provoque de nouvelles requêtes. La provenance distingue commit exécuté et commit déclencheur.

Treize fichiers de tests hors réseau ont réussi localement, dont IFRS/CAD et relecture du cache sans réseau, avec blocage sur corruption.

Une exécution après la collecte élargie doit retraiter l'ensemble des pistes depuis les bruts archivés, sans attribuer de scores. Les trois concordances d'identifiants consultées sur les sites officiels sont consignées dans CONFIG/PISTES_IDENTITE_SOURCES_OFFICIELLES.csv ; leurs réponses HTTP restent à archiver avant validation dans le registre SSI.

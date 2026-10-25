# Halden v5 : ce qui a changé après la revue de Jennifer (24 octobre 2026)

Ce dossier contient la version v5 de tous les livrables. Les anciennes versions (v2 à v4) sont gardées dans le dossier Halden et ne seront supprimées qu'avec ton accord.

## Les règles appliquées partout

- **Pilote = un seul agent, un seul pays** : encaissements (appels de fonds par jalon) à Dubaï. Les cinq autres agents passent en « vision ».
- **Chaque message vers un acheteur est validé par une personne** pendant le pilote, relances comprises. La question « qui appuie sur envoyer ? » est donc tranchée.
- **Un seul jeu de chiffres de démo**, toujours signalé comme fictif : 14 virements sur 19 rapprochés sans humain, 4 validés par la finance, 1 refusé à raison (référence d'un autre acheteur). Tour fictive de 32 acheteurs ; 35 brouillons préparés, 0 envoyé. Les anciens « 85 % », « 238/34/8 », « moins d'un jour » et « encaissé sous 15 jours » ont disparu.
- **Un chiffre inventé n'apparaît jamais dans un titre** sans « dans notre démo ».
- **Vocabulaire de Dubaï** : enregistrement Oqood auprès du DLD, plus de « notaire ». Procédure de défaut DLD (loi 13/2008 art. 11, modifiée par la loi 19/2017) ; escrow (loi n° 8 de 2007) ; données personnelles (décret-loi 45/2021).
- **Plus de Slack** pour les données clients ; le Maroc est retiré des marchés.
- **Lisibilité** : rien sous 9 points, sources comprises.

## 1. POC (dossier POC_Halden, et la PR GitHub n° 1, version 0.2.0)

- **Validation** : la règle « chaque message acheteur est validé » est écrite dans le code (guardrails.py). La grille Excel peut durcir une tâche, jamais l'assouplir.
- **Rapprochement** : n'est automatique que si référence, payeur ET montant correspondent. Sinon, la ligne part en file (ex. « la référence appartient à un autre acheteur »).
- **Relances** : aucune relance tant qu'un paiement est en attente ou qu'un dossier est escaladé ; une seule conversation par acheteur et par cycle.
- **Signaux acheteur** (nouveau, signaux.py) : « j'ai payé », avocat, réclamation, difficulté (anglais, français, arabe). Tout contact automatique est suspendu et une personne reprend la main.
- **Contrôles** : chaque montant, pourcentage et date est vérifié ; approbateurs autorisés ; journal d'audit signé.
- **Relevés** : formats CSV de plusieurs banques et MT940 ; virements rejetés et doublons détectés.
- **IA** : données masquées avant l'appel au modèle ; coût journalisé.
- **J+30** : la procédure de défaut DLD est jointe à l'escalade.
- **Vérification** : 25 tests OK ; banc d'essai de 200 lignes piégées, 0 faux rapprochement automatique.

## 2. Dossier startup (Halden_Dossier_Startup_v5.pptx, 12 slides)

- **Synthèse** au format situation, complication, résolution. Ce qu'on demande : un seul shadow run.
- **Problème** marqué HYPOTHÈSE, avec ce que gagne le directeur financier sous escrow.
- **Marché** : une seule lecture du −38 %.
- **Concurrence** : Akarati, RealSoft (Coral), In4Suite, RealCube, plus trois réponses à « pourquoi ajouter Halden ».
- **Règle d'approbation** et signaux d'arrêt.
- **Cascade de la démo** : « Dans notre démo, 14 virements sur 19… ».
- **Pack Dubaï** marqué « en préparation », avec la procédure de défaut DLD.
- **Prix indicatifs** : AED 6 à 12 par lot et par mois, AED 15 000 de mise en place par projet, pilote gratuit.
- **Marché adressable** marqué hypothèse : environ AED 28 M par an à Dubaï, environ AED 11 M en Arabie saoudite. Questions juridiques ouvertes.
- **Entonnoir** 30 → 10 → 5 → 1 shadow run, avec 4 indicateurs.
- **Tableau des risques** : 7 risques.
- **Équipe** : Jennifer (stratégie et processus), Karam (produit et prototype), Dhruv et Thomas (« membre fondateur » : rôles à me donner). Contact : haldennn.netlify.app.

## 3. Présentation client EN (Halden_Presentation_Client_EN_v5.pptx, 18 slides)

- **Couverture** bilingue anglais et arabe. L'arabe est à faire relire par un natif.
- **Quatre tâches** marquées « OUR HYPOTHESIS ». Le pilote ne porte que sur les appels de fonds.
- **Comment ça marche** : chaque message acheteur est approuvé ; Oqood, pas de notaire.
- **Cascade de démo**, gains du directeur financier, tableau « Why not my ERP? », pack Dubaï « IN PREPARATION ».
- **Données et sécurité** : AWS aux Émirats, masquage, PDPL, journal signé.
- **Prix, shadow pilot** et indicateurs : temps comparé à la situation actuelle, rapprochement, 0 erreur, 100 % des signaux escaladés.

## 4. Charte graphique et template (Halden_Charte_Graphique_v5.pptx, Halden_Template_v5.pptx)

- **Typographie** : Montserrat reste la police. Pour l'arabe, IBM Plex Sans Arabic (ma recommandation ; tu ne m'as pas encore répondu sur ce choix).
- **Taille minimale** de 9 points, en-têtes et sources compris.
- **Nouvelles règles** : un chiffre inventé jamais dans un titre sans « dans notre démo » ; stickers HYPOTHÈSE, DÉMO · FICTIF, À TESTER.
- **Checklist mise à jour** : sources externes seulement, vocabulaire de Dubaï, pas de notaire.

## 5. Architecture agentique (Halden_Architecture_Agentique_v5.pptx, 16 slides, et la page web de la note)

- **Principes** : une instance par pays, en commençant par une seule ; relevés CSV et MT940, un PDF étant d'abord exporté en CSV.
- **Frontière IA** : les données sont masquées avant Bedrock ; pas de Slack.
- **Trajet d'un jalon en 8 étapes** : un suivi par acheteur, relances validées, défaut DLD à J+30, déblocage escrow.
- **Fiches agents** : pilote = encaissements seulement, les autres en vision.
- **Grille de décision notée** sur 18 tâches, avec plancher, décision, sensibilité à ±1 point et phase. Résultat : 3 tâches humaines, 3 règles, 10 validées, 2 autonomes internes.
- **Décisions** : « qui appuie sur envoyer » est tranché ; il en reste 3 à trancher avant le live.
- **La page web de la note** a reçu les mêmes corrections : https://claude.ai/artifact/VcU72f2YJ8ukiosekU3V5C

## 6. Atlas BPMN (dossier BPMN, en anglais : c'est la version de référence)

- **Zoom encaissements reconstruit**, dans le processus cible comme dans la solution Halden :
  - un suivi par acheteur, en parallèle, au lieu d'une seule boucle pour 300 acheteurs ;
  - relances rédigées par l'agent puis validées par la finance (à refaire ou abandonnées sinon), jamais si un paiement est en attente ;
  - toutes les issues du rapprochement : exact (automatique) ; partiel, trop-perçu, référence d'un autre acheteur ou inconnu (vérifié par la finance) ; « ce n'est pas lui » (l'acheteur attend à nouveau) ;
  - un signal de l'acheteur (payé, avocat, réclamation, difficulté) coupe tout contact ;
  - à J+30, escalade : la finance choisit entre un nouveau plan et la procédure de défaut DLD (notification, 30 jours, décision selon l'avancement du chantier) ;
  - en fin de jalon, le dossier de déblocage escrow est soumis à la banque par la finance.
- **As-Is** : marqué « notre hypothèse, à vérifier en entretiens ». La fin du processus, qui n'était reliée à rien, est corrigée.
- **Cycle complet cible** : les réclamations de garantie deviennent un sous-processus qui peut se déclencher à tout moment pendant 10 ans ; « notaire » est remplacé par « DLD (Oqood) ».
- **Libellés** : « To-Be · the market » devient « Target process ».
- **Indicateurs** : « 14 / 19 dans notre démo » et « 0 message envoyé sans validation » remplacent 85 % et « moins d'un jour ».
- **Page web mise à jour** : https://claude.ai/artifact/55FTAL6PdiuzmeVDTwN7Wv

## Ce qu'il reste à faire de ton côté

1. Me donner les rôles de Dhruv et de Thomas.
2. Faire relire l'arabe par un natif.
3. Me dire si je peux supprimer les anciennes versions v2 à v4.
4. Passer le dépôt GitHub en privé.
5. Relire et fusionner la PR du POC : https://github.com/karamel75/Halden/pull/1

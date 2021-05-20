# Archimail

Ce projet a été réalisé lors d'un stage de fin d'études au Conseil d'Etat dans le cadre du Master 2 de l'Ecole nationale des chartes (année universitaire 2020-2021).

## Objectif

L'objectif est de fournir un script complémentaire aux outils développés dans le cadre du [programme VITAM](https://www.programmevitam.fr/), par exemple les [SEDA Tools](https://github.com/ProgrammeVitam/sedatools), à utiliser dans le cadre d'un projet de pérennisation numérique des données de courriers électroniques. 

## Grands principes

Le script prend en entrée un SIP conforme au SEDA décompressé. Il retourne ce même SIP enrichi de nouvelles métadonnées, toujours conforme au SEDA, qu'il conviendra de zipper à nouveau. 

Il repose sur 3 grands principes:

- Enrichir le manifeste [SEDA](https://www.francearchives.fr/seda/index.html) avec des métadonnées type "mots-clefs" au niveau de chaque mail. Ces métadonnées complètent les métadonnées ajoutées habituellement par la pratique et qui se limitent aux plus hauts niveaux de description. 
- Tester la validité des éventuelles URL trouvées dans les mails au moment du traitement et insérer la documentation de ces tests au format CSV dans le SIP.
- Décompresser les éventuelles pièces jointes ZIP. 

## Fonctionnalités

Le script propose les fonctionnalités suivantes :

- Détermination de 3 mots-clefs par mail (tokenisation, lemmatisation, évitement des noms propres) qui serviront de métadonnées de recherche basiques.
- Enrichissement du manifeste SEDA avec ces métadonnées.
- Décompression des éventuelles pièces jointes ZIP et suppression de fichiers ZIP originaux. 
- Test des URLs ainsi que leur éventuel enregistrement par [Internet Archive](https://archive.org/web/).
- Génération d'un fichier CSV rassemblant pour chaque mail les mots-clefs et les URLs testées. Ce fichier pourra être joint à un SIP. 
- Génération d'un fichier CSV contenant la liste des mails qui auront été estimés comme contenant des données personnelles. Un révision humaine sera alors nécessaire pour en juger définitivement. 

Plus de détail sur les fonctionnalités:

### Enrichissement des métadonnées

Le corps de chaque mail est parsé. En utilisant deux librairies de traitement automatique du langage naturel ([NLTK](https://www.nltk.org/) et [Spacy](https://spacy.io/)), les mots sont tokenisés (suppression des mots outils etc...), lemmatisés (chaque mot est ramené à sa forme du dictionnaire) et classés par nombre d'occurences. Les trois mots qui ont le plus d'occurences sont retenus pour servir de mots-clefs et enrichir les métadonnées de description SEDA du mail. 

Le script utilise également les fonctions de classification des librairies citées afin d'éviter d'insérer dans les métadonnées des noms propres (*Named Entity Recognition*).

Ces nouvelles métadonnées sont automatiquement insérées dans le manifeste SEDA selon l'exemple suivant :

```xml
<ArchiveUnit id="ID25">
<Content>
<Tag>élément</Tag>
<Tag>étranger</Tag>
<Tag>événement</Tag>
<DescriptionLevel>Item</DescriptionLevel>
<Title>Création du compte Instagram</Title>
<OriginatingSystemId>&lt;7b88c65f-2573-ce0f-cef5-0c79b1f5d600@chartes.psl.eu&gt;</OriginatingSystemId>
<Writer>
<FullName>john doe</FullName>
<Identifier>john.doe@example.com</Identifier>
</Writer>
<Addressee>
<FullName>jane doe</FullName>
<Identifier>jane.doe@site.fr</Identifier>
</Addressee>
<SentDate>2019-09-26T12:51:02Z</SentDate>
<ReceivedDate>2019-09-26T12:51:02Z</ReceivedDate>
</Content>
<DataObjectReference>
<DataObjectGroupReferenceId>ID26</DataObjectGroupReferenceId>
</DataObjectReference>
</ArchiveUnit>

```
NB : Ces fonctionnalités ne peuvent être utilisées à leur potentiel maximum qu'avec des données rédigées en langue française. 

A l'échelle de l'ensemble du SIP, ces enrichissements sont documentés de la façon suivante:

```xml
<DescriptiveMetadata>
      <ArchiveUnit id="ID10">
        <Management>
         [...]
        </Management>
        <Content>
          <DescriptionLevel>[...]</DescriptionLevel>
          <Title>[...]</Title>
          <Description>[...]</Description>
          <CustodialHistory>
            <CustodialHistoryItem>[...]</CustodialHistoryItem>
          </CustodialHistory>
          <Tag>[...]</Tag>
          <Tag>[...]</Tag>
          <StartDate>[...]</StartDate>
          <EndDate>[...]</EndDate>
          <Event>
            <EventType>Enrichissement des métadonnées au niveau de chaque message via un script Python</EventType>
            <EventDateTime>2021-05-14T14:00:00</EventDateTime>
            <EventDetail>Réalisation par le Bureau des Archives du Conseil d'Etat</EventDetail>
          </Event>
    [...]
</DescriptiveMetadata>

```

### Le CSV de pérennisation des URLs

Le script génère un fichier CSV (séparateur point-virgule) qui, pour chaque mail, comporte les colonnes suivantes:
- Le nom du mail (chemin)
- Les 3 mots-clefs
- Les URLs trouvées
- Le statut du test (code HTTP)
- Le timestamp du test
- Le nom du responsable de l'URL (recommandation [INTERPARES](http://interpares.org/))
- La disponibilité de l'enregistrement le plus récent dans la Wayback Machine (s'il existe)
- Le lien vers cet enregistrement
- Le timestamp de l'enregistrement

Ce fichier est inséré dans le SIP comme document de description complémentaire généré par les Archives. Il est automatiquement documenté dans le manifeste de la manière suivante:

```xml
<Content>
    <DescriptionLevel>Item</DescriptionLevel>
    <Title>urls.csv</Title>
    <Event>
        <EventType>Création</EventType>
        <EventDateTime>2021-05-14T14:00:00</EventDateTime>
        <EventDetail>Fichier généré pour documentation par les Archives</EventDetail>
    </Event>
</Content>
````

Exemple d'organisation des données dans le CSV:

| nom_fichier        | top_trois_mots      | url(s)                    | resultat_test_url | date_test_url              | responsable_url    | internet_archive_dispo | internet_archive_url                                                | internet_archive_timestamp |
|--------------------|---------------------|---------------------------|-------------------|----------------------------|--------------------|------------------------|---------------------------------------------------------------------|----------------------------|
| content/ID1197.eml | foo, bar, test | https://www.conseil-etat.fr/ | 200               | 2021-05-07 13:33:04.710089 | www.conseil-etat.fr | True                   | http://web.archive.org/web/20210418112501/http://www.conseil-etat.fr | 20210418112501             |

S'il y a plusieurs éléments à afficher dans une cellule, ils sont séparés par une virgule.

### Décompression des pièces jointes compressées

Les formats compressés (.zip, .7z...) ne sont pas recommandés pour la pérennisation numérique. A l'heure de la réalisation de ce projet l'outil RESIP (v.2.3.0) ne permet pas de décompresser automatiquement les pièces jointes des mails. Le script réalise cette décompression automatiquement et, une fois celle-ci effectuée, supprime les fichiers compressés. Cette action est automatiquement documentée dans le manifeste SEDA selon l'exemple suivant:

```xml
<Content>
    <DescriptionLevel>Item</DescriptionLevel>
    <Title>foo_bar.7z</Title>
    <Description>Veuillez trouver le document "foo_bar.7z" ci-joint</Description>
    <CreatedDate>2017-03-03T14:46:00</CreatedDate>
    <Event>
        <EventType>Décompression</EventType>
        <EventDateTime>2021-05-14T14:00:00</EventDateTime>
        <EventDetail>Décompression d'un fichier du même nom au format .7z</EventDetail>
    </Event>
</Content>

````

## Installation

### Prérequis

Les packages suivants sont nécessaires. Lancez depuis votre terminal (Mac / Linux) la commande suivante qui vérifiera si les packages existent sur votre système et les installera sinon

```bash
sudo apt-get install python3 libfreetype6-dev python3-pip python3-virtualenv sqlite3
```

Clonez le présent *repository* dans un dossier de votre choix

 ```bash
git clone https://github.com/GisliSursson/Archimail.git
```

Créez un environnement virtuel (dossier) dans lequel seront installées les librairies

```bash

virtualenv [chemin vers le dossier où vous voulez stocker votre environnement] -p python3
```

Activez l'environnement virtuel 

```bash
source [chemin vers le dossier de votre environnement]/bin/activate
```

Dans le dossier où vous avez cloné le projet, installez ensuite les librairies nécessaires (avec votre environnement virtuel activé)

```bash
pip install -r requirements.txt
```

Pour désactiver l'environnement virtuel, tapez

```bash
deactivate 
```

### Lancement

Avant d'éxécuter le script, placez à la racine du dossier cloné votre SIP décompressé (dans un dossier nommé "SIP", en majuscules).  

Dans le dossier cloné (avec votre environnement virtuel activé), lancez 

```bash
python3 main.py 
```

### Tests

Le script est testé via le service d'intégration continue [Travis CI](https://travis-ci.com/). Les tests sont lancés à chaque modification du dépôt principal. Il est possible de visualiser l'exécution de ces tests ici : [lien](https://travis-ci.com/github/GisliSursson/Archimail).

Les tests reposent sur le principe de génération de données *dummy* aléatoires (au format EML pour les mails et aux formats PDF et ODT pour les pièces jointes). 

Pour lancer manuellement les tests en local, on utilisera la commande suivante (en étant dans l'environnement virtuel du projet):

```bash
python3 test.py 
```

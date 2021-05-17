# Archimail

Ce projet a été réalisé lors d'un stage de fin d'études au Conseil d'Etat dans le cadre du Master 2 de l'Ecole nationale des chartes (année universitaire 2020-2021).

## Objectif

L'objectif est de fournir un script complémentaire aux outils développés dans le cadre du [programme VITAM](https://www.programmevitam.fr/), par exemple les [SEDA Tools](https://github.com/ProgrammeVitam/sedatools), à utiliser dans le cadre d'un projet de pérennisation numérique des données de courriers électroniques. 

## Grands principes

Le script prend en entrée un SIP conforme au SEDA décompressé. Il retourne ce même SIP modifié, toujours conforme au SEDA, qu'il conviendra de zipper à nouveau. 

Il repose sur 3 grands principes:

- Enrichir le manifeste [SEDA](https://www.francearchives.fr/seda/index.html) avec des métadonnées type "mots-clefs" au niveau de chaque mail. Ces métadonnées complètent les métadonnées ajoutées habituellement par la pratique et qui se limitent aux plus hauts niveaux de description. 
- Tester la validité des éventuelles URL trouvées dans les mails au moment du traitement.
- Décompresser les éventuelles pièces jointes ZIP. 

## Fonctionnalités

Le script propose les fonctionnalités suivantes :

- Détermination de 3 mots-clefs par mail (tokenisation, lemmatisation, évitement des noms propres) qui serviront de métadonnées de recherche basiques.
- Insertion de ces métadonnées dans le manifest SEDA.
- Décompression des éventuelles pièces jointes ZIP et suppression de fichiers ZIP originaux. 
- Test des URLs ainsi que leur éventuel enregistrement par [Internet Archive](https://archive.org/web/).
- Génération d'un fichier CSV rassemblant pour chaque mail les mots-clefs et les URLs testées. Ce fichier pourra être joint à un SIP. 
- Génération d'un fichier CSV contenant la liste des mails qui auront été estimés comme contenant des données personnelles. Un révision humaine sera alors nécessaire pour en juger définitivement. 

## Le CSV de pérennisation des URLs

Le script génère un fichier CSV qui, pour chaque mail, comporte les colonnes suivantes:
- Le nom du mail (chemin)
- Les 3 mots-clefs
- Les URLs trouvées
- Le statut du test (code HTTP)
- Le timestamp du test
- Le nom du responsable de l'URL (recommandation [INTERPARES](http://interpares.org/))
- La disponibilité de l'enregistrement le plus récent dans la Wayback Machine (s'il existe)
- Le lien vers cet enregistrement
- Le timestamp de l'enregistrement

Ce fichier a vocation à être inséré dans le SIP comme document de description complémentaire généré par les Archives. Il peut être documenté en SEDA de la façon suivante:

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

Dans le dossier où vous avez cloné le projet, installez ensuite les librairies nécessaires 

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

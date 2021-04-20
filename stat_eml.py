import datetime, json, eml_parser, os, csv, spacy
from typing import Dict
import pandas as pd
from bs4 import BeautifulSoup
from os.path import dirname, abspath
from ast import literal_eval
import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from spacy.lang.fr.stop_words import STOP_WORDS as spacy_stop
import time

start_time = time.time()
# On contrôlera par rapport à deux listes de stopwords
spacy_fr = spacy.load('fr_core_news_md')
nltk_stop = nltk.corpus.stopwords.words('french')
# On décide que l'on doit supprimer toutes les formes des verbes être et avoir qui servent dans 
# la plupart des cas à construire des conjugaisons et ne sont donc pas signifiants. Formes récupérées
# sur Wikitionary.
autres_stop = ['être', 'avoir', 'suis','es','est','sommes','êtes','sont','étais','était','étions','étiez',
               'étaient','fus','fut','fûmes','fûtes','furent','serai','seras'
               ,'sera','serons','serez','seront','serais','serais','serait','serions','seriez','seraient',
               'sois','sois','soit','soyons','soyez','soient','fusse','fusses','fût','fussions','fussiez','fussent',
               'ai','as','a','avons','avez','ont','avais','avais','avait','avions','aviez','avaient','eus','eus',
               'eut','eûmes','eûtes','eurent','aurai','auras','aura','aurons','aurez',
               'auront','aurais','aurais','aurait','aurions','auriez','auraient', 'aie','aies','ait','ayons','ayez',
               'aient','eusse','eusses','eût','eussions','eussiez','eussent']
# Ajout manuel de stopwords qui ne semblent pas être dans les frameworks utilisés
autres_sw = ['www', 'http', 'je', 'tu', 'il', 'nous', 'vous', 'ils', 'elle', 'elles', 'on', 'leur', 'leurs', 'moi', 'toi',
             'mon','ma','mes','ton','ta','tes','son','sa','ses','person','notre','nos','votre','vos','leur','leurs']
chemin_actuel = dirname(abspath(__file__))

def traitement_nlt(texte): 
    """ xxx
    
    
    """
    try:
        texte = nltk.clean_html(texte)
    except:
        pass
    # On évite la ponctuation (regex)
    tokenizer = nltk.RegexpTokenizer(r'\w+')
    # On tokenise les mots
    text_tokens = tokenizer.tokenize(texte)
    # On enlève les mots outils français (le mot à garder ne doit pas être dans l'une
    # ou dans l'autre des 4 listes de mots à retirer)
    tokens_sans_sw_un = [mot for mot in text_tokens if not mot in spacy_stop]
    tokens_sans_sw_deux = [mot for mot in tokens_sans_sw_un if not mot in nltk_stop]
    tokens_sans_sw_trois = [mot for mot in tokens_sans_sw_deux if not mot in autres_stop]
    tokens_sans_sw = [mot for mot in tokens_sans_sw_trois if not mot in autres_sw]
    # On supprime les mots qui ont une longueur d'une seule lettre. Ce sont soit des mots outils qui aurait passé les filtres
    # précédents , soit des fautes de frappe.
    tokens_sans_sw = [mot for mot in tokens_sans_sw if len(mot) > 1]
    # On enlève les mots dans lesquels il y a des chiffres. Cela permet d'éviter de renvoyer des mots
    # comme "17h30". On supprime également les mots d'une lettre. 
    tokens_iterable = set(tokens_sans_sw)
    for element in tokens_iterable:
        for letter in element:
             if letter.isnumeric():
                try:
                    tokens_sans_sw.remove(element)
                except:
                    pass
    # On calcule la fréquence d'apparition des mots
    frequence = nltk.FreqDist(tokens_sans_sw)
    # On crée un dict du type {mot:fréquence}
    freq_dict = dict((word, freq) for word, freq in frequence.items())
    # On prend le top cinq des mots les plus fréquents
    top_cinq = sorted(freq_dict.keys(), reverse=True)[0:5]
    # Classement par ordre alphabétique
    top_cinq = sorted(top_cinq)
    # On utilise Spacy pour la lemmatisation car il est mieux entraîné pour le français que 
    # NLTK.
    liste_lem = []
    # On crée une liste des lemmes des cinq mots les plus fréquents. Par exemple, si le mot est "chantait",
    # le lemme sera "chanter".
    for element in top_cinq:
        sp = spacy_fr(element)
        for element in sp:
            lemme = element.lemma_
            liste_lem.append(lemme)
    return liste_lem


def extraire_contenu_mail(mail):
    with open(mail, 'rb') as mail_ouvert:
        raw_email = mail_ouvert.read()
        ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=False)
        parsed_eml = ep.decode_email_bytes(raw_email)
        return parsed_eml
 
with open(os.path.join(chemin_actuel,"perso","df_glob.csv"), 'w') as f:
    writer = csv.writer(f, delimiter = ";")
    liste_col = ['nom_fichier', 'top_cinq_mots']
    writer.writerow(liste_col)   
    mail = 0    
    for root, dirs, files in os.walk(os.path.join(chemin_actuel,"perso","mail_enc"), topdown=True):
        for index, name in enumerate(files):
            filename = os.path.join(root, name)
            if filename.endswith(".eml"):
                mail += 1
                data = extraire_contenu_mail(filename)
                liste_val = []
                liste_val.append(filename)
                texte = data["body"][0]["content"]
                top = traitement_nlt(texte)
                string = ','.join(str(valeur) for valeur in top)
                liste_val.append(string)
                writer.writerow(liste_val)
    print("Nombre de mails traités : " + str(mail))
    print("Temps de calcul (en secondes) : " + str(time.time() - start_time))
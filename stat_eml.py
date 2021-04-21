import datetime, json, eml_parser, os, csv, spacy, re, requests
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
autres_sw = ['www', 'https', 'http', 'je', 'tu', 'il', 'nous', 'vous', 'ils', 'elle', 'elles', 'on', 'leur', 'leurs', 'moi', 'toi',
             'mon','ma','mes','ton','ta','tes','son','sa','ses','person','notre','nos','votre','vos','leur','leurs']
chemin_actuel = dirname(abspath(__file__))

# regex = """(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
# On applique ici les recommandations INTERPARES sur les liens dans les mails
def trouver_url(texte):
    # Regex non greedy
    # url_group = re.findall(r"""(https?://.+\.[a-z]{2,3}|\/[^\s"']+)""",texte)
    url_group = re.findall(r"""(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})""", texte)
    if url_group:
        # print(url_group)
        # On met les résultats des recherchers dans des listes au cas où il y aurait plus d'une URL dans un mail
        liste_uri = []
        liste_statut = []
        liste_date_test = []
        liste_pers = []
        for url in url_group:
            url = str(url)
            uri = url
            # Problèmes causés par les URL contenus dans des balises
            if "<" or ">" not in uri:
                 # On évite de considérer "www.example.com" et "www.example.com/" comme deux URL différentes
                if uri[-1] == "/":
                    uri = url[:-1]
                if uri not in liste_uri:
                    try:
                        # Charger que le header est plus court que charger toute la page
                        requests.head(url, timeout=5)
                        req = requests.head(url, timeout=5)
                        statut = str(req.status_code)
                        date_test = str(datetime.datetime.now())
                        pers = str(re.findall(r'\/?(.+[a-z]{2,3}?)', uri)[0])
                    # Erreur retournée si le code renvoyé n'est pas du HTTP standard (requests.exceptions.ConnectionError)
                    except requests.exceptions.ConnectionError:
                        pass
                        # statut = "[Errno -2]"
                        # date_test = str(datetime.datetime.now())
                        # pers = str(re.findall(r'\/?(.+[a-z]{2,3}?)', uri)[0])
                    # Au cas où un site aurait été mis dans le corps du texte (sans http)
                    except requests.exceptions.MissingSchema:
                        pass
                        # uri = "http://" + uri
                        # req = requests.head(uri, timeout=5)
                        # statut = str(req.status_code)
                        # date_test = str(datetime.datetime.now())
                        # pers = str(re.findall(r'\/?(.+[a-z]{2,3}?)', uri)[0])
                    except requests.exceptions.ReadTimeout:
                        pass
                    except requests.exceptions.InvalidURL:
                        pass
                    except requests.exceptions.InvalidSchema:
                        pass
            else:
                pass
            try:
                liste_uri.append(uri)
                liste_statut.append(statut)
                liste_date_test.append(date_test)
                liste_pers.append(pers)
            # Erreurs si une des erreurs ci-dessus a été rencontrée. 
            except ValueError:
                pass
            except UnboundLocalError:
                pass
        return liste_uri, liste_statut, liste_date_test, liste_pers      

def liste_en_str(liste):
    if liste is not None and len(liste) > 1:
        string = ','.join(str(valeur) for valeur in liste)
    elif liste is not None:
        string = str(liste)
    return string


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
 
with open(os.path.join(chemin_actuel,"perso","df_glob_2104.csv"), 'w') as f:
    writer = csv.writer(f, delimiter = ";")
    liste_col = ['nom_fichier', 'top_cinq_mots', 'url(s)', 'resultat_test_URL', 'date_test_URL', 'responsable_URL']
    writer.writerow(liste_col)   
    mail = 0
    nb_url = 0    
    for root, dirs, files in os.walk(os.path.join(chemin_actuel,"perso","mail_enc"), topdown=True):
        for index, name in enumerate(files):
            filename = os.path.join(root, name)
            if filename.endswith(".eml"):
                mail += 1
                liste_val = []
                data = extraire_contenu_mail(filename)
                texte = data["body"][0]["content"]
                liste_val.append(filename)
                top = traitement_nlt(texte)
                string = ','.join(str(valeur) for valeur in top)
                liste_val.append(string)
                try:
                    liste_uri, liste_statut, liste_date_test, liste_pers = trouver_url(texte)
                    # print(trouver_url(texte))
                    #if liste_uri is not None and liste_statut is not None and liste_date_test is not None and liste_pers is not None:
                    nb_url += 1
                    uri = liste_en_str(liste_uri)
                    statut = liste_en_str(liste_statut)
                    date_test = liste_en_str(liste_date_test)
                    pers = liste_en_str(liste_pers)
                    liste_val.append(uri)
                    liste_val.append(statut)
                    liste_val.append(date_test)
                    liste_val.append(pers)
                except TypeError:
                    pass
                writer.writerow(liste_val)
    print("Nombre de mails traités : " + str(mail))
    print("Nombre d'URL traitées : " + str(nb_url))
    print("Temps de calcul (en secondes) : " + str(time.time() - start_time))